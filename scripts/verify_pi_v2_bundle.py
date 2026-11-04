#!/usr/bin/env python3
"""Read-only ORYN CP2J source and frontend verification; no controller access.

Git may change CRLF/LF for text source. Compare normalized bytes only for
text files; compare binary assets exactly. Never include mutable saved
calibration, Wi-Fi credentials, or device state in this release manifest.
"""
from pathlib import Path
import json,hashlib,sys

root=Path(__file__).resolve().parents[1]
manifest=root/'ORYN_CP2J_SOURCE_MANIFEST.json'
try:
    data=json.loads(manifest.read_text(encoding='utf-8'))
    for rel,entry in data['files'].items():
        target=root/rel
        if not target.is_file():raise ValueError('Missing release file: '+rel)
        blob=target.read_bytes()
        if entry['mode']=='text':blob=blob.replace(b'\r\n',b'\n')
        actual=hashlib.sha256(blob).hexdigest()
        if actual!=entry['sha256']:
            raise ValueError('Unexpected source change: '+rel)
    index=(root/'static/dist/index.html').read_text(encoding='utf-8')
    js=(root/'static/dist/oryn-v2-live.js').read_text(encoding='utf-8')
    version='CP2J-SAFE-WIFI-20261104'
    if version not in index or version not in js:raise ValueError('CP2J front-end version mismatch')
    if any(k in js for k in ('<iframe','oryn-v2-dialog.open','Complete controls')):
        raise ValueError('Legacy interface detected')
    for marker in ('function wifiPanel()', 'function firmwareLabel()', 'function calCard(axis)'):
        if marker not in js:raise ValueError('Native UI element missing: '+marker)
    print('[PASS] ORYN CP2J release integrity: '+str(len(data['files']))+' source files checked')
except Exception as err:
    print('[FAIL]',err,file=sys.stderr)
    raise SystemExit(1)
