#!/usr/bin/env python3
"""Reinstall ORYN Studio V2 as the only customer-facing web application.

Use after any Vite build that overwrites static/dist. Operates on frontend
artifacts only and never changes GRBL, serial, motion mathematics or settings.
"""
from pathlib import Path

root=Path(__file__).resolve().parents[1]
source=root/'frontend/v2-native'
target=root/'static/dist'
for name in ['index.html','oryn-v2-live.js','oryn-v2.css','sw.js']:
    file=source/name
    if not file.is_file(): raise SystemExit(f'Missing required V2 source: {file}')
    (target/name).write_bytes(file.read_bytes())
# Old bookmarked URL redirects to V2 and cannot load an embedded older screen.
(target/'legacy.html').write_text('<!doctype html><html><head><meta charset="utf-8"><title>ORYN Studio V2</title></head><body><script>location.replace("/"+location.hash)</script></body></html>')
print('ORYN Studio V2 native frontend installed. No embedded previous-generation UI.')
