#!/usr/bin/env python3
"""Reconcile two JSON exports against each other on a key field.

Written for the recurring chore of proving that what one system thinks it sent
matches what another system thinks it received: billing rows against invoices,
an API dump against a database dump, yesterday's export against today's.

Each input is a list of objects, a dict of objects keyed by id, or an object
containing one of those at a dotted --path. Exits 1 when the sides disagree, so
it can be dropped straight into a cron job or CI step.

Standard library only. Python 3.8+.
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, Dict, List, Tuple


def dig(data: Any, path: str) -> Any:
    for part in filter(None, path.split(".")):
        if not isinstance(data, dict) or part not in data:
            raise SystemExit(f"path not found in input: {path}")
        data = data[part]
    return data


def load(filename: str, key: str, path: str) -> Dict[str, Dict[str, Any]]:
    with open(filename, encoding="utf-8") as handle:
        data = dig(json.load(handle), path)

    if isinstance(data, dict):
        records = list(data.values())
    elif isinstance(data, list):
        records = data
    else:
        raise SystemExit(f"{filename}: expected a list or an object of records")

    indexed: Dict[str, Dict[str, Any]] = {}
    for record in records:
        if not isinstance(record, dict):
            raise SystemExit(f"{filename}: records must be objects")
        if key not in record:
            raise SystemExit(f"{filename}: record without key field {key!r}")
        identifier = str(record[key])
        if identifier in indexed:
            raise SystemExit(f"{filename}: duplicate key {identifier!r}")
        indexed[identifier] = record
    return indexed


def differs(left: Any, right: Any, tolerance: float) -> bool:
    if tolerance and isinstance(left, (int, float)) and isinstance(right, (int, float)):
        if isinstance(left, bool) or isinstance(right, bool):
            return left is not right
        return abs(float(left) - float(right)) > tolerance
    return left != right


def compare(
    left: Dict[str, Dict[str, Any]],
    right: Dict[str, Dict[str, Any]],
    fields: List[str],
    tolerance: float,
) -> Tuple[List[str], List[str], List[Dict[str, Any]]]:
    only_left = sorted(set(left) - set(right))
    only_right = sorted(set(right) - set(left))

    mismatches: List[Dict[str, Any]] = []
    for identifier in sorted(set(left) & set(right)):
        a, b = left[identifier], right[identifier]
        checked = fields or sorted(set(a) & set(b))
        for field in checked:
            if differs(a.get(field), b.get(field), tolerance):
                mismatches.append(
                    {
                        "key": identifier,
                        "field": field,
                        "left": a.get(field),
                        "right": b.get(field),
                    }
                )
    return only_left, only_right, mismatches


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("left")
    parser.add_argument("right")
    parser.add_argument("-k", "--key", default="id", help="join field (default: id)")
    parser.add_argument(
        "-f", "--fields", default="", help="comma separated fields to compare"
    )
    parser.add_argument(
        "-p", "--path", default="", help="dotted path to the records inside each file"
    )
    parser.add_argument(
        "-t", "--tolerance", type=float, default=0.0, help="numeric slack, e.g. 0.01"
    )
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--limit", type=int, default=20, help="mismatches to print")
    args = parser.parse_args()

    fields = [f.strip() for f in args.fields.split(",") if f.strip()]
    left = load(args.left, args.key, args.path)
    right = load(args.right, args.key, args.path)
    only_left, only_right, mismatches = compare(left, right, fields, args.tolerance)

    if args.as_json:
        print(
            json.dumps(
                {
                    "only_in_left": only_left,
                    "only_in_right": only_right,
                    "mismatches": mismatches,
                },
                indent=2,
                default=str,
            )
        )
    else:
        print(f"{len(left)} records in {args.left}, {len(right)} in {args.right}")
        print(f"only in left:  {len(only_left)}  {only_left[: args.limit]}")
        print(f"only in right: {len(only_right)}  {only_right[: args.limit]}")
        print(f"mismatched fields: {len(mismatches)}")
        for row in mismatches[: args.limit]:
            print(f"  {row['key']}.{row['field']}: {row['left']!r} != {row['right']!r}")
        if len(mismatches) > args.limit:
            print(f"  ... {len(mismatches) - args.limit} more")

    return 1 if (only_left or only_right or mismatches) else 0


if __name__ == "__main__":
    sys.exit(main())
