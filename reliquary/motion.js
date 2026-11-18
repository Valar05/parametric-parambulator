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
function solve(twist,swing){return P.map(p=>{if(p.id.endsWith('boot'))return {...p};let q=around(p,0,0,twist);if(['right_upper','right_forearm','right_hand','sword'].includes(p.id))q=around(q,...rot(58,0,twist),swing);return q})}
if(typeof module==='object'){module.exports={solve,P,rot};}else{
let root=[0,0],face=0,move=[0,0],twist=0,swing=0,target=0,last=performance.now(),feet=P.filter(p=>p.id.endsWith('boot')).map(p=>({id:p.id,pos:[p.x,p.y],angle:0,step:null})),turn=0, nodes={};
for(let p of P){let n=document.createElementNS(ns,'use');n.setAttribute('href','#'+p.asset);el('actor').append(n);nodes[p.id]=n}
let active=new Map();for(let [id,kind] of [['move','move'],['attack','attack']]){let e=el(id);e.onpointerdown=v=>{e.setPointerCapture(v.pointerId);active.set(v.pointerId,{x:v.clientX,y:v.clientY,kind});};e.onpointermove=v=>{let a=active.get(v.pointerId);if(!a)return;let dx=v.clientX-a.x,dy=v.clientY-a.y;if(kind==='move'){let l=Math.max(40,Math.hypot(dx,dy));move=[dx/l,dy/l]}else target=Math.max(-95,Math.min(95,dx*1.5));};let end=v=>{active.delete(v.pointerId);if(kind==='move')move=[0,0];else target=0};e.onpointerup=end;e.onpointercancel=end;}
function tick(now){let dt=Math.min(.04,(now-last)/1000);last=now;let speed=Math.hypot(...move);if(speed>.08){root[0]+=move[0]*95*dt;root[1]+=move[1]*95*dt;let a=Math.atan2(move[0],-move[1])*180/Math.PI;face+=Math.max(-240*dt,Math.min(240*dt,((a-face+540)%360)-180))}swing+=(target-swing)*Math.min(1,dt*9);twist+=(swing*.24-twist)*Math.min(1,dt*7);
let poses=solve(twist,swing);for(let f of feet){let p=P.find(p=>p.id===f.id),v=rot(p.x,p.y,face),goal=[root[0]+v[0]+move[0]*22,root[1]+v[1]+move[1]*22];if(!f.step&&!feet.some(k=>k.step)&&Math.hypot(goal[0]-f.pos[0],goal[1]-f.pos[1])>26){f.step={from:[...f.pos],to:goal,t:0,angle:face};}if(f.step){let s=f.step;s.t=Math.min(1,s.t+dt*5);let k=s.t*s.t*(3-2*s.t);f.pos=s.from.map((v,i)=>v+(s.to[i]-v)*k);if(s.t===1){f.angle=s.angle;f.step=null}}let q=poses.find(q=>q.id===f.id),off=rot(f.pos[0]-root[0],f.pos[1]-root[1],-face);q.x=off[0];q.y=off[1];q.rotation=p.rotation+f.angle-face;}
for(let p of poses)nodes[p.id].setAttribute('transform',`translate(${p.x} ${p.y}) rotate(${p.rotation}) scale(${p.scaleX} ${p.scaleY})`);el('actor').setAttribute('transform',`translate(${root[0]} ${root[1]}) rotate(${face})`);el('stage').setAttribute('viewBox',`${root[0]-250} ${root[1]-250} 500 500`);requestAnimationFrame(tick)}requestAnimationFrame(tick)}