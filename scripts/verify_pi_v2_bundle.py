#!/usr/bin/env python3
"""Read-only ORYN CP2M integrity check; excludes per-device saved data."""
from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'ORYN_CP2M_SOURCE_MANIFEST.json').read_text(encoding='utf-8'))
problems=[]
for rel,expected in manifest['sha256_lf'].items():
    p=root/rel
    if not p.is_file():problems.append('MISSING '+rel);continue
    b=p.read_bytes().replace(b'\r\n',b'\n')
    if hashlib.sha256(b).hexdigest()!=expected:problems.append('CHANGED '+rel)
for rel in ['static/dist/index.html','static/dist/oryn-v2-live.js','frontend/v2-native/oryn-v2-live.js']:
    if 'CP2M-REFERENCE-20261111' not in (root/rel).read_text(encoding='utf-8'):
        problems.append('WRONG-VERSION '+rel)
if problems:
    for problem in problems:print('[FAIL]',problem)
    raise SystemExit(1)
print('[PASS] ORYN CP2M protected source files:',len(manifest['sha256_lf']))
