"""Read the explicitly authorized public knowledge pages into a private review cache.

No login, software download, attachment execution, or publication is performed.
"""
from __future__ import annotations
import concurrent.futures
import hashlib
import json
import re
import urllib.request
import sys
import time
import urllib.error
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / '.work' / 'forensics-web'
DECODER = json.JSONDecoder()

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    return urllib.request.urlopen(req, timeout=40).read().decode('utf-8')

def flight(html):
    chunks = []
    for match in re.finditer(r'self\.__next_f\.push\((.*?)\)</script>', html):
        item = json.loads(match[1])
        if len(item) > 1 and isinstance(item[1], str):
            chunks.append(item[1])
    return ''.join(chunks)

def property_value(text, key):
    for m in re.finditer('"' + key + '":', text):
        try:
            yield DECODER.raw_decode(text[m.end():])[0]
        except (ValueError, TypeError):
            pass

def wiki_content(html):
    data = flight(html)
    strings = {}
    encoded = data.encode('utf-8')
    for m in re.finditer(rb'(?:^|\n)([0-9a-f]+):T([0-9a-f]+),', encoded):
        size = int(m[2], 16)
        strings['$' + m[1].decode()] = encoded[m.end():m.end()+size].decode('utf-8')
    candidates = []
    for value in property_value(data, 'content'):
        if isinstance(value, str):
            value = strings.get(value, value)
            if '\n' in value or re.search(r'<(?:p|h[1-6]|div|table)\b', value):
                candidates.append(value)
    return max(candidates, key=len, default='')

class DigiParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.links=[]; self.parts=[]; self.skip=0
    def handle_starttag(self, tag, attrs):
        values=dict(attrs)
        if tag in {'script','style','nav'}: self.skip+=1
        if tag=='a' and '/wiki/' in values.get('href',''): self.links.append(values['href'])
        if tag in {'h1','h2','h3','h4','p','pre','li','tr','br','div'}: self.parts.append('\n')
        if tag in {'td','th'}: self.parts.append(' | ')
    def handle_endtag(self,tag):
        if tag in {'script','style','nav'}: self.skip=max(0,self.skip-1)
        if tag in {'h1','h2','h3','h4','p','pre','li','tr','div'}: self.parts.append('\n')
    def handle_data(self,data):
        if not self.skip:self.parts.append(data)
    def text(self):return '\n'.join(line.strip() for line in ''.join(self.parts).splitlines() if line.strip())

def collect():
    nav=json.loads((CACHE/'wiki-nav.json').read_text('utf-8'))
    tasks=[]
    for group,nodes in nav.items():
        for node in nodes:
            if node['type']==2:
                tasks.append({'site':'Forensics-Wiki','id':node['id'],'title':node['name'],'group':group,'url':'https://www.forensics-wiki.com/node/'+node['id']})
    parser=DigiParser();parser.feed((CACHE/'digi-index.html').read_text('utf-8'))
    for url in dict.fromkeys(parser.links):
        if '/wiki/nodes/' not in url:
            tasks.append({'site':'DigiForensics','id':url.rstrip('/').rsplit('/',1)[-1],'url':url})
    if '--wiki-only' in sys.argv:
        tasks=[item for item in tasks if item['site']=='Forensics-Wiki']
    if '--digi-only' in sys.argv:
        tasks=[item for item in tasks if item['site']=='DigiForensics']
    def read(item):
        path=CACHE/(item['id']+'.txt')
        try:
            if path.exists() and path.stat().st_size:
                content=path.read_text('utf-8')
            else:
                html=fetch(item['url'])
                if item['site']=='Forensics-Wiki':content=wiki_content(html)
                else:
                    p=DigiParser();p.feed(html);content=p.text()
                path.write_text(content,encoding='utf-8')
            status='login-required' if '登录后阅读全文' in content else ('read' if content.strip() else 'empty')
            item.update(status=status,chars=len(content),sha256=hashlib.sha256(content.encode()).hexdigest(),cache=path.name)
        except Exception as exc:item.update(status='blocked',error=str(exc))
        print(item['site'],item['id'],item['status'],item.get('chars',0),flush=True)
        return item
    # A throttled serial pass avoids repeating a site's rate-limit response.
    if '--digi-only' in sys.argv:
        results=[]
        rate_limited=False
        for item in tasks:
            path=CACHE/(item['id']+'.txt')
            if rate_limited and not path.exists():
                item.update(status='blocked',error='Deferred after HTTP 429; no repeated request')
                results.append(item)
                continue
            if not path.exists():time.sleep(2)
            result=read(item);results.append(result)
            rate_limited='429' in result.get('error','')
    else:
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
            results=list(pool.map(read,tasks))
    if ('--wiki-only' in sys.argv or '--digi-only' in sys.argv) and (CACHE/'pages.json').exists():
        old=json.loads((CACHE/'pages.json').read_text('utf-8'))
        selected={item['site'] for item in tasks}
        results += [item for item in old if item['site'] not in selected]
    (CACHE/'pages.json').write_text(json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
    print('Pages:',len(results),'Read:',sum(x['status']=='read' for x in results))

if __name__=='__main__':collect()
