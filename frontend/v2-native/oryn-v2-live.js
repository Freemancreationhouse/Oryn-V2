/* ORYN Studio V2 — native prebuilt Raspberry Pi screen.
 * Calls ORYN backend endpoints; no movement transforms, gear ratios,
 * GRBL settings, serial protocol, calibration algorithms or LED drivers modified.
 * Native controls only. No embedded previous-generation application pages.
 */
(()=>{'use strict';
const nav=[['home','⌂','Home'],['gallery','▧','Gallery'],['studio','◎','Studio'],['sequence','≡','Sequence'],['clean','↻','Clean'],['motion','⊕','Motion'],['light','☼','Light'],['system','⚙','System']];
const names={home:['Machine Overview','Live workspace & machine readiness'],gallery:['Pattern Gallery','Browse THR designs'],studio:['Pattern Studio','Artwork, inspector & real pattern execution'],sequence:['Sequences','Manage & execute saved collections'],clean:['Surface Cleaning','Use the established cleaning paths'],motion:['Motion & Calibration','Guided reference, serial connection & calibration'],light:['Lighting','Magic Home, WLED & native lighting'],system:['System','Connections, machine profile, settings & diagnostics']};
const cleanFiles=['clear_from_out.thr','clear_from_in.thr','clear_sideway.thr','clear_from_out_mini.thr','clear_from_in_mini.thr','clear_sideway_mini.thr','clear_from_out_pro.thr','clear_from_in_pro.thr','clear_sideway_pro.thr','clear_from_out_Ultra.thr','clear_from_in_Ultra.thr'];
let thumbnailBusy=false;
const S={page:(location.hash.slice(1).split('?')[0]||'home').toLowerCase(),patterns:[],selected:null,coords:[],clean:'clear_from_out.thr',cleanCoords:[],gallery:[],previews:{},playlists:[],status:null,serial:{},ports:[],online:false,led:{provider:'none'},ledStatus:null,rot:null,rho:null,version:'—',wifi:{mode:'unknown'},wifiNetworks:[],wifiSaved:[],physicalCheck:false,search:'',view:'artwork',rotation:0,active:0,msg:'',loading:false,connectionAttempt:0,selectedPort:'',calSpeed:30,calStep:.5,radialStep:.2,calBusy:{theta:false,rho:false},calFeedback:{theta:null,rho:null},calGuide:'reference',sequenceFiles:[],configInfo:null,forge:{token:null,coords:[],points:0,status:'Ready',stats:{}}};
if(!names[S.page])S.page='home';
const root=document.getElementById('oryn-root');
root.setAttribute('data-oryn-release','CP2L-CALIBRATION-20261110');
const E=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const path=p=>encodeURIComponent(p??'');
const leaf=s=>(s||'').split('/').pop();
const num=n=>typeof n==='number'&&Number.isFinite(n)?n.toFixed(3):'—';
const machineLabel=t=>t?({'kinetiq_motion':'ORYN Standard','kinetiq_motion_mini':'ORYN Mini','kinetiq_motion_gold':'ORYN Gold','kinetiq_motion_pro':'ORYN Pro','kinetiq_motion_mini_pro':'ORYN Mini Pro','kinetiq_motion_mini_pro_byj':'ORYN Mini Pro','kinetiq_motion_pro_pulley':'ORYN Pro Pulley'}[t]||'Custom machine profile'):'Not identified';
const ledLabel=t=>({'magic_home':'Magic Home Wi-Fi RGB','wled':'WLED network lighting','dw_leds':'ORYN GPIO lighting','none':'None'}[t]||'None');
const isRunning=()=>!!(S.status?.is_running||S.status?.is_homing||S.status?.is_paused);
const connected=()=>S.serial?.connected===true||S.status?.connection_status===true;
const pills=()=>`<span class="oryn-v2-pill ${connected()?'ok':'warn'}">${connected()?'● Controller connected':S.online?'○ Backend online':'○ Backend offline'}</span>`;
async function api(endpoint,body){const opt=body===undefined?{}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)};const response=await fetch(endpoint,opt);if(!response.ok){let detail='';try{detail=JSON.stringify(await response.json())}catch{detail=await response.text()}throw Error(`HTTP ${response.status} ${detail.slice(0,300)}`)}const text=await response.text();try{return JSON.parse(text)}catch{return text}}
function message(s,bad=false){S.msg=s;const target=document.querySelector('#oryn-msg');if(target){target.textContent=s;target.style.color=bad?'#ffa79a':'#e9c59d'}}
function svgFor(coords,rotation=0,progress=1){if(!Array.isArray(coords)||!coords.length)return `<svg viewBox="-105 -105 210 210" class="oryn-v2-viz" role="img" aria-label="Empty sand table"><circle r="100" fill="#20323b" stroke="#67747a" stroke-width="1.2"/><path d="M-100 0H100M0-100V100" stroke="#60727a" opacity=".25"/></svg>`;let points=coords.filter(x=>Array.isArray(x)&&Number.isFinite(x[0])&&Number.isFinite(x[1])&&x[1]>=0&&x[1]<=1).map(p=>{const a=p[0]+rotation*Math.PI/180;return [90*p[1]*Math.cos(a),90*p[1]*Math.sin(a)]});let all=points.map(([x,y],i)=>(i?'L':'M')+x.toFixed(2)+' '+y.toFixed(2)).join(' '),end=points[Math.max(0,Math.ceil(points.length*progress)-1)];return `<svg viewBox="-105 -105 210 210" class="oryn-v2-viz" role="img" aria-label="Theta rho artwork preview"><circle r="101" fill="#192931" stroke="#6b777a" stroke-width=".9"/>${[25,50,75,100].map(r=>`<circle r="${r}" fill="none" stroke="#56666b" stroke-opacity=".3" stroke-width=".4" stroke-dasharray="2 4"/>`).join('')}<path d="M-100 0H100 M0-100V100" stroke="#52656b" stroke-width=".35" opacity=".4"/><path d="${all}" fill="none" stroke="#ecd0a4" stroke-width=".8" stroke-linejoin="round" stroke-linecap="round"/>${end?`<circle cx="${end[0]}" cy="${end[1]}" r="2" fill="#ee865e"/>`:''}</svg>`}
// CP2K - Visualized *reported/queued* THR waypoints. No GRBL position sensor is implied.
// The motion engine, controller settings and kinematics are untouched.
const LIVE={file:'',loading:'',points:[],path:'',cumulative:[],length:0,displayed:0,target:0,animation:null,lastTick:0,lastReport:0,statusSeen:false,requestToken:0};
function activePattern(){return !!(S.status?.current_file&&(S.status?.is_running||S.status?.is_paused));}
function liveFileName(){return leaf(S.status?.current_file||LIVE.file||'');}
function pointsForLive(coords){
 const points=[];const cumulative=[];let length=0;
 const input=Array.isArray(coords)?coords:[];
 const stride=Math.max(1,Math.ceil(input.length/3500));
 for(let k=0;k<input.length;k++){if(k%stride!==0&&k!==input.length-1)continue;const p=input[k];if(!Array.isArray(p)||!Number.isFinite(p[0])||!Number.isFinite(p[1])||p[1]<0||p[1]>1)continue;
  const q=[90*p[1]*Math.cos(p[0]),90*p[1]*Math.sin(p[0])];
  if(points.length)length+=Math.hypot(q[0]-points[points.length-1][0],q[1]-points[points.length-1][1]);
  points.push(q);cumulative.push(length);
 }
 return {points,cumulative,length,path:points.map(([x,y],i)=>(i?'L':'M')+x.toFixed(3)+' '+y.toFixed(3)).join(' ')};
}
function waypointPosition(index){
 const pts=LIVE.points;if(!pts.length)return [0,0,0];
 const n=Math.max(0,Math.min(pts.length-1,Number(index)||0)),i=Math.floor(n),f=n-i,a=pts[i],b=pts[Math.min(i+1,pts.length-1)];
 const x=a[0]+(b[0]-a[0])*f,y=a[1]+(b[1]-a[1])*f;
 const len=LIVE.cumulative[i]+(LIVE.cumulative[Math.min(i+1,pts.length-1)]-LIVE.cumulative[i])*f;
 return [x,y,len];
}
function liveFigure(){
 if(!LIVE.points.length)return `<div class="oryn-v2-live-wait"><p>Waiting for current pattern coordinates…</p><p class="oryn-v2-slim">Motion tracking starts after the Pi reports a pattern and waypoint progress.</p></div>`;
 const [x,y,dist]=waypointPosition(LIVE.displayed),rest=Math.max(0,LIVE.length-dist);
 return `<svg class="oryn-v2-viz oryn-v2-live-viz" viewBox="-105 -105 210 210" role="img" aria-label="Live reported THR toolpath; estimated from queued waypoints, not physical sensor data"><circle r="101" fill="#192931" stroke="#6b777a" stroke-width=".9"/>${[25,50,75,100].map(r=>`<circle r="${r}" fill="none" stroke="#56666b" stroke-opacity=".3" stroke-width=".4" stroke-dasharray="2 4"/>`).join('')}<path d="M-100 0H100 M0-100V100" stroke="#52656b" stroke-width=".35" opacity=".4"/><path class="oryn-v2-live-plan" d="${LIVE.path}"/><path id="oryn-live-trail" d="${LIVE.path}" stroke-dasharray="${LIVE.length.toFixed(3)}" stroke-dashoffset="${rest.toFixed(3)}"/><circle id="oryn-live-cursor" cx="${x.toFixed(3)}" cy="${y.toFixed(3)}" r="3.6"/></svg>`;
}
function liveStatusCaption(){
 const p=S.status?.progress,active=activePattern();
 const pct=(p&&Number.isFinite(Number(p.current))&&Number(p.total)>0)?Math.max(0,Math.min(100,100*Number(p.current)/Number(p.total))):null;
 const stage=!S.online?'Connection lost':S.status?.is_paused?'Paused':active?'Executing':LIVE.file?'Last reported':'Awaiting pattern';
 return `<div class="oryn-v2-live-heading"><b><span class="oryn-v2-live-dot"></span> ${stage} · ${E(liveFileName()||'No active pattern')}</b><strong id="oryn-live-pct">${pct!==null?pct.toFixed(1)+'%':'—'}</strong></div><div class="oryn-v2-progress oryn-v2-live-bar"><i id="oryn-live-bar" style="width:${pct===null?0:pct}%"></i></div><p class="oryn-v2-live-note">Cursor follows reported/queued waypoints on a sampled path; GRBL provides no measured ball position. It can lag or lead actual movement.</p>`;
}
function liveCanvas(){return `<div class="oryn-v2-live-box">${liveFigure()}${liveStatusCaption()}</div>`;}
function shouldShowLive(){return S.view==='live';}
function showActiveOrPreview(coords,rotation=0){return shouldShowLive()?liveCanvas():svgFor(coords,rotation);}
function paintLive(){
 if(!LIVE.points.length)return;
 const cursor=document.getElementById('oryn-live-cursor'),trail=document.getElementById('oryn-live-trail');
 if(cursor&&trail){const [x,y,distance]=waypointPosition(LIVE.displayed);cursor.setAttribute('cx',x.toFixed(3));cursor.setAttribute('cy',y.toFixed(3));trail.setAttribute('stroke-dashoffset',Math.max(0,LIVE.length-distance).toFixed(3));}
 const p=S.status?.progress;
 const pct=(p&&Number.isFinite(Number(p.current))&&Number(p.total)>0)?Math.max(0,Math.min(100,100*Number(p.current)/Number(p.total))):null;
 const value=document.getElementById('oryn-live-pct'),bar=document.getElementById('oryn-live-bar');
 if(value)value.textContent=pct!==null?pct.toFixed(1)+'%':'—';if(bar)bar.style.width=(pct||0)+'%';
 const footer=document.getElementById('oryn-live-footer-progress');
 if(footer)footer.textContent=activePattern()?(pct!==null?pct.toFixed(1)+'% reported (not physical feedback)':'Running · awaiting progress'):'No physical position feedback';
}
function animateWaypoints(now){
 const a=LIVE.animation;if(!a)return;
 if(!activePattern()||S.status?.is_paused||!S.online){LIVE.animation=null;return;}
 const fraction=Math.min(1,Math.max(0,(now-a.start)/a.duration));
 LIVE.displayed=a.from+(a.to-a.from)*fraction;paintLive();
 if(fraction<1)LIVE.animationFrame=requestAnimationFrame(animateWaypoints);else{LIVE.displayed=a.to;LIVE.animation=null;paintLive();}
}
function acceptReportedProgress(){
 const p=S.status?.progress;if(!activePattern()||!p||!(Number(p.total)>0)||!Number.isFinite(Number(p.current))||!LIVE.points.length)return;
 const idx=Math.max(0,Math.min(LIVE.points.length-1,(Number(p.current)/Number(p.total))*(LIVE.points.length-1)));
 if(idx<LIVE.target-1){LIVE.displayed=0;LIVE.target=0;LIVE.animation=null;}
 if(Math.abs(idx-LIVE.target)<.001){paintLive();return;}
 if(LIVE.animationFrame)cancelAnimationFrame(LIVE.animationFrame);
 LIVE.target=idx;
 if(S.status.is_paused){LIVE.displayed=idx;LIVE.animation=null;paintLive();return;}
 // Smooth only *between* Pi-reported waypoints, never invent future progress.
 LIVE.animation={from:LIVE.displayed,to:idx,start:performance.now(),duration:Math.min(850,Math.max(200,performance.now()-LIVE.lastReport||650))};
 LIVE.lastReport=performance.now();LIVE.animationFrame=requestAnimationFrame(animateWaypoints);
}
async function ensureLiveFile(){
 const file=S.status?.current_file;if(!file||!activePattern())return;
 const name=leaf(file);if(!name)return;
 if(LIVE.file!==name){
  LIVE.file=name;LIVE.points=[];LIVE.cumulative=[];LIVE.path='';LIVE.length=0;LIVE.target=0;LIVE.displayed=0;LIVE.animation=null;LIVE.lastReport=0;
  S.view='live';draw();
 }
 if(LIVE.points.length||LIVE.loading===name)return;
 LIVE.loading=name;const request=++LIVE.requestToken;
 let coords=null;
 if(S.selected&&leaf(S.selected.path)===name&&S.coords.length)coords=S.coords;
 else if(leaf(S.clean)===name&&S.cleanCoords.length)coords=S.cleanCoords;
 else {
  const meta=S.patterns.find(x=>leaf(x.path)===name);
  try{const data=await api('/get_theta_rho_coordinates',{file_name:meta?.path||name});coords=data?.coordinates||[];}catch(err){message('Live path unavailable: '+err.message,true)}
 }
 if(request!==LIVE.requestToken||LIVE.file!==name)return;
 const prepared=pointsForLive(coords||[]);Object.assign(LIVE,prepared);LIVE.loading='';
 if(activePattern()){draw();acceptReportedProgress();}
}
function receiveLiveStatus(next){
 const old=S.status,oldRun=!!old?.is_running,oldFile=leaf(old?.current_file||''),oldPause=!!old?.is_paused;
 S.status=next;
 const nowRun=!!next?.is_running,nowFile=leaf(next?.current_file||''),nowPause=!!next?.is_paused;
 // The original listener omitted progress-only updates; render state changes and update the live overlay on every message.
 const changed=oldRun!==nowRun||oldFile!==nowFile||oldPause!==nowPause||old?.connection_status!==next?.connection_status||old?.is_homing!==next?.is_homing;
 if(changed)draw();
 if(activePattern())void ensureLiveFile();
 acceptReportedProgress();paintLive();
 const detail=document.querySelector('.oryn-v2-execution-detail');if(detail)detail.textContent=leaf(next?.current_file)||'No active pattern';
}
function panel(inner,extra=''){return `<section class="oryn-v2-panel ${extra}">${inner}</section>`}
const action=(key,title,kind='')=>`<button class="oryn-v2-action ${kind}" data-action="${key}">${title}</button>`;
const details=arr=>arr.map(([k,v])=>`<div class="oryn-v2-detail"><span>${E(k)}</span><strong>${E(v)}</strong></div>`).join('');
const warning=txt=>`<div class="oryn-v2-warning">${txt}</div>`;
function safety(){return `<label class="oryn-v2-checkline"><input type="checkbox" id="physical-check" ${S.physicalCheck?'checked':''}/> I have physically referenced/homed the machine using its approved procedure, verified clearance and calibration, and can stop motor power if required.</label>`}
function readiness(){return `${details([['Controller',connected()?'Connected':'Not connected'],['Motor state',S.status?.is_running?'Executing':S.status?.is_homing?'Homing':S.status?.is_paused?'Paused':'Idle / not verified'],['Theta calibration',S.status?.theta_calibrated?'Saved':'Not reported as calibrated'],['Radial calibration',S.status?.rho_calibrated?'Saved':'Not reported as calibrated'],['Home result',S.status?.homing_success===true?'Reported successful':S.status?.homing_success===false?'Failed / requires attention':'Not confirmed'],['Current radius (reported)',num(S.status?.current_rho)]])}`}
function home(){return `<div class="oryn-v2-home-layout">${panel(`<div class="oryn-v2-panel-heading"><span>ARTWORK OVERVIEW</span><span>ORYN THR geometry</span></div>${activePattern()?liveCanvas():svgFor(S.coords,S.rotation)}<div class="oryn-v2-active-info"><span class="oryn-v2-label">SELECTED DESIGN</span><h2>${E(S.selected?.name||'Choose from Gallery')}</h2>${action('open-studio','Open in Studio →','primary')}</div>`,'oryn-v2-home-main')}<div class="oryn-v2-stack">${panel(`<span class="oryn-v2-label">MACHINE READINESS</span>${readiness()}`,'oryn-v2-stat')}${panel(`<span class="oryn-v2-label">HOMING & DIRECTION</span><p class="oryn-v2-slim">Putting the ball at the center manually does not establish the controller's home reference. Calibrate theta (full turn), rho (center-to-edge), and confirm the intended start before running paths.</p>${action('open-motion','Calibrate machine →')}`,'oryn-v2-stat')}</div></div>`}
function searchBar(){return `<div class="oryn-v2-search"><span>⌕</span><input id="pattern-search" type="search" aria-label="Search patterns" placeholder="Search pattern names" value="${E(S.search)}"/><span>${S.gallery.length}/${S.patterns.length}</span></div>`}
function gallery(){const list=S.gallery.slice(0,S.active||60);return `<div class="oryn-v2-gallery">${searchBar()}<div class="oryn-v2-grid">${list.map((p,i)=>`<button class="oryn-v2-tile" data-action="choose-pattern" data-path="${E(p.path)}"><div class="oryn-v2-tile-art" id="thumb-${i}">${S.previews[p.path]?`<img class="oryn-v2-tile-img" src="${E(S.previews[p.path])}" alt="${E(p.name)}">`:'<span class="oryn-v2-tile-pending">Preview loading</span>'}</div><strong>${E(p.name)}</strong><small>${E(p.category||'Pattern')} · ${Number(p.coordinates_count||0)} points</small></button>`).join('')}</div>${S.gallery.length>list.length?action('more','Show more designs'):''}</div>`}
function studio(){return `<div class="oryn-v2-studio-grid">${panel(`<span class="oryn-v2-label">PATTERN LIBRARY</span><input id="studio-search" class="oryn-v2-input" type="search" placeholder="Search designs" value="${E(S.search)}"/><div class="oryn-v2-pattern-list oryn-v2-pane-scroll">${S.gallery.slice(0,150).map(p=>`<button class="${S.selected?.path===p.path?'selected':''}" data-action="choose-pattern" data-path="${E(p.path)}"><span>${E(p.name)}</span><span>›</span></button>`).join('')}</div>`,'oryn-v2-browser')}${panel(`<div class="oryn-v2-panel-heading"><span>${E(S.selected?.name||'No pattern')}</span><span>${S.coords.length} THR points</span></div><div class="oryn-v2-tabline"><button class="${S.view==='artwork'?'active':''}" data-action="view-art">Artwork</button><button class="${S.view==='live'?'active':''}" data-action="view-live">Live execution</button><button disabled title="Physical sensor feedback is not installed">Measured position unavailable</button></div>${showActiveOrPreview(S.coords,S.rotation)}<div class="oryn-v2-caption">Artwork displays the full path. Live execution follows backend-reported queued waypoints, not measured physical position.</div>${action('run-pattern','Run selected pattern','primary')} ${action('stop','Stop execution','danger')}`,'oryn-v2-main-canvas')}${panel(`<span class="oryn-v2-label">INSPECTOR</span><h2>Pattern properties</h2>${details([['Name',S.selected?.name||'None'],['Points',String(S.coords.length)],['Rotation preview',S.rotation+'°']])}<input type="range" id="rotate-preview" min="0" max="270" step="90" value="${S.rotation}" aria-label="Preview rotation"/><p class="oryn-v2-slim">Preview rotation does not change motor commands.</p><label class="oryn-v2-labeltext" for="pre-execution">Before pattern</label><select id="pre-execution" class="oryn-v2-input"><option value="none">None (initial test)</option><option value="adaptive">Adaptive</option><option value="clear_from_in">Clean from center</option><option value="clear_from_out">Clean from outer edge</option></select>${safety()}${warning('Run only with confirmed home/reference and radial calibration. If the machine is not referenced, use Motion first.')}${action('choose-upload','Import THR pattern')}`,'oryn-v2-inspector')}</div>`}
function forge(){const g=S.forge;return panel(`<div class="oryn-v2-panel-heading"><span>PATTERN FORGE</span><span>Convert artwork into ORYN machine-ready THR geometry</span></div><div class="oryn-v2-forge-grid"><div><label class="oryn-v2-labeltext">Artwork / vector / toolpath</label><input id="forge-file" class="oryn-v2-input" type="file" accept=".png,.jpg,.jpeg,.webp,.bmp,.svg,.dxf,.gcode,.nc,.ngc,.tap,.thr"/><div class="oryn-v2-forge-params"><label>Threshold<input id="forge-threshold" class="oryn-v2-input" type="number" min="0" max="255" value="128"/></label><label>Fit within table<input id="forge-fit" class="oryn-v2-input" type="number" min=".1" max="1" step=".01" value=".94"/></label><label>Smoothing<input id="forge-smoothing" class="oryn-v2-input" type="number" min="0" max="10" value="1"/></label><label>Simplify<input id="forge-simplify" class="oryn-v2-input" type="number" min="0" max=".5" step=".0005" value=".0025"/></label><label>Rotation (degrees)<input id="forge-rotation" class="oryn-v2-input" type="number" step="1" value="0"/></label><label>Detail<input id="forge-detail" class="oryn-v2-input" type="number" min="1" max="8" value="3"/></label></div><label class="oryn-v2-checkline"><input type="checkbox" id="forge-invert"/> Invert image</label><div class="oryn-v2-actionbar">${action('forge-preview','Generate preview','primary')}</div><p class="oryn-v2-slim">Conversion happens on the Pi. Pattern preview creates no motor movement.</p></div><div><span class="oryn-v2-label">GENERATED ARTWORK</span>${svgFor(g.coords)}${details([['Status',g.status],['Generated coordinates',String(g.points||0)]])}<label class="oryn-v2-labeltext">Save pattern as</label><input class="oryn-v2-input" id="forge-name" value="ORYN artwork" placeholder="Pattern name"/><div class="oryn-v2-actionbar">${action('forge-save','Save into Gallery','primary')}</div></div></div>`,'oryn-v2-forge')}

function sequence(){return `<div class="oryn-v2-content-grid">${panel(`<span class="oryn-v2-label">SAVED SEQUENCES</span><h2>Playlists</h2><div class="oryn-v2-smallgap">${S.playlists.length?S.playlists.map(p=>`<button class="oryn-v2-cardbtn ${S.playlist===p?'active':''}" data-action="choose-playlist" data-playlist="${E(p)}">${E(p)}</button>`).join(''):'No playlists found. Create one below.'}</div><div class="oryn-v2-actionbar">${action('reload-playlists','Refresh playlists')}</div><label class="oryn-v2-labeltext">Create or edit playlist name</label><input class="oryn-v2-input" id="seq-name" value="${E(S.playlist||'')}" placeholder="My ORYN sequence"/><label class="oryn-v2-labeltext">Pattern to add</label><select class="oryn-v2-input" id="seq-pattern"><option value="">Choose a pattern</option>${S.patterns.filter(p=>!p.name.toLowerCase().includes('clear')).map(p=>`<option value="${E(p.path)}">${E(p.name)}</option>`).join('')}</select><div class="oryn-v2-actionbar">${action('seq-add','Add to sequence')}${action('seq-save','Save sequence','primary')}</div><div class="oryn-v2-smallgap">${S.sequenceFiles.map((p,i)=>`<div class="oryn-v2-seq-row"><span>${i+1}. ${E(leaf(p))}</span><button data-action="seq-up" data-index="${i}" title="Move earlier">↑</button><button data-action="seq-down" data-index="${i}" title="Move later">↓</button><button data-action="seq-remove" data-index="${i}" title="Remove">×</button></div>`).join('')}</div>`)}${panel(`<span class="oryn-v2-label">EXECUTION</span><h2>${E(S.playlist||'No sequence selected')}</h2><p class="oryn-v2-slim">Create and reorder pattern sequences here. Execution uses the ORYN playlist engine with a single pass by default.</p>${details([['Items',String(S.sequenceFiles.length)],['Controller',connected()?'Connected':'Disconnected']])}${safety()}<div class="oryn-v2-actionbar">${action('run-playlist','Run selected sequence','primary')}${action('stop','Stop execution','danger')}</div>${warning('Save the playlist before executing. Confirm home, clearance and calibration first.')}`)}</div>`}

function clean(){return `<div class="oryn-v2-content-grid">${panel(`<div class="oryn-v2-panel-heading"><span>CLEANING TRAJECTORY</span><span>${S.cleanCoords.length} THR points</span></div>${activePattern()?liveCanvas():svgFor(S.cleanCoords)}<div class="oryn-v2-caption">Preview does not send movement commands or modify pattern geometry.</div>${action('run-clean','Run selected cleaning path','primary')} ${action('stop','Stop cleaning','danger')}`,'oryn-v2-main-canvas')}${panel(`<span class="oryn-v2-label">CLEAN MODE</span><h2>Surface preparation</h2><div class="oryn-v2-clean-options">${cleanFiles.map(p=>`<button data-action="select-clean" data-clean="${E(p)}" class="${S.clean===p?'active':''}">${E(p.replace('clear_','').replace('.thr','').replaceAll('_',' '))}</button>`).join('')}</div>${safety()}${warning('Only run the cleaning file matched to your table type. Full-length physical cleaning must be verified on this machine before unattended operation.')}<p class="oryn-v2-slim">Cleaning operations use the existing verified execution engine. Do not run unsupervised until the full physical cleaning cycle passes.</p>`)}</div>`}
function calibrationGuide(){
 const stages=[['reference','1 · Home reference'],['theta','2 · Rotation 360°'],['rho','3 · Table radius'],['verify','4 · Check & finish']];
 const explain={
  reference:`<h3>First identify the true center</h3><p>Stop every pattern. Connect the controller and ensure the mechanism has clearance. Use the previously established ORYN HOME procedure only when motor power and physical position are known. <b>USB connected, GRBL coordinate zero, or a ball manually placed at center do NOT prove HOME.</b></p><p>Do not move to a saved perimeter with an unverified or outdated calibration. If this is a new/larger table, do not assume its previous radial travel value is correct.</p>`,
  theta:`<h3>Teach one exact revolution</h3><p>Mark the rotating arm orientation. Select <b>Start rotation teaching</b>, then make short, supervised X jogs with the + / − buttons below until the arm has returned to its mark after <b>exactly one complete turn</b>. Save only after visually verifying 360°. Your existing 10:1 gearing setting is not changed.</p><p>If the theta gearing and drive have not changed, the previously measured theta travel may remain valid; verify it instead of automatically recalibrating.</p>`,
  rho:`<h3>Teach the usable radius of THIS table</h3><p>From a physically established center reference, choose <b>Start radial teaching</b>. Use small + Y jogs to move the ball outward, slowing and reducing the step near the edge. Stop at the <b>safe usable drawing perimeter</b>, BEFORE any hard stop, and then save. A larger table normally needs a new saved radial travel value.</p><p>The displayed jog increment is in controller units—not millimetres of table diameter. Do not guess travel from the table diameter or from an old machine profile.</p>`,
  verify:`<h3>Confirm before drawing</h3><p>Check the physical HOME reference, the actual 360° return, and the center-to-safe-edge travel. The software may show “Saved” without confirming physical accuracy. Return the ball only through a known, safe path and verify both positions before running patterns.</p><p>Use one short supervised pattern first. Cleaning and full-length operation remain separate acceptance tests.</p>`
 };
 return panel(`<span class="oryn-v2-label">GUIDED MACHINE SETUP</span><h2>Calibrate your ORYN table in four steps</h2><p class="oryn-v2-slim">Follow the steps in order for a new table. Revisit only the relevant step when changing the table size. Calibration is physical teaching, not a change to motion mathematics.</p><div class="oryn-v2-guide-tabs">${stages.map(([key,name])=>`<button type="button" class="${S.calGuide===key?'active':''}" data-action="guide-step" data-step="${key}">${name}</button>`).join('')}</div><div class="oryn-v2-guide-explain" role="region" aria-label="Calibration instructions">${explain[S.calGuide]||explain.reference}</div>${S.calGuide==='verify'?details([['Controller',connected()?'Connected':'Disconnected'],['Physical home',S.status?.physical_home_verified?'Software verified; visually confirm':'Not physically verified'],['Theta 360° taught',S.rot?.calibrated?'Saved (verify physically)':'Not saved'],['Center to edge taught',S.rho?.calibrated?'Saved (verify physically)':'Not saved'],['Theta travel',S.rot?.theta_revolution_units!=null?Number(S.rot.theta_revolution_units).toFixed(3)+' controller units':'—'],['Radial travel',S.rho?.rho_travel_units!=null?Number(S.rho.rho_travel_units).toFixed(3)+' controller units':'—']]):''}<div class="oryn-v2-actionbar">${action('refresh-status','Refresh readings')}${action('stop','STOP','danger')}</div>`,'oryn-v2-guide');
}
function calCard(axis){
 const theta=axis==='theta',c=theta?S.rot:S.rho,canJog=!!c?.active&&!S.calBusy[axis],notice=S.calFeedback[axis];
 const id=theta?'theta':'rho',title=theta?'Teach rotation — ONE full turn':'Teach radial travel — center to safe edge';
 const val=theta?c?.theta_revolution_units:c?.rho_travel_units;
 const step=theta?S.calStep:S.radialStep;
 const instructions=theta?'Place a stationary angle reference. Jog slowly until exactly 360° is completed, then save.':'Start from the verified physical center. Jog outward in small increments; stop BEFORE a physical limit and save the safe drawing radius.';
 return `<section class="oryn-v2-calcard" id="cal-${id}"><div class="oryn-v2-calhead"><div><span class="oryn-v2-label">${theta?'STEP 2 • THETA':'STEP 3 • RHO'}</span><h3>${title}</h3></div><span class="oryn-v2-tag ${c?.calibrated?'verified':'pending'}">${c?.calibrated?'Previously saved':'Not calibrated'}</span></div><p class="oryn-v2-slim">${instructions}</p>${details([['Previously saved',val!=null?Number(val).toFixed(3)+' controller units':'Not saved'],['Session',canJog?'Teaching in progress':'Not started'],['Travel taught this session',c?.current_units!=null?Number(c.current_units).toFixed(3)+' controller units':'—']])}<div class="oryn-v2-cal-state ${c?.active?'active':'inactive'}"><b>${c?.active?'TEACHING SESSION ACTIVE':'TEACHING SESSION NOT ACTIVE'}</b><span>${c?.active?'Jog with the + and − buttons below. The numbers update after each confirmed move.':'Press Start teaching. Jogs become enabled ONLY after the Pi confirms an active session.'}</span></div><div class="oryn-v2-actionbar">${action('cal-start-'+id,c?.active?'Restart teaching session':theta?'Start rotation teaching':'Start radial teaching','primary')}${action('cal-refresh-'+id,'Check session status')}</div><div id="cal-feedback-${id}" class="oryn-v2-cal-feedback ${notice?.bad?'bad':notice?'ok':''}" role="status" aria-live="polite">${E(notice?.text||'No movement is permitted until the teaching session is active.')}</div><div class="oryn-v2-jog"><label class="oryn-v2-labeltext" for="${id}-step">Jog increment · controller units (smaller near the edge)</label><input id="${id}-step" class="oryn-v2-input" type="number" min="0.01" max="${theta?'25':'10'}" step="0.01" value="${step}"/><button type="button" data-action="cal-jog-minus-${id}" ${!canJog?'disabled title="Start teaching and confirm active session first"':''}>${theta?'↶ − Rotate':'← − Inward'}</button><button type="button" data-action="cal-jog-plus-${id}" ${!canJog?'disabled title="Start teaching and confirm active session first"':''}>${theta?'↷ + Rotate':'→ + Outward'}</button></div><div class="oryn-v2-actionbar"><button type="button" class="oryn-v2-action primary" data-action="cal-save-${id}" ${!canJog?'disabled':''}>${theta?'Save exactly 360°':'Save safe edge travel'}</button>${!theta?action('cal-cancel-rho','Cancel radial teaching'):''}</div><details class="oryn-v2-native-advanced"><summary>Advanced: enter an independently measured value</summary><p class="oryn-v2-slim">Only when you have physically measured the exact travel in controller units. This does not move motors, but overwrites the saved calibration.</p><div class="oryn-v2-actionbar"><input id="${id}-exact" class="oryn-v2-input" type="number" step="0.001" placeholder="Controller units" value="${val??''}"/>${action('cal-set-'+id,'Save measured value')}</div>${action('cal-reset-'+id,'Clear saved calibration','danger')}</details></section>`;
}
function motion(){return `<div class="oryn-v2-motion-top">${panel(`<span class="oryn-v2-label">MACHINE CONNECTION</span><h2>Controller connection</h2><p class="oryn-v2-slim">Select the detected USB controller and connect before teaching travel. Connection alone does not establish HOME.</p><select id="serial-select" class="oryn-v2-input"><option value="">Select serial port</option>${S.ports.map(p=>{const value=typeof p==='string'?p:p.device||p.port||p.path||'';return `<option value="${E(value)}" ${S.selectedPort===value?'selected':''}>${E(value)}</option>`}).join('')}</select><div class="oryn-v2-actionbar">${action('refresh-ports','Scan ports')}${action('connect-serial','Connect','primary')}${action('disconnect-serial','Disconnect')}</div>${details([['Connection',connected()?'Connected':'Disconnected'],['Port',S.serial?.port||'Not reported'],['Firmware',firmwareLabel()]])}`)}</div>${calibrationGuide()}${S.calGuide==='reference'?panel(`<span class="oryn-v2-label">STEP 1 · PHYSICAL CENTER REFERENCE</span><h2>HOME and safe positioning</h2>${warning('HOME can physically move the motor. If you have changed the table radius, do not trust old travel or use automatic Move to Perimeter until the new radial travel has been verified.')}${details([['Physical HOME',S.status?.physical_home_verified===true?'Software verified; confirm ball':'NOT verified'],['HOME routine',S.status?.homing_success===true?'Reported complete; verify visually':S.status?.homing_success===false?'Failed':'Not run this session']])}<div class="oryn-v2-actionbar">${action('home-machine','Run supervised HOME','primary')}${action('stop','STOP','danger')}</div><p class="oryn-v2-slim">If sensorless HOME requires the old perimeter value, confirm the center reference using your established machine setup procedure before starting radial teaching. Do not force the arm against a hard stop.</p>`):''}${S.calGuide==='theta'?`<div class="oryn-v2-calgrid">${calCard('theta')}</div>`:''}${S.calGuide==='rho'?`<div class="oryn-v2-calgrid">${calCard('rho')}</div>`:''}${S.calGuide==='verify'?panel(`<span class="oryn-v2-label">PHYSICAL VALIDATION</span><h2>Ready to verify, not yet certified</h2><p class="oryn-v2-slim">Saved values do not guarantee correct mechanical travel. Verify HOME and endpoint positions in person before enabling a drawing or cleaning cycle.</p><div class="oryn-v2-actionbar">${action('open-studio','Preview a short pattern','primary')}${action('stop','STOP','danger')}</div>`):''}`;}

function light(){const led=S.led||{};return `<div class="oryn-v2-content-grid">${panel(`<span class="oryn-v2-label">LIGHTING ENVIRONMENT</span><div class="oryn-v2-glow-disc" style="margin:25px auto;max-width:230px"></div><p class="oryn-v2-slim">Provider: ${E(led.provider||'none')} · Local status: ${S.ledStatus?.connected?'Connected':S.ledStatus?.message||'Not checked'}</p><div class="oryn-v2-actionbar">${action('led-check','Check connection')}${action('led-on','Lights ON','primary')}${action('led-off','Lights OFF')}</div><label class="oryn-v2-labeltext">Color</label><input id="led-color" type="color" value="${E(S.lightColor||'#ffb470')}" style="width:100%;height:56px;margin:8px 0"/><label class="oryn-v2-labeltext">Brightness: <span id="bright-value">${S.lightBrightness??50}</span>%</label><input type="range" id="led-brightness" min="0" max="100" value="${S.lightBrightness??50}" style="width:100%"/>${action('led-apply','Apply color & brightness','primary')}`,'oryn-v2-light-ring')}${panel(`<span class="oryn-v2-label">CONTROLLER SETUP</span><h2>Lighting provider</h2><select id="led-provider" class="oryn-v2-input"><option value="magic_home" ${led.provider==='magic_home'?'selected':''}>Magic Home RGB Wi-Fi</option><option value="wled" ${led.provider==='wled'?'selected':''}>WLED</option><option value="dw_leds" ${led.provider==='dw_leds'?'selected':''}>GPIO / ORYN LEDs</option><option value="none" ${led.provider==='none'?'selected':''}>None</option></select><label class="oryn-v2-labeltext">LED controller IPv4 address</label><input id="led-ip" class="oryn-v2-input" value="${E(led.magic_home_ip||led.wled_ip||'')}" placeholder="192.168.1.100"/>${action('led-save','Save LAN connection','primary')}<p class="oryn-v2-slim">Use the IP already found during your successful Wi-Fi pairing. No cloud required for classic Magic Home protocol. Existing WLED and GPIO providers remain available.</p><p class="oryn-v2-slim">Additional supported lighting modes depend on the selected LED controller. Core on/off, RGB and brightness controls are available here.</p>`)}</div>`}
function firmwareLabel(){if(!connected())return 'Connect controller to identify';const v=S.serial?.firmware_version||S.status?.firmware_version;if(v)return ((S.serial?.firmware_type||S.status?.firmware_type)==='fluidnc'?'FluidNC ':'GRBL ')+String(v);return ((S.serial?.firmware_type||S.status?.firmware_type)==='grbl-compatible'?'GRBL-compatible — version not reported':'Connected — version not reported')}
function wifiPanel(){
 const mode=S.wifi?.mode||'unknown',ssid=S.wifi?.ssid||'',ip=S.wifi?.ip||'—';
 const networks=Array.isArray(S.wifiNetworks)?S.wifiNetworks:[];
 const installed=S.wifi?.hotspot_configured===true;
 return panel(`<span class="oryn-v2-label">NETWORK SETUP</span><h2>Wi-Fi & ORYN hotspot</h2>
 ${details([['Mode',mode==='client'?'Connected to router':mode==='hotspot'?'ORYN setup hotspot':mode==='disconnected'?'Disconnected':'Not yet determined'],['Connected network',ssid||'None'],['Pi IP address',ip],['ORYN fallback hotspot',installed?(S.wifi?.hotspot_recovery_enabled?'Ready when home Wi-Fi is unavailable':'Profile exists; recovery service not enabled'):'Not configured on this Pi']])}
 <p class="oryn-v2-slim">The ORYN setup Wi-Fi appears when no saved router is reachable and fallback hotspot service is installed. With one Pi Wi-Fi radio it normally does NOT broadcast while connected to your home router.</p>
 <div class="oryn-v2-actionbar">${action('wifi-scan','Scan nearby Wi-Fi','primary')}${action('wifi-status','Refresh network status')}</div>
 <label class="oryn-v2-labeltext" for="wifi-select">Choose another Wi-Fi network</label>
 <select class="oryn-v2-input" id="wifi-select"><option value="">Select network</option>${networks.map(n=>`<option value="${E(n.ssid)}">${E(n.ssid)}${n.active?' · Connected':''}${n.saved?' · Saved':''} · ${Number(n.signal||0)}%</option>`).join('')}</select>
 <label class="oryn-v2-labeltext" for="wifi-password">Wi-Fi password (leave empty for saved or open networks)</label>
 <input id="wifi-password" type="password" autocomplete="new-password" class="oryn-v2-input" placeholder="Network password"/>
 <div class="oryn-v2-actionbar">${action('wifi-save','Save network without switching')}${action('wifi-connect','Connect to selected Wi-Fi','primary')}</div>
 <p class="oryn-v2-slim">Switching Wi-Fi can change the Pi IP address and disconnect this page or SSH. Your existing saved networks are retained. An unsupported hotspot cannot be created by this screen until its Pi service is installed.</p>
 `)}
function system(){return `<div class="oryn-v2-content-grid">${wifiPanel()}${panel(`<span class="oryn-v2-label">SYSTEM STATUS</span><h2>ORYN Studio V2</h2>${details([['Application','ORYN Studio V2 · Studio Kinematics™'],['Backend',S.version],['Controller',connected()?'Connected':'Offline'],['Port',S.serial?.port||'None'],['Firmware',firmwareLabel()],['Machine profile',machineLabel(S.status?.table_type)],['Motion configuration','ORYN standard 10:1'],['LED provider',ledLabel(S.led?.provider)],['Current file',S.status?.current_file||'None']])}<div class="oryn-v2-actionbar">${action('refresh-status','Refresh system status','primary')}${action('open-motion','Connect a controller')}</div>`)}${panel(`<span class="oryn-v2-label">FIRMWARE & DIAGNOSTICS</span><h2>Controller identification</h2><p class="oryn-v2-slim">ORYN reads the controller firmware version after a supported connection. No firmware is installed or flashed from this screen.</p>${connected()?details([['Connection','Online'],['Reported firmware',firmwareLabel()]]) : warning('No controller is connected. Attach your Arduino/ESP32 to the Pi and connect in Motion. A missing firmware label does not mean the controller firmware was erased.')}<h3>Supported transports</h3><div class="oryn-v2-device-types"><span>Arduino GRBL (USB)</span><span>ESP32 FluidNC</span><span>ESP32 GRBL</span><span>MKS DLC32</span></div><div class="oryn-v2-actionbar">${action('refresh-status','Check again')}${action('open-motion','Open Motion','primary')}</div><p class="oryn-v2-slim">Automatic firmware identification depends on the live controller response. Never flash firmware merely to fix an offline status.</p>`)}${panel(`<span class="oryn-v2-label">MACHINE READINESS</span><h2>Calibration & safety</h2>${readiness()}<div class="oryn-v2-actionbar">${action('open-motion','Configure machine','primary')}${action('open-light','Configure lighting')}</div>`)}${panel(`<span class="oryn-v2-label">NETWORK & PRODUCT</span><h2>ORYN · Designed to Move</h2><p class="oryn-v2-slim">Studio Kinematics™. Local-first machine control with dedicated Pi/USB and network LED providers.</p>${details([['Controller status',connected()?'Connected':'Disconnected'],['Backend communication',S.online?'Online':'Not connected'],['Firmware flashing','Not performed by this interface']])}<p class="oryn-v2-slim">To update from your GitHub repository, use your controlled Pi deployment process. Do not overwrite working machine configurations without a deliberate backup.</p>` )}</div>`}

function mainContent(){return S.page==='studio'?studio()+forge():({home,gallery,studio,sequence,clean,motion,light,system}[S.page]||home)()}
function draw(){const header=names[S.page];root.innerHTML=`<div class="oryn-v2-shell"><aside class="oryn-v2-rail" id="v2-rail" aria-label="ORYN V2 navigation"><button class="oryn-v2-mark" data-action="nav" data-page="home" title="ORYN home">◎</button><div class="oryn-v2-rail-links">${nav.map(([key,icon,name])=>`<button class="oryn-v2-navbtn ${S.page===key?'active':''}" data-action="nav" data-page="${key}" aria-label="${name}" aria-current="${S.page===key?'page':'false'}"><span style="font-size:23px">${icon}</span><span>${name}</span></button>`).join('')}</div></aside><div class="oryn-v2-viewport"><header class="oryn-v2-topbar"><div class="oryn-v2-top-left"><button class="oryn-v2-mobile-menu" data-action="menu" aria-label="Toggle navigation">☰</button><div><b>ORYN <span>STUDIO</span></b><small>DESIGNED TO MOVE · STUDIO KINEMATICS™</small></div></div><div class="oryn-v2-top-right"><span class="oryn-v2-app-version">ORYN V2 · CP2L</span>${pills()}</div></header><main class="oryn-v2-screen"><div class="oryn-v2-heading"><div><span class="oryn-v2-label">WORKSPACE / ${S.page.toUpperCase()}</span><h1>${header[0]}</h1><p>${header[1]}</p></div>${S.page==='motion'?action('refresh-status','Refresh machine'):S.page==='system'?action('refresh-status','Refresh status'):S.page==='studio'?action('choose-upload','Import pattern'):''}</div><div class="oryn-v2-msg" id="oryn-msg">${E(S.msg)}</div>${mainContent()}<input id="import-thr" type="file" accept=".thr,text/plain" hidden/><footer class="oryn-v2-execution"><div><span style="color:#e3b48a">●</span><span>${S.status?.is_running?'EXECUTING':S.status?.is_homing?'HOMING':S.status?.is_paused?'PAUSED':'NOT EXECUTING'}</span><span class="oryn-v2-execution-detail">${E(leaf(S.status?.current_file)||'No active pattern')}</span></div><div><span id="oryn-live-footer-progress">${S.status?.progress?.percentage!=null?Number(S.status.progress.percentage).toFixed(1)+'% reported (not physical feedback)':'No physical position feedback'}</span><button class="oryn-v2-stop" data-action="stop">STOP</button></div></footer></main></div></div>`;const inp=document.getElementById('physical-check');if(inp)inp.onchange=e=>{S.physicalCheck=e.target.checked};const ps=document.querySelector('#pattern-search,#studio-search');if(ps)ps.oninput=e=>{const pos=e.target.selectionStart;S.search=e.target.value;updateGallery();if(S.page==='gallery'||S.page==='studio'){draw();const renewed=document.querySelector('#pattern-search,#studio-search');if(renewed){renewed.focus();try{renewed.setSelectionRange(pos,pos)}catch{}}}};const bright=document.getElementById('led-brightness');if(bright)bright.oninput=e=>{S.lightBrightness=Number(e.target.value);document.getElementById('bright-value').textContent=e.target.value};const col=document.getElementById('led-color');if(col)col.oninput=e=>S.lightColor=e.target.value;const rot=document.getElementById('rotate-preview');if(rot)rot.oninput=e=>{S.rotation=Number(e.target.value);draw()};if(S.page==='gallery'&&!thumbnailBusy)loadThumbnails();}
function updateGallery(){const q=S.search.trim().toLowerCase();S.gallery=S.patterns.filter(p=>(p.name+' '+(p.category||'')).toLowerCase().includes(q))}
function selectPage(p){if(!names[p])return;S.page=p;S.msg='';S.active=60;S.physicalCheck=false;history.replaceState(null,'','#'+p);if(p==='clean')loadCoords(S.clean,true);if(p==='sequence')loadPlaylists();if(p==='light'||p==='system')loadLed();if(p==='system')loadWifi(false);if(p==='motion')loadPortsAndCal();draw()}
async function loadPatterns(){try{const p=await api('/list_theta_rho_files_with_metadata');S.patterns=Array.isArray(p)?p.filter(x=>x&&typeof x.path==='string'):[];updateGallery();if(!S.selected){S.selected=S.patterns.find(x=>x.path.toLowerCase().endsWith('/star.thr')||x.path.toLowerCase()==='star.thr')||S.patterns.find(x=>!x.name.toLowerCase().includes('clear'))||S.patterns[0];if(S.selected)await loadCoords(S.selected.path)}else draw();if(S.page==='gallery')loadThumbnails()}catch(e){message('Pattern library unavailable: '+e.message,true)}}
async function loadCoords(file,isClean=false){try{const data=await api('/get_theta_rho_coordinates',{file_name:file});const coords=Array.isArray(data.coordinates)?data.coordinates:[];if(isClean)S.cleanCoords=coords;else S.coords=coords;draw()}catch(e){if(isClean)S.cleanCoords=[];else S.coords=[];message('Pattern coordinates unavailable: '+e.message,true)}}
async function loadPlaylists(){try{S.playlists=await api('/list_all_playlists');if(!Array.isArray(S.playlists))S.playlists=[];draw()}catch(e){message('Playlist fetch: '+e.message,true)}}
async function loadWifi(scan=false){
 const paths=scan?['/api/wifi/status','/api/wifi/saved','/api/wifi/networks']:['/api/wifi/status','/api/wifi/saved'];
 const values=await Promise.allSettled(paths.map(x=>api(x)));
 if(values[0].status==='fulfilled')S.wifi=values[0].value;
 if(values[1].status==='fulfilled')S.wifiSaved=values[1].value;
 if(scan){if(values[2].status==='fulfilled')S.wifiNetworks=values[2].value;else message('Wi-Fi scan unavailable: '+values[2].reason.message,true)}
 if(S.page==='system')draw();
}
async function loadLed(){try{S.led=await api('/get_led_config');draw()}catch(e){message('LED settings: '+e.message,true)}}
async function loadPortsAndCal(){const results=await Promise.allSettled([api('/list_serial_ports'),api('/api/rotation-calibration'),api('/api/perimeter-calibration')]);if(results[0].status==='fulfilled'){const res=results[0].value;S.ports=Array.isArray(res)?res:Array.isArray(res.ports)?res.ports:[]}if(results[1].status==='fulfilled')S.rot=results[1].value;if(results[2].status==='fulfilled')S.rho=results[2].value;try{S.serial=await api('/serial_status')}catch{}draw()}
async function loadThumbnails(){
 if(thumbnailBusy)return;
 thumbnailBusy=true;
 try{
  const files=S.gallery.slice(0,S.active||60).map(p=>p.path).filter(p=>!S.previews[p]);
  for(let i=0;i<files.length;i+=8){
   if(S.page!=='gallery')break;
   try{
    const d=await api('/preview_thr_batch',{file_names:files.slice(i,i+8)});
    for(const [p,v] of Object.entries(d||{}))if(v?.image_data?.startsWith('data:image/'))S.previews[p]=await recolor(v.image_data);
    if(S.page==='gallery')draw();
   }catch(e){console.warn('ORYN thumbnail unavailable',e)}
  }
 }finally{thumbnailBusy=false;}
}
function recolor(src){return new Promise(resolve=>{const im=new Image();im.onload=()=>{try{const c=document.createElement('canvas');c.width=im.naturalWidth;c.height=im.naturalHeight;const ctx=c.getContext('2d',{willReadFrequently:true});ctx.drawImage(im,0,0);const pixels=ctx.getImageData(0,0,c.width,c.height),b=pixels.data;for(let i=0;i<b.length;i+=4){if(b[i+3]&&b[i]<=35&&b[i+1]<=35&&b[i+2]<=35){b[i]=236;b[i+1]=208;b[i+2]=164;b[i+3]=Math.min(255,Math.round(b[i+3]*2.8))}}ctx.putImageData(pixels,0,0);resolve(c.toDataURL('image/webp',.9))}catch{resolve(src)}};im.onerror=()=>resolve(src);im.src=src})}
async function refreshStatus(){try{S.serial=await api('/serial_status')}catch(e){S.serial={connected:false,port:null}}if(S.page==='motion')await loadPortsAndCal();else draw()}
function requiresSafeRun(label){if(!connected()){message('Controller not connected: use Motion → Connect first.',true);return false}if(isRunning()){message('Controller is busy; stop/finish current execution first.',true);return false}if(!S.physicalCheck){message('Confirm physical home/reference and clearance using the checkbox before starting.',true);return false}const cal=!S.status?.theta_calibrated||!S.status?.rho_calibrated;const note=cal?'\nWARNING: saved theta/rho calibration is not confirmed. Backend may reject the run.':'';return confirm(`Start ${label}?\n\nConfirm the ball is physically referenced, the path is safe, and you can cut motor power if necessary.${note}\n\nThis is a real motor operation.`)}
async function command(endpoint,data,label){try{const res=await api(endpoint,data);message(label+' — request accepted. Observe physical mechanism.');return res}catch(e){message(label+': '+e.message,true);return null}}
async function dispatchAction(event){const t=event.target.closest('[data-action]');if(!t)return;const a=t.dataset.action;try{if(a==='nav')return selectPage(t.dataset.page);if(a==='menu'){document.getElementById('v2-rail').classList.toggle('mobile-open');return}if(a==='forge-preview'){
 const file=document.getElementById('forge-file')?.files?.[0];
 if(!file){message('Select artwork to convert first.',true);return}
 if(file.size>25*1024*1024){message('Artwork exceeds the 25 MB limit.',true);return}
 const form=new FormData();form.append('file',file);
 for(const [id,key] of [['threshold','threshold'],['fit','fit'],['smoothing','smoothing'],['simplify','simplify'],['rotation','rotation_deg'],['detail','detail']])form.append(key,document.getElementById('forge-'+id)?.value||'');
 form.append('invert',document.getElementById('forge-invert')?.checked?'true':'false');
 S.forge={token:null,coords:[],points:0,status:'Converting…',stats:{}};draw();
 try{
  // FormData is intentionally sent without a JSON content-type.
  const res=await fetch('/api/v2/pattern-generator/preview-start',{method:'POST',body:form});
  if(!res.ok)throw Error('Preview request failed: HTTP '+res.status);
  const result=await res.json();if(!result.job_id)throw Error('No conversion job returned');
  let ready=null;
  for(let tries=0;tries<90;tries++){
   await new Promise(resolve=>setTimeout(resolve,1000));
   const job=await api('/api/v2/pattern-generator/preview-job/'+encodeURIComponent(result.job_id));
   if(job.status==='error')throw Error(job.error||'Conversion failed');
   if(job.status==='done'){ready=job;break}
  }
  if(!ready)throw Error('Conversion took too long. Retry with smaller artwork.');
  S.forge={token:ready.token,coords:Array.isArray(ready.coordinates)?ready.coordinates:[],points:ready.points||0,status:'Preview ready',stats:ready.stats||{}};
  draw();message('Artwork converted. Review preview before saving; no motors were moved.');
 }catch(e){S.forge.status='Conversion failed';draw();message('Pattern Forge: '+e.message,true)}
 return;
}
if(a==='forge-save'){
 if(!S.forge?.token){message('Generate a preview before saving.',true);return}
 const name=document.getElementById('forge-name')?.value.trim();if(!name){message('Name the pattern first.',true);return}
 const saved=await command('/api/v2/pattern-generator/save',{token:S.forge.token,name},'Save generated pattern');
 if(saved){S.forge.token=null;await loadPatterns();message('Saved '+name+' to ORYN Gallery')}
 return;
}
if(a==='choose-upload'){document.getElementById('import-thr')?.click();return}
if(a==='wifi-scan'){await loadWifi(true);message('Wi-Fi scan finished. Choose a network, or keep the current connection.');return}
if(a==='wifi-status'){await loadWifi(false);return}
if(a==='wifi-save'||a==='wifi-connect'){
 const ssid=document.getElementById('wifi-select')?.value||'';
 const password=document.getElementById('wifi-password')?.value||'';
 if(!ssid){message('Scan and select a Wi-Fi network first.',true);return}
 const switching=a==='wifi-connect';
 if(!confirm(switching?'Change ORYN to Wi-Fi '+ssid+'? This may disconnect the browser and SSH and change the Pi IP address.':'Save credentials for '+ssid+' without switching away from the current Wi-Fi?'))return;
 if(switching)message('Connecting to '+ssid+'… If the page disconnects, reconnect through your router or oryn.local.');
 try{const result=await api(switching?'/api/wifi/connect':'/api/wifi/save',{ssid,password});message(result?.message||'Wi-Fi request sent.');if(!switching)await loadWifi(false)}
 catch(e){message('Wi-Fi request: '+e.message+'; check the Pi/router connection before retrying.',true)}
 return;
}
if(a==='guide-step'){const next=t.dataset.step;if(['reference','theta','rho','verify'].includes(next)){S.calGuide=next;draw()}return;}
if(a==='open-light')return selectPage('light');
if(a==='move-center'||a==='move-perimeter'){
 if(!connected()||isRunning()){message('Connect an idle controller first.',true);return}
 if(!confirm('Real motor movement to '+(a==='move-center'?'CENTER':'PERIMETER')+'. Confirm physical calibration, clear travel and emergency power access.'))return;
 await command(a==='move-center'?'/move_to_center':'/move_to_perimeter',{},a==='move-center'?'Move to center':'Move to perimeter');return;
}
if(a.startsWith('cal-')){
 const tokens=a.split('-'),verb=tokens[1],axis=verb==='jog'?tokens[3]:tokens[2],theta=axis==='theta';
 if(!['theta','rho'].includes(axis))return;
 const name=theta?'rotation':'perimeter',src='/api/'+name+'-calibration';
 const setFeedback=(text,bad=false)=>{S.calFeedback[axis]={text,bad};message(text,bad);draw();};
 if(S.calBusy[axis])return;
 if(verb==='refresh'){
  try{await loadPortsAndCal();setFeedback((theta?S.rot:S.rho)?.active?'Teaching active: jog buttons are enabled.':'No active teaching session. Press Start teaching first.');}
  catch(e){setFeedback('Cannot read calibration state: '+e.message,true)}
  return;
 }
 if(!connected()||isRunning()){setFeedback('Controller must be CONNECTED and IDLE. Stop any pattern and reconnect before calibration.',true);return;}
 let body={};
 if(verb==='start'){
  if(!confirm('Begin supervised '+(theta?'360° rotation':'center-to-safe-edge radial')+' teaching? Check motor power, physical reference, clearance and stop access. Starting a session alone does not move motors.'))return;
 }else if(verb==='jog'){
  const v=Number(document.getElementById(axis+'-step')?.value),max=theta?25:10;
  if(!Number.isFinite(v)||v<.01||v>max){setFeedback('Enter a valid step from 0.01 to '+max+' controller units.',true);return;}
  if(!((theta?S.rot:S.rho)?.active)){setFeedback('Teaching is not active. Press Start teaching and wait for ACTIVE before using a jog button.',true);return;}
  body={units:tokens[2]==='minus'?-v:v,speed:30};
  if(!confirm('REAL MOTOR MOVE: '+(theta?'theta':'rho')+' '+(body.units>0?'+':'')+body.units+' controller units at feed 30. Clear of hard stops?'))return;
 }else if(verb==='set'){
  const v=Number(document.getElementById(axis+'-exact')?.value);
  if(!Number.isFinite(v)||v<=0){setFeedback('Enter an independently measured positive travel value.',true);return;}
  if(!confirm('Override saved '+axis+' calibration with '+v+' controller units? Only if physically measured.'))return;
  body={units:v};
 }else if(verb==='reset'){
  if(!confirm('Clear saved '+axis+' calibration? This cannot be undone.'))return;
 }else if(verb==='save'){
  if(!((theta?S.rot:S.rho)?.active)){setFeedback('Start teaching and make controlled physical jogs before saving.',true);return;}
  if(!confirm('Save '+axis+' calibration? Verify '+(theta?'exactly ONE physical 360° rotation':'the real safe center-to-edge radius')+' before saving.'))return;
 }else if(verb==='cancel'&&axis==='rho'){
  if(!confirm('Cancel radial teaching without changing saved calibration?'))return;
 }else return;
 S.calBusy[axis]=true;
 S.calFeedback[axis]={text:verb==='start'?'Starting teaching on Raspberry Pi…':verb==='jog'?'Jog request sent; waiting for controller Idle…':'Sending '+verb+' request…',bad:false};
 draw();
 try{
  const res=await api(src+'/'+verb,body);
  if(res?.success!==true)throw Error('Controller did not confirm '+verb+'. No motion assumed.');
  // Confirm the state by reading the real backend, rather than enabling jogs from a popup alone.
  const session=await api(src);
  if(!session||typeof session.active!=='boolean')throw Error('Session state could not be confirmed; jogging remains blocked. Refresh state.');
  if(theta)S.rot=session;else S.rho=session;
  if(verb==='start'&&!session.active)throw Error('Start was acknowledged but Pi did NOT retain an active session. Jogging is blocked.');
  if(verb==='jog'&&!session.active)throw Error('Session ended unexpectedly after jog; stop and check connection.');
  const v=Number(session.current_units||0).toFixed(3);
  S.calFeedback[axis]={bad:false,text:verb==='start'?'ACTIVE. Choose a small step and press + / − to physically '+(theta?'rotate':'move the carriage')+'.':verb==='jog'?'Jog acknowledged and controller returned Idle. Session travel: '+v+' units. Check the physical position before the next step.':verb==='save'?'CALIBRATION SAVED. Verify the physical end position before running a pattern.':'Calibration '+verb+' confirmed.'};
  message(S.calFeedback[axis].text);
 }catch(e){
  // Read back state on errors (a rejected start must never leave fake active controls).
  try{const session=await api(src);if(theta)S.rot=session;else S.rho=session}catch{}
  let detail=e.message||String(e);
  const match=detail.match(/^HTTP \d+ (.*)$/);
  if(match){try{const d=JSON.parse(match[1]);detail=typeof d.detail==='string'?d.detail:JSON.stringify(d.detail||d)}catch{}}
  const tip=(verb==='start'&&!theta)?' If radial start is rejected, check that ORYN reports the ball at the true center (rho near 0), then use the approved HOME procedure.':' Check controller connection and idle status.';
  S.calFeedback[axis]={bad:true,text:'NOT STARTED / NOT COMPLETED: '+detail+tip};
  message(S.calFeedback[axis].text,true);
 }finally{S.calBusy[axis]=false;draw();}
 return;
}
if(a==='seq-add'){
 const p=document.getElementById('seq-pattern')?.value;
 if(!p){message('Select a pattern to add.',true);return}
 S.sequenceFiles.push(p);draw();return;
}
if(['seq-up','seq-down','seq-remove'].includes(a)){
 const i=Number(t.dataset.index);if(!Number.isInteger(i)||i<0||i>=S.sequenceFiles.length)return;
 if(a==='seq-remove')S.sequenceFiles.splice(i,1);else{const j=i+(a==='seq-up'?-1:1);if(j>=0&&j<S.sequenceFiles.length)[S.sequenceFiles[i],S.sequenceFiles[j]]=[S.sequenceFiles[j],S.sequenceFiles[i]]}
 draw();return;
}
if(a==='seq-save'){
 const name=document.getElementById('seq-name')?.value.trim();if(!name){message('Enter a playlist name.',true);return}
 if(!S.sequenceFiles.length){message('Add at least one pattern.',true);return}
 const res=await command('/create_playlist',{playlist_name:name,files:S.sequenceFiles},'Save sequence');if(res){S.playlist=name;await loadPlaylists()};return;
}
if(a==='open-studio')return selectPage('studio');if(a==='open-motion')return selectPage('motion');if(a==='choose-pattern'){S.selected=S.patterns.find(p=>p.path===t.dataset.path)||S.selected;S.rotation=0;if(!activePattern())S.view='artwork';selectPage('studio');return loadCoords(S.selected.path)}if(a==='select-clean'){S.clean=t.dataset.clean;draw();return loadCoords(S.clean,true)}if(a==='view-art'||a==='view-live'){S.view=a==='view-art'?'artwork':'live';return draw()}if(a==='more'){S.active=(S.active||60)+60;draw();return loadThumbnails()}if(a==='run-pattern'){if(S.selected&&requiresSafeRun('pattern '+S.selected.name))await command('/run_theta_rho',{file_name:S.selected.path,pre_execution:document.getElementById('pre-execution')?.value||'none'},'Pattern');return}if(a==='run-clean'){if(requiresSafeRun('cleaning '+S.clean))await command('/run_theta_rho',{file_name:S.clean,pre_execution:'none'},'Cleaning');return}if(a==='run-playlist'){if(S.playlist&&requiresSafeRun('sequence '+S.playlist))await command('/run_playlist',{playlist_name:S.playlist,run_mode:'single',pause_time:0,clear_pattern:'none',shuffle:false},'Sequence');return}if(a==='stop'){if(!connected()){message('No controller connected; stop motor power directly if movement is unsafe.',true);return}const r=await command('/stop_execution',{},'Stop');if(!r&&confirm('Normal stop failed. Request force stop?'))await command('/force_stop',{},'Force stop');return}if(a==='home-machine'){if(!connected()){message('Connect controller first.',true);return}if(!confirm('Run ORYN HOME routine? This physically moves motors. A manually centered ball is NOT the controller home reference. Verify clearances and be ready to cut power.'))return;await command('/send_home',{},'Home');return}if(a==='refresh-ports')return loadPortsAndCal();if(a==='connect-serial'){const port=document.getElementById('serial-select')?.value;if(!port){message('Choose the Raspberry Pi USB serial port.',true);return}await command('/connect',{port},'Serial connection');await refreshStatus();return}if(a==='disconnect-serial'){await command('/disconnect',{},'Serial disconnect');await refreshStatus();return}if(a==='refresh-status')return refreshStatus();if(a==='choose-playlist'){S.playlist=t.dataset.playlist;try{const seq=await api('/get_playlist?name='+encodeURIComponent(S.playlist));S.sequenceFiles=Array.isArray(seq.files)?seq.files:[]}catch(e){message('Could not open playlist: '+e.message,true)}return draw()}if(a==='reload-playlists')return loadPlaylists();if(a==='led-save'){const provider=document.getElementById('led-provider').value,ip=document.getElementById('led-ip').value.trim();if(provider==='dw_leds'){message('GPIO strip pin/count settings must be validated by your Pi installer before enabling. The current provider has been preserved.',true);return}const config={provider};if(provider==='magic_home')config.magic_home_ip=ip;if(provider==='wled')config.ip_address=ip;const r=await command('/set_led_config',config,'LED configuration');if(r)loadLed();return}if(a==='led-check'){try{const provider=S.led?.provider;S.ledStatus=await api(provider==='magic_home'?'/api/magic_home/status':provider==='dw_leds'?'/api/dw_leds/status':'/get_led_config');message(S.ledStatus.connected?'LED controller connected':S.led?.provider==='wled'?'WLED saved; check power from the configured controller':'LED status: '+(S.ledStatus.message||'Not connected'),!S.ledStatus.connected);draw()}catch(e){message(e.message,true)}return}if(a==='led-on'||a==='led-off'){const prov=S.led?.provider;if(!['magic_home','dw_leds'].includes(prov)){message('Direct power switching is supported here for Magic Home and ORYN GPIO. Select an applicable LED provider.',true);return}await command(prov==='magic_home'?'/api/magic_home/power':'/api/dw_leds/power',{state:a==='led-on'?1:0},'LED power');return}if(a==='led-apply'){const color=document.getElementById('led-color').value,brightness=Number(document.getElementById('led-brightness').value),prov=S.led?.provider;if(prov==='magic_home'){await command('/api/magic_home/color',{color,brightness},'RGB color');return}if(prov==='dw_leds'){const c=[1,3,5].map(i=>parseInt(color.slice(i,i+2),16));await command('/api/dw_leds/color',{color:c},'GPIO LED color');await command('/api/dw_leds/brightness',{value:brightness},'GPIO brightness');return}message('Color controls are available for configured Magic Home and ORYN GPIO devices. WLED uses its own lighting service.',true);return}}
catch(e){message('Action error: '+e.message,true)}}


document.body.addEventListener('click',dispatchAction);
document.body.addEventListener('change',async e=>{
 if(e.target.id==='serial-select'){S.selectedPort=e.target.value;return}
 if(e.target.id==='theta-step'){S.calStep=Number(e.target.value);return}
 if(e.target.id==='rho-step'){S.radialStep=Number(e.target.value);return}
 if(e.target.id!=='import-thr')return;
 const file=e.target.files?.[0];if(!file)return;
 if(!file.name.toLowerCase().endsWith('.thr')){message('Only THR patterns are accepted.',true);return}
 if(!confirm('Import '+file.name+' into the ORYN pattern library? This does not move motors.'))return;
 const form=new FormData();form.append('file',file);
 try{const response=await fetch('/upload_theta_rho',{method:'POST',body:form});if(!response.ok)throw Error('Upload HTTP '+response.status);await loadPatterns();message('Pattern imported: '+file.name)}catch(err){message('Import failed: '+err.message,true)}
});
window.addEventListener('hashchange',()=>{const p=location.hash.slice(1);if(names[p])selectPage(p)});
function connectWS(){const url=(location.protocol==='https:'?'wss://':'ws://')+location.host+'/ws/status';let sock;try{sock=new WebSocket(url)}catch{return}sock.onopen=()=>{S.online=true;draw()};sock.onmessage=e=>{try{const d=JSON.parse(e.data);if(d.type==='status_update')receiveLiveStatus(d.data)}catch(err){message('Live status update failed: '+err.message,true)}};sock.onclose=()=>{S.online=false;S.status=null;LIVE.animation=null;draw();setTimeout(connectWS,3000)};sock.onerror=()=>{S.online=false}}

(async()=>{draw();connectWS();await Promise.allSettled([loadPatterns(),api('/api/version').then(d=>S.version=d.current||d.version||'—'),loadLed(),api('/serial_status').then(d=>S.serial=d)]);if(S.page==='clean')await loadCoords(S.clean,true);if(S.page==='sequence')await loadPlaylists();if(S.page==='motion')await loadPortsAndCal();if(S.page==='system')await loadWifi(false);draw()})();
})();
