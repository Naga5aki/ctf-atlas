#!/usr/bin/env python3
"""Audit normalized movements offline. No network, wallet access, or signatures."""
import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

FIELDS = ['source_ref', 'source_kind', 'chain', 'asset_id', 'decimals',
          'tx_hash', 'event_index', 'block_hash', 'event_type', 'from', 'to',
          'status', 'raw_amount', 'timestamp_utc']
STATUSES = {'confirmed_success', 'confirmed_failed', 'pending', 'orphaned', 'unknown'}


def utc(value):
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('timestamp requires an explicit UTC offset')
    return parsed.astimezone(timezone.utc)


def display(raw, decimals):
    sign = '-' if raw < 0 else ''
    digits = str(abs(raw)).zfill(decimals + 1)
    return sign + (digits if not decimals else digits[:-decimals] + '.' + digits[-decimals:])


def analyze(path, target, start=None, end=None):
    if not target:
        raise ValueError('target must be explicit')
    begin, finish = utc(start) if start else None, utc(end) if end else None
    if begin and finish and begin >= finish:
        raise ValueError('start must precede end')
    decisions, issues, keyed = [], [], defaultdict(list)
    with Path(path).open(encoding='utf-8-sig', newline='') as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ValueError('missing or duplicate CSV header')
        if set(FIELDS) - set(reader.fieldnames):
            raise ValueError('missing columns: ' + ','.join(sorted(set(FIELDS) - set(reader.fieldnames))))
        for line, original in enumerate(reader, 2):
            row = {field: original.get(field) for field in FIELDS}
            entry = {'line': line, **row, 'decision': ''}
            decisions.append(entry)
            try:
                if None in original or any(value is None for value in row.values()):
                    raise ValueError('row width does not match header')
                if any(not row[field] for field in FIELDS if field != 'block_hash'):
                    raise ValueError('empty required value')
                if row['source_kind'] not in {'chain', 'platform'} or row['status'] not in STATUSES:
                    raise ValueError('unknown source kind or status')
                if row['event_type'] not in {'transfer', 'fee', 'approval'}:
                    raise ValueError('unknown event type')
                if not re.fullmatch(r'0|[1-9][0-9]*', row['raw_amount']):
                    raise ValueError('raw_amount must be a nonnegative integer string')
                if not re.fullmatch(r'0|[1-9][0-9]*', row['decimals']):
                    raise ValueError('decimals must be an integer')
                amount, decimals = int(row['raw_amount']), int(row['decimals'])
                if not 0 <= decimals <= 255:
                    raise ValueError('decimals outside 0..255')
                instant = utc(row['timestamp_utc'])
                if row['source_kind'] == 'chain' and row['status'] in {'confirmed_success', 'confirmed_failed'} and not row['block_hash']:
                    raise ValueError('confirmed chain movement requires block_hash')
                key = tuple(row[field] for field in ['source_kind', 'chain', 'asset_id', 'tx_hash', 'event_index'])
                signature = (decimals, row['block_hash'], row['event_type'], row['from'], row['to'],
                             row['status'], amount, instant)
                keyed[key].append((entry, signature, amount, decimals, instant))
            except (ValueError, TypeError) as error:
                entry['decision'] = 'invalid'
                issues.append({'line': line, 'source_ref': row['source_ref'], 'reason': str(error)})

    asset_precision = defaultdict(set)
    for entries in keyed.values():
        for entry, _, _, decimals, _ in entries:
            if entry['source_kind'] == 'chain':
                asset_precision[(entry['chain'], entry['asset_id'])].add(decimals)
    unique = []
    for entries in keyed.values():
        if len({item[1] for item in entries}) != 1:
            for entry, *_ in entries:
                entry['decision'] = 'conflict'
                issues.append({'line': entry['line'], 'source_ref': entry['source_ref'],
                               'reason': 'same event key has conflicting quantity, state, block, time or endpoints'})
            continue
        unique.append(entries[0])
        for entry, *_ in entries[1:]:
            entry['decision'] = 'duplicate'

    # Quarantine an entire asset if metadata disagree, even on otherwise distinct events.
    groups = {}
    for entry, _, amount, decimals, instant in unique:
        asset_key = (entry['chain'], entry['asset_id'])
        if entry['source_kind'] == 'platform':
            decision = 'platform_separate'
        elif len(asset_precision[asset_key]) != 1:
            decision = 'precision_conflict'
            issues.append({'line': entry['line'], 'source_ref': entry['source_ref'],
                           'reason': 'asset has inconsistent decimals; resolve metadata before aggregation'})
        elif (begin and instant < begin) or (finish and instant >= finish):
            decision = 'outside_time'
        elif entry['event_type'] == 'approval':
            decision = 'approval'
        elif entry['status'] != 'confirmed_success' and not (entry['event_type'] == 'fee' and entry['status'] == 'confirmed_failed'):
            decision = entry['status']
        elif entry['from'] == target and entry['to'] == target:
            decision = 'self_transfer'
        elif entry['event_type'] == 'fee':
            decision = 'fee' if entry['from'] == target else 'unrelated'
        elif entry['to'] == target:
            decision = 'incoming'
        elif entry['from'] == target:
            decision = 'outgoing'
        else:
            decision = 'unrelated'
        entry['decision'] = decision
        if decision not in {'incoming', 'outgoing', 'fee'}:
            continue
        group = groups.setdefault(asset_key, {'chain': asset_key[0], 'asset_id': asset_key[1],
            'decimals': decimals, 'incoming_raw': 0, 'outgoing_raw': 0, 'fee_raw': 0,
            'incoming_events': 0, 'positive_incoming_events': 0, 'outgoing_events': 0, 'fee_events': 0})
        group[decision + '_raw'] += amount
        group[decision + '_events'] += 1
        if decision == 'incoming' and amount > 0:
            group['positive_incoming_events'] += 1
    for group in groups.values():
        group['net_flow_raw'] = group['incoming_raw'] - group['outgoing_raw'] - group['fee_raw']
        for field in ['incoming', 'outgoing', 'fee', 'net_flow']:
            raw = group[field + '_raw']
            group[field] = display(raw, group['decimals'])
            group[field + '_raw'] = str(raw)  # JSON consumers must not round large integers.
    summary = {'review_status': 'needs_review' if issues else 'no_row_conflicts_detected',
        'scope': {'target': target, 'start_inclusive': start, 'end_exclusive': end,
                  'coverage': 'input rows only; acquisition completeness and attribution are not verified',
                  'meaning': 'net flow of selected movements, not an account balance or profit'},
        'input_sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        'tool_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'input_rows': len(decisions), 'decisions': dict(sorted(Counter(row['decision'] for row in decisions).items())),
        'groups': [groups[key] for key in sorted(groups)], 'issues': len(issues)}
    return summary, decisions, issues


def write_csv(path, fields, rows):
    temporary = path.with_suffix(path.suffix + '.tmp')
    with temporary.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--target', required=True, help='already validated and normalized target identifier')
    parser.add_argument('--start', help='inclusive ISO8601 timestamp with timezone')
    parser.add_argument('--end', help='exclusive ISO8601 timestamp with timezone')
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    summary, decisions, issues = analyze(args.input, args.target, args.start, args.end)
    destination = args.out.resolve()
    source = args.input.resolve()
    names = ['summary.json', 'decisions.csv', 'issues.csv']
    candidates = [destination/name for name in names + [name + '.tmp' for name in names]]
    if any(path == source or (path.exists() and path.samefile(source)) for path in candidates):
        parser.error('output must not overwrite the input evidence')
    destination.mkdir(parents=True, exist_ok=True)
    write_csv(destination/'decisions.csv', ['line'] + FIELDS + ['decision'], decisions)
    write_csv(destination/'issues.csv', ['line', 'source_ref', 'reason'], issues)
    temporary = destination/'summary.json.tmp'
    temporary.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(destination/'summary.json')
    print(json.dumps({'review_status': summary['review_status'], 'rows': summary['input_rows'],
                      'issues': summary['issues'], 'out': str(destination)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
