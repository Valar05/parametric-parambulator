const POSE={
  "version": 1,
  "source": "reliquary_duelist.svg",
  "forward": "-Y",
  "parts": [
    {
      "id": "left_boot",
      "asset": "boot",
      "x": -26.1,
      "y": 4,
      "rotation": 180,
      "scaleX": 1,
      "scaleY": 1
    },
    {
      "id": "torso",
      "asset": "torso",
      "x": -0.3,
      "y": 3.5,
      "rotation": 0,
      "scaleX": 1,
      "scaleY": 1
    },
    {
      "id": "cloth",
      "asset": "cloth",
      "x": 4.1,
      "y": 8.6,
      "rotation": 0,
      "scaleX": 1,
      "scaleY": 1
    },
    {
      "id": "left_upper",
      "asset": "upper",
      "x": -58,
      "y": 0,
      "rotation": 109,
      "scaleX": -1,
      "scaleY": 1
    },
    {
      "id": "right_upper",
      "asset": "upper",
      "x": 58,
      "y": 0,
      "rotation": -60,
      "scaleX": 1,
      "scaleY": 1
    },
    {
      "id": "left_forearm",
      "asset": "forearm",
      "x": -86.9,
      "y": -13.2,
      "rotation": 195,
      "scaleX": 1,
      "scaleY": 1
    },
    {
      "id": "right_forearm",
      "asset": "forearm",
      "x": 96.8,
      "y": 20.5,
      "rotation": 210,
      "scaleX": 1,
      "scaleY": 1
    },
    {
      "id": "left_hand",
      "asset": "open_hand",
      "x": -63.9,
      "y": -58.6,
      "rotation": 30,
      "scaleX": -0.85,
      "scaleY": 1
    },
    {
      "id": "sword",
      "asset": "sword",
      "x": 119.4,
      "y": -47.5,
      "rotation": -33,
      "scaleX": 1,
      "scaleY": 1
    },
    {
      "id": "right_hand",
      "asset": "fist",
      "x": 124.9,
      "y": -15.8,
      "rotation": 32,
      "scaleX": 1,
      "scaleY": 1
    },
    {
      "id": "right_boot",
      "asset": "boot",
      "x": 26.1,
      "y": 4,
      "rotation": 180,
      "scaleX": 1,
      "scaleY": 1
    },
    {
      "id": "left_shoulder",
      "asset": "shoulder",
      "x": -31,
      "y": 0,
      "rotation": 0,
      "scaleX": 1,
      "scaleY": 1
    },
    {
      "id": "right_shoulder",
      "asset": "shoulder",
      "x": 31,
      "y": 0,
      "rotation": 0,
      "scaleX": -1,
      "scaleY": 1
    },
    {
      "id": "helmet",
      "asset": "helmet",
      "x": 0,
      "y": -15,
      "rotation": 0,
      "scaleX": 1,
      "scaleY": 1
    }
  ]
};
const P=POSE.parts, ns='http://www.w3.org/2000/svg', el=id=>document.getElementById(id), rad=a=>a*Math.PI/180;
const rot=(x,y,a)=>[x*Math.cos(rad(a))-y*Math.sin(rad(a)),x*Math.sin(rad(a))+y*Math.cos(rad(a))];
function around(p,x,y,a){let v=rot(p.x-x,p.y-y,a);return {...p,x:x+v[0],y:y+v[1],rotation:p.rotation+a}}
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
function solve(twist,swing,reach=0){
 if(!twist&&!swing&&!reach)return P.map(p=>({...p})); const left=clamp(-swing/95,0,1), retract=35*left;
 return P.map(p=>{if(p.id.endsWith('boot'))return {...p};let q={...p};
 if(['left_shoulder','left_upper','left_forearm','left_hand'].includes(p.id))q=around(q,-31,0,retract);
 if(['right_upper','right_forearm','right_hand','sword'].includes(p.id)){
 q=around(q,58,0,swing); if(['right_forearm','right_hand','sword'].includes(p.id)){
 const pivot=around({x:96.8,y:20.5,rotation:0},58,0,swing);q=around(q,pivot.x,pivot.y,reach*65);}
 }return around(q,0,0,twist);});}
function gait(feet,root,face,move,dt){let speed=Math.hypot(...move);for(let f of feet){if(f.step){let s=f.step;s.t=Math.min(1,s.t+dt/.34);let k=s.t*s.t*(3-2*s.t);f.pos=s.from.map((v,i)=>v+(s.to[i]-v)*k);f.angle=s.angle0+(s.angle-s.angle0)*k;if(s.t===1)f.step=null;}}
 if(!feet.some(f=>f.step)){let options=feet.map(f=>{let v=rot(f.id==='left_boot'?-34:34,12,face),base=[root[0]+v[0],root[1]+v[1]],err=Math.hypot(base[0]-f.pos[0],base[1]-f.pos[1]);return {f,base,err}}).sort((a,b)=>b.err-a.err);let {f,base,err}=options[0];if(err>(speed>.05?38:13)){f.step={from:[...f.pos],to:[base[0]+move[0]*45,base[1]+move[1]*45],t:0,angle0:f.angle,angle:f.angle+((face-f.angle+540)%360)-180};}}}

const angle=(x,y)=>Math.atan2(x,-y)*180/Math.PI, delta=(a,b)=>((a-b+540)%360)-180;
const point=(p,x,y)=>{let v=rot(x,y,p.rotation);return [p.x+v[0],p.y+v[1]]};
// A fixed two-link arm with the accepted sprite origins as joint witnesses.
function blade(target){let a=angle(...target),twist=clamp(delta(a,68)*.24,-48,48), poses=solve(twist,clamp(delta(a,68),-120,120),0), get=id=>poses.find(p=>p.id===id);
 let S=rot(58,0,twist), d=[target[0]-S[0],target[1]-S[1]], L1=Math.hypot(38.8,20.5),L2=Math.hypot(28.1,-36.3), dist=clamp(Math.hypot(...d),Math.abs(L1-L2)+2,L1+L2-.2), A=Math.atan2(d[1],d[0]), B=Math.acos(clamp((L1*L1+dist*dist-L2*L2)/(2*L1*dist),-1,1)), E=[S[0]+L1*Math.cos(A+B),S[1]+L1*Math.sin(A+B)], H=[S[0]+dist*Math.cos(A),S[1]+dist*Math.sin(A)];
 let upper=get('right_upper'), fore=get('right_forearm'), hand=get('right_hand'), sword=get('sword');Object.assign(upper,{x:S[0],y:S[1],rotation:angle(E[0]-S[0],E[1]-S[1])-180});Object.assign(fore,{x:E[0],y:E[1],rotation:angle(H[0]-E[0],H[1]-E[1])-180});let orientation=a;Object.assign(hand,{x:H[0],y:H[1],rotation:orientation+65});let g=rot(0,-26,orientation);Object.assign(sword,{x:H[0]+g[0],y:H[1]+g[1],rotation:orientation});return {poses,hand:H,tip:point(sword,0,-204),angle:a};}
function mapPad(x,y,w,h,face){let scale=Math.min(w/2,h)/340;return rot((x-w*.75)/scale,(y-h*.5)/scale,-face)}
function observe(prev,next,dt,was){let vx=(next.hand[0]-prev.hand[0])/dt,vy=(next.hand[1]-prev.hand[1])/dt,tip=Math.hypot(next.tip[0]-prev.tip[0],next.tip[1]-prev.tip[1])/dt;let radial=(Math.hypot(...next.hand)-Math.hypot(...prev.hand))/dt,angular=delta(next.angle,prev.angle)/dt;let speed=Math.hypot(vx,vy);let state=speed>100||Math.abs(angular)>100?(radial< -65&&Math.abs(angular)<100?'windup':'attack'):was==='attack'&&tip>35?'recovery':'guard';return {state,speed,tip,radial,angular,potential:tip*tip/100000};}
if(typeof module==='object')module.exports={blade,mapPad,observe,gait,P};else{
let root=[0,0],face=0,move=[0,0],target=[124.9,-15.8],last=performance.now(),feet=P.filter(p=>p.id.endsWith('boot')).map(p=>({id:p.id,pos:[p.id==='left_boot'?-34:34,12],angle:0,step:null})),nodes={},active=new Map(),touch=null,prev=blade(target),state='guard';
for(let p of [...P.filter(p=>p.id.endsWith('boot')),...P.filter(p=>!p.id.endsWith('boot'))]){let n=document.createElementNS(ns,'use');n.setAttribute('href','#'+p.asset);el('actor').append(n);nodes[p.id]=n}
let stage=el('stage');stage.onpointerdown=e=>{let kind=e.clientX<innerWidth/2?'move':'attack';if([...active.values()].some(a=>a.kind===kind))return;stage.setPointerCapture(e.pointerId);active.set(e.pointerId,{x:e.clientX,y:e.clientY,kind});if(kind==='attack'){touch=[e.clientX,e.clientY];return}let ring=el('move');ring.style.display='block';ring.style.left=e.clientX+'px';ring.style.top=e.clientY+'px';};
stage.onpointermove=e=>{let a=active.get(e.pointerId);if(!a)return;if(a.kind==='attack'){touch=[e.clientX,e.clientY];return}let dx=e.clientX-a.x,dy=e.clientY-a.y,l=Math.max(65,Math.hypot(dx,dy));move=[dx/l,dy/l];el('move').firstElementChild.style.transform=`translate(${dx/l*42}px,${dy/l*42}px)`;};
function end(e){let a=active.get(e.pointerId);if(!a)return;active.delete(e.pointerId);if(a.kind==='move'){move=[0,0];el('move').style.display='none'}else{if(e.type==='pointerup')target=mapPad(e.clientX,e.clientY,innerWidth,innerHeight,face);touch=null;}}stage.onpointerup=end;stage.onpointercancel=end;stage.onlostpointercapture=end;
function tick(now){let dt=Math.max(.001,Math.min(.04,(now-last)/1000));last=now;if(Math.hypot(...move)>.04){root[0]+=move[0]*125*dt;root[1]+=move[1]*125*dt;face+=clamp(delta(angle(...move),face),-240*dt,240*dt)}if(touch)target=mapPad(...touch,innerWidth,innerHeight,face);let next=blade(target),obs=observe(prev,next,dt,state);state=obs.state;prev=next;el('telemetry').textContent=`${state} | tip ${Math.round(obs.tip)} u/s | energy proxy ${obs.potential.toFixed(2)}`;gait(feet,root,face,move,dt);for(let f of feet){let q=next.poses.find(q=>q.id===f.id),off=rot(f.pos[0]-root[0],f.pos[1]-root[1],-face);q.x=off[0];q.y=off[1];q.rotation=180+f.angle-face;}for(let p of next.poses)nodes[p.id].setAttribute('transform',`translate(${p.x} ${p.y}) rotate(${p.rotation}) scale(${p.scaleX} ${p.scaleY})`);el('actor').setAttribute('transform',`translate(${root[0]} ${root[1]}) rotate(${face})`);let H=620,W=H*innerWidth/innerHeight;stage.setAttribute('viewBox',`${root[0]-W/2} ${root[1]-H/2} ${W} ${H}`);requestAnimationFrame(tick)}requestAnimationFrame(tick)}
