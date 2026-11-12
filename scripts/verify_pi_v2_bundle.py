#!/usr/bin/env python3
"""Read-only ORYN CP2P integrity audit. Per-machine saved data excluded."""
from pathlib import Path
import hashlib, json

root=Path(__file__).resolve().parents[1]
manifest=json.loads((root/'ORYN_CP2P_SOURCE_MANIFEST.json').read_text(encoding='utf-8'))
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
    if 'CP2P-SESSION-SAFETY-20261112' not in (root/rel).read_text(encoding='utf-8'):
        errors.append('WRONG VERSION: '+rel)
for name in ('index.html','oryn-v2-live.js','oryn-v2.css'):
    if (root/'static/dist'/name).read_bytes()!=(root/'frontend/v2-native'/name).read_bytes():
        errors.append('RUNTIME/SOURCE MISMATCH: '+name)
for rel in ['static/dist/oryn-v2-live.js','frontend/v2-native/oryn-v2-live.js']:
    code=(root/rel).read_text(encoding='utf-8')
    if 'id=\"physical-check\"' in code or 'S.physicalCheck' in code:
        errors.append('REPEATED CHECKBOX REGRESSION: '+rel)
    if 'oryn-v2-session-reference' not in code:
        errors.append('MISSING SESSION STATUS: '+rel)
if errors:
    for error in errors: print('[FAIL]',error)
    raise SystemExit(1)
print('[PASS] ORYN CP2P protected source files:',len(manifest['sha256_lf']))
print('[PASS] CP2P source/runtime V2 frontend synchronized')
