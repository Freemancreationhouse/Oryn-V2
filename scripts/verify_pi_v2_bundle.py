#!/usr/bin/env python3
"""Read-only ORYN CP2O integrity audit. Per-machine saved data excluded."""
from pathlib import Path
import hashlib, json

root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'ORYN_CP2O_SOURCE_MANIFEST.json').read_text(encoding='utf-8'))
errors=[]
for rel,expected in manifest['sha256_lf'].items():
    source=root/rel
    if not source.is_file():
        errors.append('MISSING: '+rel)
        continue
    payload=source.read_bytes().replace(b'\r\n',b'\n')
    if hashlib.sha256(payload).hexdigest()!=expected:
        errors.append('CHANGED: '+rel)
for rel in ['static/dist/index.html','static/dist/oryn-v2-live.js',
            'frontend/v2-native/index.html','frontend/v2-native/oryn-v2-live.js']:
    if 'CP2O-HOME-ACK-SAFETY-20261112' not in (root/rel).read_text(encoding='utf-8'):
        errors.append('WRONG VERSION: '+rel)
for name in ('index.html','oryn-v2-live.js','oryn-v2.css'):
    if (root/'static/dist'/name).read_bytes()!=(root/'frontend/v2-native'/name).read_bytes():
        errors.append('RUNTIME/SOURCE MISMATCH: '+name)
if errors:
    for error in errors: print('[FAIL]',error)
    raise SystemExit(1)
print('[PASS] ORYN CP2O protected source files:',len(manifest['sha256_lf']))
print('[PASS] CP2O source/runtime V2 frontend synchronized')
