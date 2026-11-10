#!/usr/bin/env python3
"""Read-only CP2L source-integrity check. Ignores mutable customer settings/data."""
from pathlib import Path
import hashlib,json,sys
root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'ORYN_CP2L_SOURCE_MANIFEST.json').read_text(encoding='utf-8'))
problems=[]
for rel,expected in manifest['sha256_lf'].items():
    candidate=root/rel
    if not candidate.is_file():problems.append('MISSING '+rel);continue
    actual=hashlib.sha256(candidate.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
    if actual!=expected:problems.append('CHANGED '+rel)
if problems:
    for problem in problems:print('[FAIL]',problem)
    raise SystemExit(1)
for rel in ['static/dist/index.html','static/dist/oryn-v2-live.js','frontend/v2-native/oryn-v2-live.js']:
    if 'CP2L-CALIBRATION-20261110' not in (root/rel).read_text(encoding='utf-8'):
        print('[FAIL] V2 release marker absent in',rel);raise SystemExit(1)
print('[PASS] ORYN CP2L protected source files:',len(manifest['sha256_lf']))
