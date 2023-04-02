#!/usr/bin/env python3

import argparse
import json
import random
import string

parser = argparse.ArgumentParser()
parser.add_argument("file")
args = parser.parse_args()

with open(args.file) as f:
    lines = f.read().splitlines()

# memory book format looks like:
#
# {
#   "kind": "memory",
#   "name": "Aiden's Memory Bank",
#   "description": "Cleaned up and slightly modified memory book for Aiden testing. ",
#   "entries": [
#     {
#       "name": "Aiden was born on a sunny day in May, in a small town in the Midwest.",
#       "entry": "Aiden was born on a sunny day in May, in a small town in the Midwest.",
#       "keywords": [
#         "born"
#       ],
#       "priority": 0,
#       "weight": 0,
#       "enabled": true
#     },


doc = {
    "kind": "memory",
    "name": f"Memory book - {args.file}",
    "description": f"Memory book transformed from {args.file}",
}

entries = []

for line in lines:
    if not line.strip():
        continue

    keyword = "".join(random.choices(string.ascii_lowercase, k=7))

    entry = {
        "name": line,
        "entry": line,
        "keywords": [keyword],
        "priority": 0,
        "weight": 0,
        "enabled": True,
    }

    entries.append(entry)

doc["entries"] = entries

print(json.dumps(doc, indent=2))
