#!/usr/bin/env python3
"""Read-only ORYN deployment audit: files on disk vs web server output.
No machine/serial/LED commands are issued. Uses only Python standard library.
"""
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import sys

root=Path(__file__).resolve().parents[1]
version='CP2J-SAFE-WIFI-20261104'
base=(sys.argv[1] if len(sys.argv)>1 else 'http://127.0.0.1').rstrip('/')
checks={
 'index.html': ('/','oryn-v2.css?v='+version),
 'oryn-v2-live.js': ('/oryn-v2-live.js?v='+version, "data-oryn-release','"+version),
 'oryn-v2.css': ('/oryn-v2.css?v='+version, '.oryn-v2-calgrid'),
}
failed=False
for name,(url,token) in checks.items():
    local=(root/'static/dist'/name)
    if not local.exists() or token not in local.read_text(errors='replace'):
        print('[FAIL] Local V2 build missing or out of date:',name);failed=True;continue
    try:
        req=Request(base+url,headers={'Cache-Control':'no-cache','Pragma':'no-cache'})
        with urlopen(req,timeout=8) as res:
            body=res.read().decode('utf-8','replace')
            if token not in body: print('[FAIL] Server is serving OLD',name,'from',base);failed=True
            elif name=='oryn-v2-live.js' and any(x in body for x in ['<iframe','Complete controls','oryn-v2-dialog.open']):
                print('[FAIL] Old embedded controls are still present');failed=True
            elif name=='oryn-v2-live.js' and not all(marker in body for marker in ['function wifiPanel()', 'function firmwareLabel()', 'function calCard(axis)']):
                print('[FAIL] Native Wi-Fi, firmware, or Motion controls are missing');failed=True
            else: print('[PASS] Served:',name)
    except (URLError,HTTPError,OSError) as e:
        print('[FAIL] Could not read',base+url,str(e));failed=True
if failed:
    print('Check GitHub pull, nginx document root, and browser cache. Do not call UI updated.')
    sys.exit(1)
print('[PASS] Pi serves ORYN Studio V2 '+version+' (no older control modal).')
