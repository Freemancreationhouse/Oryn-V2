#!/usr/bin/env python3
"""After a normal Vite frontend build, install functional ORYN V2 static UI.
Reuses the just-built classic React app only for advanced-control drawer.
Never alters the original Python backend or motion math.
"""
from pathlib import Path
r=Path(__file__).resolve().parents[1]
d=r/'static/dist'
src=r/'frontend/v2-native'
old=d/'index.html'
if not old.is_file() or 'assets/' not in old.read_text(errors='replace'):
 raise SystemExit('First run frontend build to generate classic React assets, then this script.')
legacy=old.read_text()
legacy=legacy.replace('<head>', '<head><script>(function(){var a=new URLSearchParams(location.search).get("area")||"";var routes={gallery:"/",sequence:"/playlists",clean:"/table-control",motion:"/table-control",light:"/led",system:"/settings",studio:"/",home:"/"};history.replaceState(null,"",(routes[a]||"/")+"?oryn_legacy=1");})();</script>',1)
(d/'legacy.html').write_text(legacy)
for name in ['index.html','oryn-v2-live.js','oryn-v2.css','sw.js']:
 (d/name).write_bytes((src/name).read_bytes())
print('ORYN Studio V2 installed as default; advanced React controls preserved in legacy.html')
