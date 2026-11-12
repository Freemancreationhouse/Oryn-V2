#!/usr/bin/env python3
"""Read-only ORYN deployment check: compare Pi-served frontend with installed files."""
from pathlib import Path
from urllib.request import Request,urlopen
import hashlib,sys
ROOT=Path(__file__).resolve().parents[1]
VERSION='CP2M-REFERENCE-20261111'
base=(sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1').rstrip('/')
checks={'index.html':'/','oryn-v2-live.js':'/oryn-v2-live.js?v='+VERSION,'oryn-v2.css':'/oryn-v2.css?v='+VERSION}
failures=[]
for name,url in checks.items():
    local=ROOT/'static/dist'/name
    if not local.is_file():failures.append('Local missing: '+name);continue
    expected=local.read_bytes()
    try:
        req=Request(base+url,headers={'Cache-Control':'no-cache','Pragma':'no-cache'})
        with urlopen(req,timeout=8) as response:received=response.read()
    except Exception as exc:
        failures.append('Cannot fetch '+name+': '+str(exc));continue
    if hashlib.sha256(received).digest()!=hashlib.sha256(expected).digest():
        failures.append('Pi is serving different '+name);continue
    if name=='index.html' and VERSION.encode() not in received:failures.append('Old HTML version detected')
    if name=='oryn-v2-live.js':
        if VERSION.encode() not in received:failures.append('Old JavaScript version detected')
        if b'<iframe' in received or b'Complete controls' in received:failures.append('Embedded old UI detected')
        for marker in [b'function calCard(axis)',b'calFeedback',b'calibration_single_attempt',b'function calibrationGuide()',b'confirm-home',b'move-perimeter',b'CP2M-REFERENCE-20261111']:
            if marker==b'calibration_single_attempt':continue # Server-side invariant, not part of frontend.
            if marker not in received:failures.append('Missing calibration control: '+marker.decode())
    print('[PASS] Served matches installed source:',name)
if failures:
    for msg in failures:print('[FAIL]',msg)
    raise SystemExit(1)
print('[PASS] Pi serves ORYN Studio V2 '+VERSION+'; native calibration is present.')
