#!/usr/bin/env python3
"""Offline Bitcoin header and supplied TXID Merkle-path teaching exercise.

This is not a block/transaction validator, a node, or a wallet tool.
"""
import argparse
import hashlib
import json
import re
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path

GENESIS = '000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f'


def sha256d(value):
    return hashlib.sha256(hashlib.sha256(value).digest()).digest()


def hex_bytes(value, size, name):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-fA-F]{' + str(size * 2) + '}', value):
        raise ValueError(f'{name} must contain exactly {size} bytes of hexadecimal')
    return bytes.fromhex(value)


def integer(value, name, minimum, maximum):
    if type(value) is not int or not minimum <= value <= maximum:
        raise ValueError(f'{name} must be an integer in [{minimum}, {maximum}]')
    return value


def compact_target(bits):
    exponent, mantissa = bits >> 24, bits & 0x007fffff
    if bits & 0x00800000:
        raise ValueError('nBits has a negative sign')
    target = mantissa >> (8 * (3 - exponent)) if exponent <= 3 else mantissa << (8 * (exponent - 3))
    if not 0 < target < 2 ** 256:
        raise ValueError('nBits target is zero or overflows 256 bits')
    return target


def analyze(data):
    if not isinstance(data, dict):
        raise ValueError('input must be a JSON object')
    header = hex_bytes(data.get('header_hex'), 80, 'header_hex')
    current = hex_bytes(data.get('target_txid'), 32, 'target_txid')[::-1]
    count = integer(data.get('transaction_count'), 'transaction_count', 1, 2 ** 32)
    index = integer(data.get('transaction_index'), 'transaction_index', 0, count - 1)
    siblings = data.get('siblings')
    if not isinstance(siblings, list):
        raise ValueError('siblings must be a nearest-to-root ordered list')
    depth, width = 0, count
    while width > 1:
        depth += 1
        width = (width + 1) // 2
    if len(siblings) != depth:
        raise ValueError('Merkle path length does not match the supplied leaf count')
    steps, width, position = [], count, index
    for sibling_hex in siblings:
        sibling = hex_bytes(sibling_hex, 32, 'sibling')[::-1]
        duplicated = position % 2 == 0 and position + 1 == width
        if duplicated and sibling != current:
            raise ValueError('an unpaired final node must duplicate itself')
        side = 'left' if position % 2 else 'right'
        pair = sibling + current if side == 'left' else current + sibling
        current = sha256d(pair)
        steps.append({'sibling_side': side, 'duplicated_last_node': duplicated, 'parent_hash_display': current[::-1].hex()})
        width, position = (width + 1) // 2, position // 2
    version = struct.unpack_from('<i', header)[0]
    timestamp, bits, nonce = struct.unpack_from('<III', header, 68)
    target = compact_target(bits)
    digest = sha256d(header)
    block_hash = digest[::-1].hex()
    return {
        'block_hash': block_hash,
        'header': {'version': version, 'previous_block_hash': header[4:36][::-1].hex(),
                   'merkle_root': header[36:68][::-1].hex(), 'timestamp_raw': timestamp,
                   'timestamp_utc': datetime.fromtimestamp(timestamp, timezone.utc).isoformat().replace('+00:00', 'Z'),
                   'bits': f'0x{bits:08x}', 'nonce': nonce},
        'target': f'{target:064x}',
        'matches_bitcoin_mainnet_genesis': block_hash == GENESIS,
        'pow_matches_claimed_target': int.from_bytes(digest, 'little') <= target,
        'merkle_inclusion_matches_header': current == header[36:68],
        'merkle_steps': steps,
        'active_chain_checked': False, 'difficulty_rules_checked': False,
        'transaction_validity_checked': False, 'leaf_count_independently_checked': False,
        'ownership_checked': False, 'confirmations': None,
        'boundary': 'The supplied TXID, path and count are checked against one supplied header. No raw transaction, full block, chainwork, signatures or current node state are validated.'
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path, help='JSON header and TXID Merkle-path file; never modified')
    args = parser.parse_args()
    try:
        output = analyze(json.loads(args.input.read_text(encoding='utf-8')))
    except (OSError, ValueError, OverflowError) as exc:
        print(f'input error: {exc}', file=sys.stderr)
        return 2
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if output['pow_matches_claimed_target'] and output['merkle_inclusion_matches_header'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
