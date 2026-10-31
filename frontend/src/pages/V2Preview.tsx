import { useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { useStatusStore } from '@/stores/useStatusStore'
import { Activity, ArrowLeft, ChevronRight, CircleDot, Compass, Gauge, Home, Images, Layers, Lightbulb, ListMusic, RotateCcw, Search, Settings2, SlidersHorizontal, Wifi, X } from 'lucide-react'
import './v2Preview.css'

type Workspace = 'home' | 'gallery' | 'studio' | 'sequence' | 'clean' | 'motion' | 'light' | 'system'
type Pattern = { path: string; name: string; category?: string; coordinates_count?: number }
type Coordinate = [number, number]
type PreviewInfo = { image_data?: string }
type PreviewSettings = { app?: { name?: string }; led?: { provider?: string; brightness?: number; num_leds?: number } }
// CP1.1 preview intentionally uses the same origin as the page. A previously saved
// multi-table selection must not silently redirect this local, read-only test to a
// different controller. Endpoints here cannot initiate physical movement.
async function previewRequest<T>(path: string, body?: Record<string, unknown>, signal?: AbortSignal): Promise<T> {
  const response = await fetch(path, {
    method: body ? 'POST' : 'GET',
    headers: body ? { 'Content-Type': 'application/json' } : undefined,
    body: body ? JSON.stringify(body) : undefined,
    signal,
  })
  if (!response.ok) throw new Error(`${path}: HTTP ${response.status}`)
  return response.json() as Promise<T>
}
function cleanCoordData(value: unknown): Coordinate[] {
  if (!Array.isArray(value)) return []
  return value.filter((item): item is Coordinate =>
    Array.isArray(item) && item.length >= 2 &&
    typeof item[0] === 'number' && Number.isFinite(item[0]) &&
    typeof item[1] === 'number' && Number.isFinite(item[1]) &&
    item[1] >= 0 && item[1] <= 1)
}

const nav: { key: Workspace; title: string; Icon: typeof Home }[] = [
  { key: 'home', title: 'Home', Icon: Home },
  { key: 'gallery', title: 'Gallery', Icon: Images },
  { key: 'studio', title: 'Studio', Icon: Compass },
  { key: 'sequence', title: 'Sequence', Icon: ListMusic },
  { key: 'clean', title: 'Clean', Icon: RotateCcw },
  { key: 'motion', title: 'Motion', Icon: SlidersHorizontal },
  { key: 'light', title: 'Light', Icon: Lightbulb },
  { key: 'system', title: 'System', Icon: Settings2 },
]
const titles: Record<Workspace, { title: string; desc: string }> = {
  home: { title: 'Machine Overview', desc: 'Your live table and workspace' },
  gallery: { title: 'Pattern Gallery', desc: 'Find a design to explore' },
  studio: { title: 'Pattern Studio', desc: 'Inspect the original theta/rho trajectory' },
  sequence: { title: 'Sequences', desc: 'Composition and playback overview' },
  clean: { title: 'Surface Cleaning', desc: 'Review cleaning paths before running' },
  motion: { title: 'Motion & Calibration', desc: 'Live state and existing diagnostic controls' },
  light: { title: 'Lighting', desc: 'Lighting workspace and original controller' },
  system: { title: 'System', desc: 'Device information and original settings' },
}
const legacy: Record<Workspace, string> = {
  home: '/', gallery: '/', studio: '/', sequence: '/playlists', clean: '/table-control', motion: '/table-control', light: '/led', system: '/settings',
}
const cleanNames = ['clear_from_out.thr', 'clear_from_in.thr', 'clear_sideway.thr', 'clear_from_out_mini.thr', 'clear_from_in_mini.thr', 'clear_sideway_mini.thr', 'clear_from_out_pro.thr', 'clear_from_in_pro.thr', 'clear_sideway_pro.thr', 'clear_from_out_Ultra.thr', 'clear_from_in_Ultra.thr']
function usePatterns() {
  const [patterns, setPatterns] = useState<Pattern[]>([])
  const [error, setError] = useState('')
  const [phase, setPhase] = useState<'loading'|'ready'|'error'>('loading')
  const [reload, setReload] = useState(0)
  useEffect(() => {
    const controller = new AbortController()
    setPhase('loading')
    setError('')
    previewRequest<Pattern[]>('/list_theta_rho_files_with_metadata', undefined, controller.signal)
      .then(data => {
        if (controller.signal.aborted) return
        if (!Array.isArray(data)) throw new Error('Pattern API returned an invalid list')
        setPatterns(data.filter(p => p && typeof p.path === 'string' && typeof p.name === 'string'))
        setPhase('ready')
      }).catch(err => {
        if (controller.signal.aborted) return
        setPhase('error')
        setError(err instanceof Error ? err.message : 'Unable to load pattern library')
      })
    return () => controller.abort()
  }, [reload])
  // Reconnect does not clear a successfully loaded library. Unlike CP1, a retry
  // actually fetches the data rather than just emptying the pattern list.
  return { patterns, error, phase, retry: () => setReload(n => n + 1) }
}
function PatternArtwork({ coords, progress = 1, rotation = 0, compact = false }: { coords: Coordinate[]; progress?: number; rotation?: number; compact?: boolean }) {
  const paths = useMemo(() => {
    if (!coords.length) return { all: '', part: '', end: null as null | [number, number], start: null as null | [number, number] }
    const xy = (p: Coordinate): [number, number] => [90 * p[1] * Math.cos(p[0] + rotation * Math.PI / 180), 90 * p[1] * Math.sin(p[0] + rotation * Math.PI / 180)]
    const items = coords.map(xy)
    const path = (values: [number, number][]) => values.map(([x, y], i) => `${i ? 'L' : 'M'}${x.toFixed(2)} ${y.toFixed(2)}`).join(' ')
    const count = Math.max(1, Math.floor(items.length * progress))
    return { all: path(items), part: path(items.slice(0, count)), start: items[0], end: items[count - 1] }
  }, [coords, rotation, progress])
  return <svg className="oryn-v2-art" viewBox="-105 -105 210 210" role="img" aria-label={coords.length ? 'Original logical theta rho pattern' : 'Blank circular sand table'}>
    <circle r="101" fill="#192931" stroke="#6b777a" strokeWidth=".9" />
    {[25, 50, 75, 100].map(r => <circle key={r} r={r} fill="none" stroke="#56666b" strokeOpacity=".25" strokeWidth=".35" strokeDasharray="1.5 4" />)}
    <path d="M-100 0H100 M0 -100V100" stroke="#52656b" strokeWidth=".35" opacity=".45" />
    {paths.all && <path d={paths.all} fill="none" stroke="#93a2a2" strokeOpacity=".25" strokeWidth=".55" />}
    {paths.part && <path d={paths.part} fill="none" stroke="#ecd0a4" strokeWidth={compact ? 1 : .75} strokeLinejoin="round" strokeLinecap="round" />}
    {paths.start && <circle cx={paths.start[0]} cy={paths.start[1]} r="1.7" fill="#5ecbbb" />}
    {paths.end && <circle cx={paths.end[0]} cy={paths.end[1]} r="2.0" fill="#e98258" />}
  </svg>
}
// CP1.4: Original Dune Weaver cached WebPs use black, translucent strokes.
// Recolor *only the preview pixels* to the sand-gold of Pattern Studio and
// strengthen thin anti-aliased strokes. This never changes a .thr or backend cache.
// Preserve any cached artwork that already contains non-black colored pixels.
async function colorizeCachedThumbnail(source: string): Promise<string> {
  if (!source.startsWith('data:image/')) return source
  try {
    const image = new Image()
    image.src = source
    await image.decode()
    if (!image.naturalWidth || !image.naturalHeight) return source
    const canvas = document.createElement('canvas')
    canvas.width = image.naturalWidth
    canvas.height = image.naturalHeight
    const context = canvas.getContext('2d', { willReadFrequently: true })
    if (!context) return source
    context.drawImage(image, 0, 0)
    const pixels = context.getImageData(0, 0, canvas.width, canvas.height)
    const rgba = pixels.data
    for (let i = 0; i < rgba.length; i += 4) {
      const alpha = rgba[i + 3]
      if (alpha === 0) continue
      // The existing ORYN WebP cache draws its linework in (0, 0, 0).
      // Do not overwrite colored thumbnail content introduced in the future.
      if (rgba[i] <= 35 && rgba[i + 1] <= 35 && rgba[i + 2] <= 35) {
        rgba[i] = 236
        rgba[i + 1] = 208
        rgba[i + 2] = 164
        rgba[i + 3] = Math.min(255, Math.round(alpha * 2.8))
      }
    }
    context.putImageData(pixels, 0, 0)
    return canvas.toDataURL('image/webp', 0.9)
  } catch (error) {
    // One unrenderable thumbnail must never hide its gallery pattern.
    console.warn('ORYN Gallery color preview unavailable:', error)
    return source
  }
}

function IconLabel({ children }: { children: ReactNode }) { return <span className="oryn-v2-label">{children}</span> }

export function V2Preview() {
  const [page, setPage] = useState<Workspace>('home')
  const [query, setQuery] = useState('')
  const [visibleLimit, setVisibleLimit] = useState(36)
  const [selected, setSelected] = useState<Pattern | null>(null)
  const [coords, setCoords] = useState<Coordinate[]>([])
  const [coordError, setCoordError] = useState('')
  const [coordRetry, setCoordRetry] = useState(0)
  const [previews, setPreviews] = useState<Record<string, string>>({})
  const [playlists, setPlaylists] = useState<string[]>([])
  const [version, setVersion] = useState<string>('—')
  const [ledInfo, setLedInfo] = useState('Not configured')
  const [loading, setLoading] = useState(false)
  const [rotation, setRotation] = useState(0)
  const [view, setView] = useState<'artwork'|'progress'>('artwork')
  const [cleanFile, setCleanFile] = useState('clear_from_out.thr')
  const [menuOpen, setMenuOpen] = useState(false)
  const { patterns, error, phase, retry } = usePatterns()
  const status = useStatusStore(s => s.status)
  const online = useStatusStore(s => s.isBackendConnected)
  const machineConnected = Boolean(online && status?.connection_status)
  const filteredPatterns = useMemo(() => patterns.filter(p => `${p.name} ${p.category ?? ''}`.toLowerCase().includes(query.toLowerCase())), [patterns, query])
  const gallery = useMemo(() => filteredPatterns.slice(0, visibleLimit), [filteredPatterns, visibleLimit])
  const progress = status?.progress?.percentage ? Math.min(1, Math.max(0, status.progress.percentage / 100)) : 0

  useEffect(() => {
    if (!selected && patterns.length) setSelected(patterns.find(p => !p.name.toLowerCase().includes('clear')) ?? patterns[0])
  }, [patterns, selected])
  useEffect(() => {
    // Only the Home, Studio and Clean pages need a potentially large THR payload.
    if (page !== 'home' && page !== 'studio' && page !== 'clean') return
    const file = page === 'clean' ? cleanFile : selected?.path
    if (!file) { setCoords([]); return }
    const controller = new AbortController()
    setLoading(true)
    setCoords([])
    setCoordError('')
    previewRequest<{coordinates?: unknown}>('/get_theta_rho_coordinates', { file_name: file }, controller.signal)
      .then(result => {
        if (controller.signal.aborted) return
        const parsed = cleanCoordData(result.coordinates)
        setCoords(parsed)
        if (!parsed.length) setCoordError(`No valid THR points returned for ${file}`)
      }).catch(err => {
        if (!controller.signal.aborted) {
          setCoordError(err instanceof Error ? err.message : 'Unable to preview THR file')
          setCoords([])
        }
      }).finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [selected?.path, page, cleanFile, coordRetry])
  useEffect(() => {
    if (page !== 'gallery' || !gallery.length) return
    // CP1.3: Request real cached images for every visible pattern, not just
    // the first sixteen. Small sequential batches avoid flooding the cache
    // renderer with a large simultaneous request (no machine commands).
    const missing = gallery.map(p => p.path).filter(path => !(path in previews))
    if (!missing.length) return
    const controller = new AbortController()
    const fetchVisibleThumbnails = async () => {
      for (let offset = 0; offset < missing.length && !controller.signal.aborted; offset += 8) {
        const batch = missing.slice(offset, offset + 8)
        try {
          const data = await previewRequest<Record<string, PreviewInfo>>('/preview_thr_batch', { file_names: batch }, controller.signal)
          if (controller.signal.aborted) return
          // Colorize the pre-existing cached raster, not the underlying THR.
          // Batch remains eight patterns at a time to avoid a gallery UI freeze.
          const entries = await Promise.all(Object.entries(data || {}).map(async ([path, item]) => {
            if (typeof item?.image_data !== 'string' || !item.image_data.startsWith('data:image/')) return null
            return [path, await colorizeCachedThumbnail(item.image_data)] as const
          }))
          if (controller.signal.aborted) return
          const images: Record<string, string> = {}
          for (const entry of entries) {
            if (entry) images[entry[0]] = entry[1]
          }
          setPreviews(old => ({ ...old, ...images }))
        } catch (err) {
          if (controller.signal.aborted) return
          // A broken thumbnail must never prevent pattern browsing or selection.
          console.warn('ORYN preview image batch unavailable:', err)
        }
      }
    }
    void fetchVisibleThumbnails()
    return () => controller.abort()
    // Loaded previews intentionally do not restart this effect mid-batch.
  }, [page, gallery])
  useEffect(() => {
    if (page !== 'sequence') return
    const controller = new AbortController()
    previewRequest<string[]>('/list_all_playlists', undefined, controller.signal)
      .then(data => { if (!controller.signal.aborted) setPlaylists(Array.isArray(data) ? data : []) })
      .catch(() => { if (!controller.signal.aborted) setPlaylists([]) })
    return () => controller.abort()
  }, [page])
  useEffect(() => {
    if (page !== 'system' && page !== 'light') return
    const controller = new AbortController()
    previewRequest<Record<string, unknown>>('/api/version', undefined, controller.signal)
      .then(data => { if (!controller.signal.aborted) setVersion(String(data?.current ?? data?.version ?? data?.current_version ?? 'Unknown')) })
      .catch(() => { if (!controller.signal.aborted) setVersion('Unavailable') })
    // Settings are loaded strictly for display; no settings mutation endpoint is called.
    previewRequest<PreviewSettings>('/api/settings', undefined, controller.signal)
      .then(data => {
        if (!controller.signal.aborted) setLedInfo(String(data?.led?.provider ?? 'See original LED settings'))
      }).catch(() => { if (!controller.signal.aborted) setLedInfo('Unavailable') })
    return () => controller.abort()
  }, [page])
  const pageData = titles[page]
  const activePattern = page === 'clean' ? cleanFile : selected?.name || 'No pattern selected'
  const choose = (next: Workspace) => { setPage(next); setMenuOpen(false); setView('artwork') }
  // CP1.2: Visiting /studio-v2 is the explicit opt-in to the read-only V2 preview.
  // Do not require an ephemeral Vite env flag or send the user to the legacy UI.
  // This component contains no movement or settings-mutation requests.
  return <div className="oryn-v2-shell">
    <aside className={`oryn-v2-rail ${menuOpen ? 'mobile-open' : ''}`} aria-label="ORYN Studio navigation">
      <button className="oryn-v2-mark" onClick={() => choose('home')} title="ORYN Studio Home"><Compass size={24}/></button>
      <div className="oryn-v2-rail-links">{nav.map(({ key, title, Icon }) => <button key={key} type="button" title={title} aria-label={title} aria-current={page === key ? 'page' : undefined} className={page === key ? 'active' : ''} onClick={() => choose(key)}><Icon size={21}/><span>{title}</span></button>)}</div>
      <Link className="oryn-v2-legacy" title="Return to original ORYN" to="/"><ArrowLeft size={17}/><span>Original</span></Link>
    </aside>
    <div className="oryn-v2-viewport">
      <header className="oryn-v2-topbar"><div className="oryn-v2-top-left"><button className="oryn-v2-mobile-menu" onClick={() => setMenuOpen(!menuOpen)} aria-label="Toggle navigation">{menuOpen ? <X size={20}/> : <Layers size={20}/>}</button><div><b>ORYN <span>STUDIO</span></b><small>DESIGNED TO MOVE</small></div></div><div className="oryn-v2-top-right"><span className="oryn-v2-preview-chip">V2 · READ-ONLY CHECKPOINT</span><span className={machineConnected ? 'oryn-v2-online' : 'oryn-v2-offline'}><CircleDot size={12}/>{machineConnected ? 'Machine connected' : online ? 'Backend ready · Machine offline' : 'Backend unavailable'}</span></div></header>
      <div className="oryn-v2-screen">
        <div className="oryn-v2-heading"><div><IconLabel>WORKSPACE / {page.toUpperCase()}</IconLabel><h1>{pageData.title}</h1><p>{pageData.desc}</p></div><Link className="oryn-v2-original-btn" to={legacy[page]}>Original ORYN controls <ChevronRight size={15}/></Link></div>
        {phase === 'error' && <div className="oryn-v2-alert" role="alert">ORYN backend is unavailable at this local preview. Start the read-only preview backend on port 8080, then <button type="button" onClick={retry}>Retry connection</button>. The V2 interface remains accessible and cannot initiate motion.</div>}
        {page === 'home' && <div className="oryn-v2-home-layout"><section className="oryn-v2-panel oryn-v2-home-main"><div className="oryn-v2-panel-heading"><span>ARTWORK OVERVIEW</span><span>Logical preview</span></div><PatternArtwork coords={coords} compact/>{coordError && <div className="oryn-v2-alert" role="alert">{coordError}</div>}<div className="oryn-v2-active-info"><IconLabel>READY TO EXPLORE</IconLabel><h2>{selected?.name ?? 'Connect your machine'}</h2><button onClick={() => choose('studio')}>Open in Pattern Studio <ChevronRight size={15}/></button></div></section><div className="oryn-v2-stack"><section className="oryn-v2-panel oryn-v2-stat"><IconLabel>CONNECTION</IconLabel><strong>{machineConnected ? 'CONNECTED' : 'DISCONNECTED'}</strong><p>{online ? 'Backend online · No physical controller connected' : 'Backend API unavailable'}</p></section><section className="oryn-v2-panel oryn-v2-stat"><IconLabel>MACHINE STATE</IconLabel><strong>{status?.is_homing ? 'HOMING' : status?.is_running ? 'RUNNING' : status?.is_paused ? 'PAUSED' : 'IDLE / UNKNOWN'}</strong><p>{status?.is_running ? `Progress ${status.progress?.percentage ?? 0}%` : 'No motion is initiated from this preview'}</p></section><section className="oryn-v2-panel oryn-v2-stat"><IconLabel>LIBRARY</IconLabel><strong>{patterns.length || '—'}</strong><p>{phase === 'loading' ? 'Loading library…' : phase === 'error' ? `Load failed: ${error}` : 'Discovered patterns'}</p>{phase === 'error' && <button onClick={retry}>Retry library</button>}<button onClick={() => choose('gallery')}>Browse collection →</button></section></div></div>}
        {page === 'gallery' && <div className="oryn-v2-gallery"><div className="oryn-v2-search"><Search size={17}/><input aria-label="Search patterns" placeholder="Search patterns, collections, and geometry" value={query} onChange={e => { setQuery(e.target.value); setVisibleLimit(36) }}/><span>{gallery.length}/{filteredPatterns.length} shown</span></div>{phase === 'loading' && <div className="oryn-v2-alert">Loading patterns from the local ORYN backend…</div>}{phase === 'error' && <div className="oryn-v2-alert" role="alert">Gallery could not load: {error}. <button onClick={retry}>Retry library</button></div>}<div className="oryn-v2-grid">{gallery.map(pattern => <button className="oryn-v2-tile" key={pattern.path} onClick={() => { setSelected(pattern); choose('studio') }}><div className="oryn-v2-tile-art">{previews[pattern.path] ? <img src={previews[pattern.path]} alt={`THR preview: ${pattern.name}`} loading="lazy" className="oryn-v2-tile-img"/> : <span className="oryn-v2-tile-pending">Preview loading / unavailable</span>}</div><strong>{pattern.name}</strong><small>{pattern.category || 'Pattern'} · {pattern.coordinates_count ?? 0} points</small></button>)}</div>{gallery.length < filteredPatterns.length && <button className="oryn-v2-more" onClick={() => setVisibleLimit(n => n + 36)}>Show more patterns ({filteredPatterns.length - gallery.length} remaining)</button>}{!gallery.length && phase === 'ready' && <div className="oryn-v2-empty">{query ? 'No matches — clear the search to see all patterns.' : 'The local ORYN pattern directory is empty.'}</div>}<p className="oryn-v2-footnote">Gallery thumbnails use the same sand-gold linework as Studio. Cached THR data and machine movement are unchanged; if an image cannot be loaded, its pattern remains selectable.</p></div>}
        {page === 'studio' && <div className="oryn-v2-studio-grid"><section className="oryn-v2-panel oryn-v2-browser"><IconLabel>PATTERN LIBRARY</IconLabel><input aria-label="Filter library" placeholder="Find a pattern" value={query} onChange={e => { setQuery(e.target.value); setVisibleLimit(36) }}/><div className="oryn-v2-pattern-list">{gallery.map(p => <button key={p.path} className={selected?.path === p.path ? 'selected' : ''} onClick={() => { setSelected(p); setRotation(0) }}><span>{p.name}</span><ChevronRight size={13}/></button>)}</div></section><section className="oryn-v2-panel oryn-v2-main-canvas"><div className="oryn-v2-panel-heading"><span>{activePattern}</span><span>{loading ? 'Loading…' : `${coords.length} THR points`}</span></div>{phase === 'error' && <div className="oryn-v2-alert" role="alert">Library unavailable: {error}. <button onClick={retry}>Retry</button></div>}{coordError && <div className="oryn-v2-alert" role="alert">{coordError} <button onClick={() => setCoordRetry(n => n + 1)}>Retry pattern</button></div>}<div className="oryn-v2-tabline"><button className={view === 'artwork' ? 'active' : ''} onClick={() => setView('artwork')}>Artwork</button><button className={view === 'progress' ? 'active' : ''} onClick={() => setView('progress')}>Reported Progress</button><button disabled title="True motor-path view requires verified shared motion transform">Machine Path · coming after math validation</button></div><PatternArtwork coords={coords} progress={view === 'progress' && status?.current_file === selected?.path ? progress : 1} rotation={rotation}/><div className="oryn-v2-caption">{view === 'artwork' ? 'Original THR visualization — not verified physical motor position' : 'Reported execution index — not physical ball-position feedback'}</div></section><aside className="oryn-v2-panel oryn-v2-inspector"><IconLabel>INSPECTOR</IconLabel><h2>Pattern properties</h2><div className="oryn-v2-field"><span>Selected pattern</span><strong>{selected?.name || '—'}</strong></div><div className="oryn-v2-field"><span>Coordinates</span><strong>{coords.length}</strong></div><div className="oryn-v2-field"><span>Preview rotation</span><strong>{rotation}°</strong></div><input type="range" min="0" max="270" step="90" value={rotation} onChange={e => setRotation(Number(e.target.value))} aria-label="Preview rotation"/><p>Rotation is preview-only. It does not change a saved THR or a machine command.</p><Link className="oryn-v2-wide-link" to="/">Open original pattern execution</Link></aside></div>}
        {page === 'sequence' && <div className="oryn-v2-content-grid"><section className="oryn-v2-panel"><IconLabel>LIVE EXECUTION QUEUE</IconLabel><h2>Current sequence</h2><div className="oryn-v2-field"><span>Available saved sequences</span><strong>{playlists.length ? playlists.join(' · ') : 'No saved sequences loaded'}</strong></div>{status?.playlist?.files?.length ? status.playlist.files.map((p,i) => <div className="oryn-v2-listrow" key={`${i}-${p}`}><span className="oryn-v2-number">{String(i+1).padStart(2,'0')}</span><span>{p.split('/').pop()}</span><span>{i === status.playlist?.current_index ? 'CURRENT' : 'QUEUED'}</span></div>) : <div className="oryn-v2-empty">No active sequence. The existing playlist editor remains available.</div>}</section><section className="oryn-v2-panel oryn-v2-side-info"><ListMusic size={35}/><h2>Visual sequencing</h2><p>Playlist editing, repeats, reordering, and automation are still managed by the verified original Sequences page in this checkpoint.</p><Link className="oryn-v2-wide-link" to="/playlists">Open sequence editor</Link></section></div>}
        {page === 'clean' && <div className="oryn-v2-content-grid"><section className="oryn-v2-panel oryn-v2-main-canvas"><div className="oryn-v2-panel-heading"><span>ORIGINAL CLEANING TRAJECTORY</span><span>{coords.length} points</span></div>{coordError && <div className="oryn-v2-alert" role="alert">{coordError} <button onClick={() => setCoordRetry(n => n + 1)}>Retry cleaning preview</button></div>}<PatternArtwork coords={coords}/><div className="oryn-v2-caption">{loading ? 'Loading original cleaning THR…' : 'Read-only inspection of the unchanged cleaning THR file'}</div></section><section className="oryn-v2-panel oryn-v2-side-info"><IconLabel>CLEANING MODE</IconLabel><h2>Surface preparation</h2><div className="oryn-v2-clean-options">{cleanNames.map(name => <button key={name} className={name === cleanFile ? 'active' : ''} onClick={() => setCleanFile(name)}>{name.replace('clear_', '').replace('.thr','').replaceAll('_',' ')}</button>)}</div><p>No physical cleaning commands are sent by this preview. Continue using original controls until the motion checkpoint is verified.</p><Link className="oryn-v2-wide-link" to="/table-control">Open original Clean controls</Link></section></div>}
        {page === 'motion' && <div className="oryn-v2-content-grid"><section className="oryn-v2-panel"><IconLabel>REAL-TIME MOTION STATE</IconLabel><div className="oryn-v2-measures"><div><span>THETA</span><strong>{machineConnected && typeof status?.current_theta === 'number' ? (status.current_theta * 180 / Math.PI).toFixed(2)+'°' : '—'}</strong></div><div><span>RHO</span><strong>{machineConnected && typeof status?.current_rho === 'number' ? status.current_rho.toFixed(3) : '—'}</strong></div><div><span>360° CALIBRATION</span><strong>{!machineConnected ? 'OFFLINE · UNKNOWN' : status?.theta_calibrated ? 'SAVED' : 'NOT SAVED'}</strong></div><div><span>RADIAL CALIBRATION</span><strong>{!machineConnected ? 'OFFLINE · UNKNOWN' : status?.rho_calibrated ? 'SAVED' : 'NOT SAVED'}</strong></div></div></section><section className="oryn-v2-panel oryn-v2-side-info"><Gauge size={35}/><h2>Protected calibration</h2><p>Existing homing, rotation, perimeter, orientation and motion diagnostic operations remain in the unchanged original controller. When disconnected, calibration values cannot be verified.</p><Link className="oryn-v2-wide-link" to="/table-control">Open motion diagnostics</Link></section></div>}
        {page === 'light' && <div className="oryn-v2-content-grid"><section className="oryn-v2-panel oryn-v2-light-ring"><IconLabel>LIGHTING ENVIRONMENT</IconLabel><div className="oryn-v2-glow-disc"/><p>Visual lighting scene concept · Current provider: {ledInfo}</p></section><section className="oryn-v2-panel oryn-v2-side-info"><Lightbulb size={35}/><h2>Existing LED integrations remain</h2><p>WLED, preset controls and other configured lighting capabilities are unchanged. The decorative ring shown here does not represent measured LED output.</p><Link className="oryn-v2-wide-link" to="/led">Open lighting controls</Link></section></div>}
        {page === 'system' && <div className="oryn-v2-content-grid"><section className="oryn-v2-panel"><IconLabel>DEVICE INFORMATION</IconLabel><div className="oryn-v2-system-list">{[['Backend API', phase === 'ready' ? 'Library reachable' : phase === 'error' ? 'Unavailable' : 'Checking'], ['Live telemetry', online ? 'WebSocket connected' : 'Unavailable'], ['Controller', status?.connection_status ? 'Connected' : 'Offline'], ['Backend version',version], ['Firmware',status?.firmware_version || 'Unknown'], ['Machine profile',status?.table_type || 'Unknown'], ['Current file',status?.current_file || 'None']].map(([key,val]) => <div key={key}><span>{key}</span><strong>{val}</strong></div>)}</div></section><section className="oryn-v2-panel oryn-v2-side-info"><Wifi size={35}/><h2>Original settings protected</h2><p>Network setup, table selection, security, updates, diagnostics, log review, and device maintenance continue through existing ORYN screens.</p><Link className="oryn-v2-wide-link" to="/settings">Open original System</Link></section></div>}
        <footer className="oryn-v2-execution"><div><Activity size={16}/><span>{status?.is_running ? 'EXECUTING' : status?.is_homing ? 'HOMING' : 'NOT EXECUTING'}</span><span className="oryn-v2-execution-detail">{status?.current_file?.split('/').pop() || 'No active pattern'}</span></div><div><span>{status?.is_running ? `${status.progress?.percentage ?? 0}% reported` : 'V2 READ-ONLY'}</span><Link to="/">Original ORYN <ChevronRight size={14}/></Link></div></footer>
      </div>
    </div>
  </div>
}
