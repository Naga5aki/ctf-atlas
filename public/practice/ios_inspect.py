"""Read-only typed plist inspection and explicit-epoch time conversion.

This helper validates formats, not a competition answer or a decryption tool.
"""
import argparse
import base64
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation, ROUND_DOWN
import hashlib
import json
from pathlib import Path
import plistlib
from zoneinfo import ZoneInfo

def typed(value):
    if isinstance(value, plistlib.UID):
        return {'type': 'UID', 'value': value.data}
    if isinstance(value, bytes):
        return {'type': 'data', 'length': len(value), 'base64': base64.b64encode(value).decode('ascii')}
    if isinstance(value, datetime):
        # plistlib's default naive date value represents UTC, not host local time.
        utc = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
        return {'type': 'date', 'utc': utc.isoformat()}
    if isinstance(value, dict):
        return {'type': 'dict', 'value': {k: typed(v) for k, v in value.items()}}
    if isinstance(value, (list, tuple)):
        return {'type': 'array', 'value': [typed(v) for v in value]}
    return {'type': type(value).__name__, 'value': value}

def inspect_plist(path):
    raw = Path(path).read_bytes()
    value = plistlib.loads(raw)
    return {'path': str(Path(path)), 'sha256': hashlib.sha256(raw).hexdigest(),
            'format': 'binary' if raw.startswith(b'bplist00') else 'XML/other plistlib-supported',
            'value': typed(value)}

def convert_time(value, epoch, unit, zone):
    try:
        number = Decimal(value)
    except InvalidOperation as error:
        raise ValueError('timestamp must be a decimal number') from error
    if not number.is_finite():
        raise ValueError('timestamp must be finite')
    divisors = {'s': Decimal(1), 'ms': Decimal(1000), 'us': Decimal(1000000), 'ns': Decimal(1000000000)}
    start = datetime(2001 if epoch == 'apple' else 1970, 1, 1, tzinfo=timezone.utc)
    microseconds = int((number / divisors[unit] * 1000000).to_integral_value(rounding=ROUND_DOWN))
    moment = start + timedelta(microseconds=microseconds)
    target = timezone.utc if zone == 'UTC' else ZoneInfo(zone)
    return {'raw': value, 'epoch': epoch, 'unit': unit, 'utc': moment.isoformat(),
            'zone': zone, 'display': moment.astimezone(target).isoformat(),
            'precision': 'microsecond; sub-microsecond part truncated toward zero'}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    p = sub.add_parser('plist'); p.add_argument('path')
    t = sub.add_parser('time')
    t.add_argument('--value', required=True)
    t.add_argument('--epoch', choices=['unix', 'apple'], required=True)
    t.add_argument('--unit', choices=['s', 'ms', 'us', 'ns'], required=True)
    t.add_argument('--zone', default='UTC')
    args = parser.parse_args()
    try:
        result = inspect_plist(args.path) if args.action == 'plist' else convert_time(args.value, args.epoch, args.unit, args.zone)
    except (OSError, ValueError, OverflowError, KeyError, plistlib.InvalidFileException) as error:
        parser.exit(2, f'Inspection error: {error}\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
