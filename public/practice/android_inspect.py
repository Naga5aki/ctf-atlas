#!/usr/bin/env python3
"""Read-only Android structure checks. No acquisition, decryption or authentication."""
import argparse
import base64
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, DecimalException
import hashlib
import json
from pathlib import Path
import re
import sys
import xml.etree.ElementTree as ET


def sha256_file(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''): h.update(chunk)
    return h.hexdigest()


def inspect_ab(path):
    path = Path(path)
    with path.open('rb') as f:
        def line():
            raw = f.readline(8193)
            if not raw.endswith(b'\n') or len(raw) > 8192:
                raise ValueError('AB header line truncated or too long')
            try: return raw[:-1].decode('ascii')
            except UnicodeDecodeError as e: raise ValueError('AB header must be ASCII') from e
        if line() != 'ANDROID BACKUP': raise ValueError('Invalid ANDROID BACKUP magic line')
        version = line()
        if version not in ('1', '2', '3', '4', '5'):
            raise ValueError('Unsupported AB version; check a version-specific implementation')
        compressed = line()
        if compressed not in ('0', '1'): raise ValueError('AB compression flag must be 0 or 1')
        encryption = line()
        result = {'path': str(path), 'version': int(version), 'compressed': compressed == '1',
                  'encryption': encryption, 'payload_status': 'not_decrypted_or_decompressed'}
        if encryption == 'AES-256':
            user_salt, checksum_salt, rounds, iv, blob = [line() for _ in range(5)]
            def hex_size(value):
                if not re.fullmatch(r'(?:[0-9a-fA-F]{2})+', value):
                    raise ValueError('Invalid hexadecimal AES header field')
                return len(value) // 2
            if not re.fullmatch(r'[0-9]+', rounds) or int(rounds) <= 0:
                raise ValueError('PBKDF2 rounds must be a positive integer')
            result['aes_header'] = {'user_salt_bytes': hex_size(user_salt),
                                    'checksum_salt_bytes': hex_size(checksum_salt),
                                    'pbkdf2_rounds': int(rounds), 'user_iv_bytes': hex_size(iv),
                                    'encrypted_master_blob_bytes': hex_size(blob)}
            if result['aes_header']['user_iv_bytes'] != 16:
                raise ValueError('AES CBC user IV must have 16 bytes')
        elif encryption != 'none': raise ValueError('Unsupported AB encryption algorithm')
        result['payload_offset'] = f.tell()
        result['payload_bytes'] = path.stat().st_size - f.tell()
    result['sha256'] = sha256_file(path)
    return result


def inspect_prefs(path):
    path = Path(path)
    if path.stat().st_size > 4 * 1024 * 1024: raise ValueError('XML exceeds 4 MiB inspection limit')
    raw = path.read_bytes()
    marker = raw.replace(b'\x00', b'').upper()
    if b'<!DOCTYPE' in marker or b'<!ENTITY' in marker:
        raise ValueError('DTD/entities are not supported')
    root = ET.fromstring(raw)
    if root.tag != 'map': raise ValueError('Expected SharedPreferences map root')
    entries = []
    for node in root:
        if 'name' not in node.attrib: raise ValueError('Preference entry missing name')
        kind = node.tag
        if kind == 'string': value = node.text or ''
        elif kind in ('int', 'long'): value = int(node.attrib['value'])
        elif kind == 'float':
            value = float(node.attrib['value'])
            if not Decimal(str(value)).is_finite(): raise ValueError('Non-finite float')
        elif kind == 'boolean':
            s = node.attrib['value']
            if s not in ('true', 'false'): raise ValueError('Invalid boolean value')
            value = s == 'true'
        elif kind == 'set':
            if any(n.tag != 'string' for n in node): raise ValueError('Set must contain strings')
            value = [n.text or '' for n in node]
        else: raise ValueError('Unsupported preference type: ' + kind)
        entries.append({'name': node.attrib['name'], 'type': kind, 'value': value})
    return {'path': str(path), 'sha256': hashlib.sha256(raw).hexdigest(), 'entries': entries}


def inspect_jwt(token):
    token = token.strip()
    if len(token) > 1024 * 1024: raise ValueError('Token exceeds 1 MiB inspection limit')
    parts = token.split('.')
    if len(parts) != 3: raise ValueError('Expected three JWT segments')
    def decode(segment):
        if not re.fullmatch(r'[A-Za-z0-9_-]+={0,2}', segment):
            raise ValueError('Invalid Base64url segment')
        padded = segment + '=' * ((-len(segment)) % 4)
        raw = base64.b64decode(padded, altchars=b'-_', validate=True)
        try: result = json.loads(raw.decode('utf-8'))
        except RecursionError as e: raise ValueError('JWT JSON nesting exceeds inspection limit') from e
        if not isinstance(result, dict): raise ValueError('JWT header/payload must be JSON objects')
        stack = [(result, 0)]
        while stack:
            value, depth = stack.pop()
            if depth > 64: raise ValueError('JWT JSON nesting exceeds 64 levels')
            if isinstance(value, dict): stack.extend((v, depth + 1) for v in value.values())
            elif isinstance(value, list): stack.extend((v, depth + 1) for v in value)
        return result
    return {'header': decode(parts[0]), 'payload': decode(parts[1]),
            'signature_verified': False, 'claims_trusted': False,
            'status': 'decoded_only_no_authentication'}


def convert_time(value, epoch, unit):
    try: number = Decimal(value)
    except InvalidOperation as e: raise ValueError('Invalid numeric time') from e
    if not number.is_finite(): raise ValueError('Time must be finite')
    if epoch not in ('unix', 'webkit') or unit not in ('s', 'ms', 'us', 'ns'):
        raise ValueError('Choose explicit supported epoch and unit')
    origin = datetime(1970, 1, 1, tzinfo=timezone.utc) if epoch == 'unix' else datetime(1601, 1, 1, tzinfo=timezone.utc)
    scale = {'s': Decimal(1), 'ms': Decimal(1000), 'us': Decimal(1000000), 'ns': Decimal(1000000000)}[unit]
    try: converted = origin + timedelta(microseconds=int(number * 1000000 / scale))
    except (OverflowError, ValueError, DecimalException) as e: raise ValueError('Time outside datetime range') from e
    return {'raw': value, 'epoch': epoch, 'unit': unit, 'utc': converted.isoformat(),
            'precision': 'microseconds; sub-microseconds truncated, never auto-guessed'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for name in ('ab', 'prefs'):
        p = sub.add_parser(name); p.add_argument('path', type=Path)
    p = sub.add_parser('jwt')
    p.add_argument('--token-file', required=True, type=Path)
    p = sub.add_parser('time'); p.add_argument('value')
    p.add_argument('--epoch', required=True, choices=('unix', 'webkit'))
    p.add_argument('--unit', required=True, choices=('s', 'ms', 'us', 'ns'))
    args = parser.parse_args()
    try:
        if args.command == 'ab': result = inspect_ab(args.path)
        elif args.command == 'prefs': result = inspect_prefs(args.path)
        elif args.command == 'jwt':
            if args.token_file.stat().st_size > 1024 * 1024: raise ValueError('Token file exceeds 1 MiB limit')
            result = inspect_jwt(args.token_file.read_text('utf-8'))
            result['input_sha256'] = sha256_file(args.token_file)
        else: result = convert_time(args.value, args.epoch, args.unit)
        print(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
        return 0
    except (OSError, ValueError, KeyError, ET.ParseError) as e:
        print(json.dumps({'error': str(e)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__': sys.exit(main())
