#!/usr/bin/env python3
"""Read-only source guard for ORYN Pi V2 release. No device activity."""
import hashlib,json,pathlib,sys
root=pathlib.Path(__file__).resolve().parents[1]
manifest=root/'ORYN_PI_V2_PRESERVATION.json'
try:
 data=json.loads(manifest.read_text())
 for relative, expected in data['protected_sha256'].items():
  p=root/relative
  if not p.is_file(): raise ValueError(f'Missing protected file: {relative}')
  actual=hashlib.sha256(p.read_bytes()).hexdigest()
  if actual!=expected: raise ValueError(f'Unexpected change: {relative}')
 for rel in ['static/dist/index.html','static/dist/oryn-v2-live.js','static/dist/legacy.html','static/dist/oryn-v2.css']:
  if not (root/rel).is_file():raise ValueError(f'Missing UI file: {rel}')
 text=(root/'static/dist/index.html').read_text()
 if 'oryn-v2-live.js' not in text:raise ValueError('Approved V2 UI not root')
 print(f"[PASS] {len(data['protected_sha256'])} protected sources unchanged, V2 main frontend present.")
except Exception as exc:
 print('[FAIL]',exc,file=sys.stderr)
 sys.exit(1)
