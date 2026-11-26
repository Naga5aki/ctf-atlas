const COMMAND = /^(?:7z|avifdec|base64|binwalk|bkcrack|cat|convert|curl|dd|exiftool|ffmpeg|file|foremost|gaps|grep|hashcat|hexdump|identify|jar|javap|john|libreoffice|magick|midicsv|montage|nc|nmap|npiet|objdump|openssl|pdfimages|pdfinfo|python3?|rar2john|readelf|rg|scalpel|sox|steghide|stegsnow|strings|tar|tcpdump|tshark|unzip|wasm-objdump|wasm2wat|wget|xxd|YAFU|zbarimg|zip2john|zipinfo|zsteg)(?:[ \t]+|$)/i;

export function isStandaloneCommand(value) {
  const text = value.trim();
  return text.length > 0
    && text.length <= 240
    && !/[\n\r\u3400-\u9fff]/u.test(text)
    && COMMAND.test(text);
}

export function isRepeatedSummary(summary, lead) {
  const normalizedSummary = summary.trim();
  return normalizedSummary.length > 0 && normalizedSummary === lead.trim();
}

export function commandCaption(value) {
  const text = value.trim();
  if (text === '# Disk DescriptorFile') return null;
  return /^# [^#\n\r]+$/u.test(text) || /^#[\u3400-\u9fff-][^\n\r]*$/u.test(text)
    ? text.slice(1).trim()
    : null;
}

export function normalizeCommandText(value) {
  return value.replace(/^Binwalk(?=[ \t])/i, 'binwalk');
}
