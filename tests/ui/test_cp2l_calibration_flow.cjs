'use strict';
// Virtual DOM + fake controller backend: no USB, motors, networking, or browser hardware.
const fs=require('fs'),vm=require('vm'),assert=require('assert'),path=require('path');
const app=fs.readFileSync(path.join(__dirname,'../../static/dist/oryn-v2-live.js'),'utf8');
const state={theta:{active:false,calibrated:false,current_units:0,theta_revolution_units:70},rho:{active:false,calibrated:false,current_units:0,rho_travel_units:50.201},requests:[],rejectRho:false};
const root={innerHTML:'',setAttribute(){}};
let click=null,change=null;
const doc={body:{addEventListener(type,fn){if(type==='click')click=fn;else if(type==='change')change=fn}},getElementById(id){if(id==='oryn-root')return root;if(id==='theta-step')return {value:'0.5'};if(id==='rho-step')return {value:'0.2'};return null},querySelector(){return null}};
function reply(value,status=200){return {ok:status<400,status,async text(){return JSON.stringify(value)},async json(){return value}}}
async function fetch(url,opts={}){
 const route=String(url).split('?')[0],method=opts.method||'GET';
 const body=opts.body?JSON.parse(opts.body):{};
 state.requests.push([method,route,body]);
 const axis=route.startsWith('/api/rotation-calibration')?'theta':route.startsWith('/api/perimeter-calibration')?'rho':null;
 if(axis){
  const t=state[axis],verb=route.split('/').pop();
  if(method==='GET')return reply({...t});
  if(verb==='start'){
   if(axis==='rho'&&state.rejectRho)return reply({detail:'Radial teaching requires logical rho near 0. Establish and verify the true physical center'},409);
   t.active=true;t.current_units=0;return reply({success:true,active:true,current_units:0});
  }
  if(verb==='jog'){
   if(!t.active)return reply({detail:'Start teaching first'},409);
   t.current_units+=body.units;return reply({success:true,current_units:t.current_units});
  }
  if(verb==='save'){
   if(!t.active)return reply({detail:'Start teaching first'},409);
   t.active=false;t.calibrated=true;t[axis==='theta'?'theta_revolution_units':'rho_travel_units']=Math.abs(t.current_units);return reply({success:true});
  }
  if(verb==='reset'){t.active=false;t.calibrated=false;return reply({success:true});}
  if(verb==='cancel'){t.active=false;return reply({success:true});}
  if(verb==='set'){t.calibrated=true;return reply({success:true});}
 }
 const fixed={
  '/serial_status':{connected:true,port:'/dev/ttyUSB0',firmware_type:'grbl',firmware_version:'1.1h'},
  '/list_serial_ports':['/dev/ttyUSB0'],'/list_theta_rho_files_with_metadata':[],
  '/api/version':{current:'CP2L'},'/get_led_config':{provider:'none'}
 };
 return reply(fixed[route]??{});
}
const ctx={document:doc,location:{hash:'#motion',protocol:'http:',host:'localhost'},history:{replaceState(){}},window:{addEventListener(){}},WebSocket:class {constructor(){/* do not open */}},fetch,confirm:()=>true,console,URL,Image:class{},setTimeout:()=>0,clearTimeout:()=>{},performance:{now:()=>100},requestAnimationFrame:()=>0,FormData:class{},AbortController};
vm.runInNewContext(app,ctx,{filename:'oryn-v2-live.js'});
const spin=()=>new Promise(resolve=>setImmediate(resolve));
async function send(action,props={}){
  assert.ok(click,'click listener missing');
  const t={dataset:{action,...props}};
  await click({target:{closest(){return t}}});
}
async function test(){
 await spin();await spin();await spin();
 for(const [axis,step] of [['theta',.5],['rho',.2]]){
  await send('guide-step',{step:axis});
  assert(root.innerHTML.includes('data-action="cal-start-'+axis+'"'));
  assert(root.innerHTML.includes('TEACHING SESSION NOT ACTIVE'));
  assert(root.innerHTML.includes('data-action="cal-jog-plus-'+axis+'" disabled'));
  await send('cal-start-'+axis);
  assert(state[axis].active,'backend start not activated '+axis);
  assert(root.innerHTML.includes('TEACHING SESSION ACTIVE'),'UI not active after POST + GET for '+axis);
  assert(root.innerHTML.includes('data-action="cal-jog-plus-'+axis+'" '),'plus button absent');
  assert(!root.innerHTML.includes('data-action="cal-jog-plus-'+axis+'" disabled'),'plus still disabled');
  await send('cal-jog-plus-'+axis);
  assert(Math.abs(state[axis].current_units-step)<1e-6,'plus sign wrong: '+axis);
  await send('cal-jog-minus-'+axis);
  assert(Math.abs(state[axis].current_units)<1e-6,'minus sign wrong: '+axis);
  await send('cal-jog-plus-'+axis);
  await send('cal-save-'+axis);
  assert(state[axis].calibrated&&!state[axis].active,'save failed: '+axis);
  assert(root.innerHTML.includes('CALIBRATION SAVED'),'save confirmation not visible');
 }
 state.rejectRho=true;
 await send('guide-step',{step:'rho'});
 await send('cal-start-rho');
 assert(!state.rho.active,'rejected radial start activated');
 assert(root.innerHTML.includes('NOT STARTED / NOT COMPLETED'),'rejected start not shown in card');
 assert(root.innerHTML.includes('true physical center'),'real backend error not shown');
 assert(root.innerHTML.includes('data-action="cal-jog-plus-rho" disabled'),'jog not locked after rejection');
 const jogs=state.requests.filter(x=>x[1].endsWith('/jog')).map(x=>x[2].units);
 assert.deepStrictEqual(jogs,[.5,-.5,.5,.2,-.2,.2]);
 console.log('PASS: start → active UI → theta X+ / X− → save');
 console.log('PASS: start → active UI → rho Y+ / Y− → save');
 console.log('PASS: rejected radial start preserves jog lock and shows visible inline error');
 console.log('PASS: exact jog signs and all six mock request payloads',JSON.stringify(jogs));
}
test().catch(e=>{console.error(e);process.exit(1)});
