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
 if(!twist&&!swing&&!reach)return P.map(p=>({...p})); const left=clamp(-swing/95,0,1), retract=18*left;
 return P.map(p=>{if(p.id.endsWith('boot'))return {...p};let q={...p};
 if(['left_shoulder','left_upper','left_forearm','left_hand'].includes(p.id))q=around(q,-31,0,retract);
 if(['right_upper','right_forearm','right_hand','sword'].includes(p.id)){
 q=around(q,58,0,swing); if(['right_forearm','right_hand','sword'].includes(p.id)){
 const pivot=around({x:96.8,y:20.5,rotation:0},58,0,swing);q=around(q,pivot.x,pivot.y,reach*65);}
 }return around(q,0,0,twist);});}
const STEP_DURATION=.32, STEP_BONUS=3.5;
function burstStep(state,move,dt){const m=Math.hypot(...move);if(m<.12){state.armed=true;state.remaining=0;return {mult:1,start:false};}let start=false;if(state.armed&&m>=.25){state.armed=false;state.remaining=STEP_DURATION;start=true;}const t=state.remaining||0,end=Math.max(0,t-dt);state.remaining=end;return {mult:1+STEP_BONUS*(t*t*t-end*end*end)/(3*STEP_DURATION*STEP_DURATION*dt),start};}
function stance(f,root,face,engaged=true,lead='left_boot'){let left=f.id==='left_boot',front=f.id===lead,v=rot(engaged?(left?-28:34):(left?-34:34),engaged?(front?-32:36):12,face);return {pos:[root[0]+v[0],root[1]+v[1]],angle:face+(engaged?(front?0:left?-55:55):0)};}
// Continuous travel plus additive contact pulses; alternating swing in every direction.
function requestFlick(g,dx,dy,ms){let n=Math.hypot(dx,dy);if(n<18||ms>160||n/Math.max(ms,1)<.28||g.vector||g.flick)return false;g.flick=[dx/n,dy/n];return true;}
function vectorStep(g,feet,root,face,move,dt,engaged){
 const hip=f=>{let h=rot(f.id==='left_boot'?-24:24,8,face);return root.map((v,i)=>v+h[i]);};
 const safe=()=>{for(let f of feet){let h=hip(f),d=Math.hypot(f.pos[0]-h[0],f.pos[1]-h[1]);if(d>115){f.pos=h.map((v,i)=>v+(f.pos[i]-v)*110/d);f.step={t:.5};g.emergency=(g.emergency||0)+1;if(g.swing?.support===f){g.swing=null;g.lastSwing=feet.find(x=>x!==f).id;}}}};
 if(g.flick&&!g.vector){let dir=g.flick;g.flick=null;if(engaged){let local=rot(...dir,-face),dot=f=>f.pos[0]*dir[0]+f.pos[1]*dir[1];let f=[...feet].sort((a,b)=>dot(b)-dot(a))[0],support=feet.find(x=>x!==f);if(Math.abs(local[0])>Math.abs(local[1])){f=feet.find(x=>(x.id==='left_boot')===(local[0]<0));support=feet.find(x=>x!==f);}if(Math.abs(local[1])>=Math.abs(local[0]))g.lead=local[1]<0?f.id:support.id;g.swing=null;for(let x of feet)x.step=null;g.vector={dir,f,support,t:0,from:[...f.pos],angle:f.angle,sa:support.angle};}}
 if(!g.vector){let v=combatCycle(g,feet,root,face,move,dt,engaged);safe();return v;}
 let c=g.vector,before=[...root],a=c.t,b=Math.min(.24,a+dt),smooth=t=>{t=clamp(t,0,1);return t*t*(3-2*t)},advance=110*(smooth(b/.24)-smooth(a/.24));root[0]+=c.dir[0]*advance;root[1]+=c.dir[1]*advance;c.t=b;
 let h=hip(c.f),left=110*(1-smooth(b/.24)),dest=h.map((v,i)=>v+c.dir[i]*(left+25));let k=smooth(b/.19);c.f.pos=c.from.map((v,i)=>v+(dest[i]-v)*k);c.f.angle=c.angle+delta(stance(c.f,root,face,true,g.lead).angle,c.angle)*smooth(b/.075);c.f.step={t:b/.24};if(b>.12)c.support.angle+=clamp(delta(stance(c.support,root,face,true,g.lead).angle,c.support.angle),-420*dt,420*dt);safe();g.phase='VECTOR STEP';if(b>=.24){c.f.step=null;g.lastSwing=c.f.id;g.vector=null;}return root.map((v,i)=>(v-before[i])/dt);
}
function combatCycle(g,feet,root,face,move,dt,engaged){
 const before=[...root], mag=Math.min(1,Math.hypot(...move)), dir=mag?move.map(v=>v/Math.hypot(...move)):[0,0], moving=mag>.06;
 const smooth=t=>{t=clamp(t,0,1);return t*t*(3-2*t)}, hip=(f,r)=>{let v=rot(f.id==='left_boot'?-24:24,8,face);return r.map((x,i)=>x+v[i]);};
 g.lead??='left_boot';g.armed??=true;g.engaged=engaged;
 if(mag<.12)g.armed=true;
 g.pending=false;
 // Integrate the same velocity law for both root travel and future landing prediction.
 const base=engaged?125:400;
 const integral=(c,t)=>{let start=c.opening?.015:.085, width=c.opening?.075:.22, peak=c.opening?650:310;let x=clamp(t-start,0,width);return peak*(x/2-width*Math.sin(2*Math.PI*x/width)/(4*Math.PI));};
 const extraTravel=(c,a,b)=>engaged&&c.moving?integral(c,b)-integral(c,a):0;
 const target=(c,r,remaining)=>{let h=hip(c.f,r);let advance=mag*(base*remaining+extraTravel(c,c.elapsed,c.duration));let ahead=moving?(engaged?38:51):0;let local=rot(...dir,-face);let bias=engaged&&Math.abs(local[0])>Math.abs(local[1])?(c.f.id===g.lead?-15:15):0;let b=rot(0,bias,face);return h.map((v,i)=>v+b[i]+dir[i]*(advance+ahead));};
 let remaining=dt, maxExtra=0, openingFrame=false;
 while(remaining>1e-8){
  if(!g.swing){let local=rot(...dir,-face), lateral=Math.abs(local[0])>Math.abs(local[1]), opening=!!(g.pending&&engaged), f;
   if(moving){if(opening||!g.lastSwing)f=lateral?feet.find(f=>(f.id==='left_boot')===(local[0]<0)):feet.find(f=>(f.id===g.lead)===(local[1]<0));else f=feet.find(f=>f.id!==g.lastSwing);}
   else {let opts=feet.map(f=>({f,e:Math.hypot(...f.pos.map((v,i)=>v-stance(f,root,face,engaged,g.lead).pos[i]))})).sort((a,b)=>b.e-a.e);if(opts[0].e>8)f=opts[0].f;}
   if(!f)break;
   let support=feet.find(x=>x!==f);if(engaged&&moving&&!lateral)g.lead=local[1]<0?f.id:support.id;
   let c={f,support,from:[...f.pos],angle:f.angle,t:0,elapsed:0,duration:opening?.38:engaged?.34:moving?.255:.34,opening,moving};c.to=moving?target(c,root,c.duration):stance(f,root,face,engaged,g.lead).pos;g.swing=c;g.lastSwing=f.id;if(opening)g.pending=false;
  }
  let c=g.swing,h=Math.min(remaining,c.duration-c.elapsed),end=c.elapsed+h,extra=extraTravel(c,c.elapsed,end);openingFrame||=c.opening;maxExtra=Math.max(maxExtra,extra/h);
  // Never brake the body to repair a landing. Predict the landing from the actual integrated root path.
  let advance=mag*(base*h+extra);root[0]+=dir[0]*advance;root[1]+=dir[1]*advance;c.elapsed=end;c.t=end/c.duration;
  let desired=moving?target(c,root,c.duration-end):stance(c.f,root,face,engaged,g.lead).pos;
  // Replan on changing input/heading, but maintain a continuous swing trajectory.
  c.to=desired;let k=smooth(c.t);c.f.pos=c.from.map((v,i)=>v+(c.to[i]-v)*k);
  let a=stance(c.f,root,face,engaged,g.lead).angle;c.f.angle=c.angle+delta(a,c.angle)*smooth(c.t/.30);c.f.step={t:c.t};
  let sa=stance(c.support,root,face,engaged,g.lead).angle;if(c.t>.45)c.support.angle+=clamp(delta(sa,c.support.angle),-420*h,420*h);
  remaining-=h;if(c.t>=1-1e-9){c.f.step=null;g.swing=null;}
 }
 g.phase=openingFrame?'COMBAT STEP':maxExtra>20?'DRIVE':moving?'TRAVEL':'GUARD';return root.map((v,i)=>(v-before[i])/dt);
}
function gait(feet,root,face,move,dt,event={},g={lead:'left_boot',engaged:true}){let speed=Math.hypot(...move),local=rot(...move,-face),engaged=g.engaged!==false;g.lead??='left_boot';let launch=(f,to,duration)=>{let target=stance(f,root,face,engaged,g.lead);f.step={from:[...f.pos],to,t:0,duration,angle0:f.angle,angle:f.angle+delta(target.angle,f.angle)};};
 for(let f of feet){if(f.step){let s=f.step;s.t=Math.min(1,s.t+dt/s.duration);let k=s.t*s.t*(3-2*s.t);f.pos=s.from.map((v,i)=>v+(s.to[i]-v)*k);f.angle=s.angle0+(s.angle-s.angle0)*k;if(s.t===1)f.step=null;}}
 if(!feet.some(f=>f.step)){let options=feet.map(f=>{let base=stance(f,root,face,engaged,g.lead),err=Math.hypot(base.pos[0]-f.pos[0],base.pos[1]-f.pos[1]);return {f,base,err}}).sort((a,b)=>b.err-a.err);let f=options[0].f;let passing=engaged&&speed>.25&&Math.abs(local[1])>Math.abs(local[0])&&options[0].err>30;
 if(event.start){let left=Math.abs(local[1])>=Math.abs(local[0])?(local[1]<0?g.lead==='left_boot':g.lead!=='left_boot'):local[0]<0;f=feet.find(f=>(f.id==='left_boot')===left);}
 else if(passing){f=feet.find(f=>(f.id===g.lead)===(local[1]>0));g.lead=feet.find(x=>x!==f).id;if(local[1]<0)g.lead=f.id;g.pulse=.18;}
 let base=stance(f,root,face,engaged,g.lead),err=Math.hypot(base.pos[0]-f.pos[0],base.pos[1]-f.pos[1]);if(event.start||passing||err>(speed>.05?38:4)||Math.abs(delta(base.angle,f.angle))>5){let dir=move.map(v=>v/Math.max(speed,.001));launch(f,base.pos.map((v,i)=>v+dir[i]*(speed>.05?(event.start?65:passing?35:45):0)),event.start?.19:passing?.22:.34);event.support=feet.find(x=>x!==f).id;}}
 for(let f of feet)if(!f.step){let a=stance(f,root,face,engaged,g.lead).angle;f.angle+=clamp(delta(a,f.angle),-300*dt,300*dt);}}
const angle=(x,y)=>Math.atan2(x,-y)*180/Math.PI, delta=(a,b)=>(((a-b+180)%360+360)%360)-180;
const point=(p,x,y)=>{let v=rot(x,y,p.rotation);return [p.x+v[0],p.y+v[1]]};
// A fixed two-link arm with the accepted sprite origins as joint witnesses.
// Tip-first bounded search over wrist orientation and torso twist.
function blade(target, preferred, previous, lock=false){
 const L1=Math.hypot(38.8,20.5),L2=Math.hypot(28.1,-36.3), R=230;
 const radial=angle(...target), want=preferred??radial, prior=previous?.angle??want;
 let best=null;
 function candidate(a,t,branch){
  a=delta(a,0);if(a < -145 || a > 165)return;
  const S=rot(58,0,t), off=rot(0,-R,a), desired=[target[0]-off[0],target[1]-off[1]], d=[desired[0]-S[0],desired[1]-S[1]], len=Math.hypot(...d), dist=clamp(len,38,L1+L2-.2), A=len>.00001?Math.atan2(d[1],d[0]):0, B=Math.acos(clamp((L1*L1+dist*dist-L2*L2)/(2*L1*dist),-1,1)), E=[S[0]+L1*Math.cos(A+branch*B),S[1]+L1*Math.sin(A+branch*B)], H=[S[0]+dist*Math.cos(A),S[1]+dist*Math.sin(A)], tip=[H[0]+off[0],H[1]+off[1]];
  const wrist=delta(a,angle(H[0]-E[0],H[1]-E[1])); if(Math.abs(wrist)>65)return;
  const upperAngle=delta(angle(E[0]-S[0],E[1]-S[1]),t); if(upperAngle < -25 || upperAngle > 155 || H[0]*H[0]+H[1]*H[1]<42*42)return;
  const error=Math.hypot(tip[0]-target[0],tip[1]-target[1]);
  const cost=error*error+ (lock==='thrust'?12:lock?.18:.025)*delta(a,want)**2+.018*delta(a,prior)**2+.08*(t-clamp(delta(radial,68)*.15,-30,30))**2+(previous&&branch!==previous.branch?180:0)+(previous?.elbow ? .8*((E[0]-previous.elbow[0])**2+(E[1]-previous.elbow[1])**2)+.4*((H[0]-previous.hand[0])**2+(H[1]-previous.hand[1])**2):0);
  if(!best||cost<best.cost)best={a,t,branch,S,E,H,tip,error,cost,wrist};
 }
 if(previous)candidate(previous.angle,previous.twist,1);
 for(let a=-180;a<180;a+=6)for(let t=-30;t<=30;t+=6)for(let branch of [1])candidate(a,t,branch);
 if(!best){ if(previous)return {...previous,error:Math.hypot(previous.tip[0]-target[0],previous.tip[1]-target[1])}; return blade([0,-270],0); }
 const coarse=best;for(let a=coarse.a-6;a<=coarse.a+6;a+=1)for(let t=Math.max(-30,coarse.t-6);t<=Math.min(30,coarse.t+6);t+=3)candidate(a,t,coarse.branch);
 const {a,t,branch,S,E,H,tip,error,wrist}=best,poses=solve(t,clamp(delta(a,68),-120,120),0),get=id=>poses.find(p=>p.id===id);
 Object.assign(get('right_upper'),{x:S[0],y:S[1],rotation:angle(E[0]-S[0],E[1]-S[1])-180});Object.assign(get('right_forearm'),{x:E[0],y:E[1],rotation:angle(H[0]-E[0],H[1]-E[1])-180});Object.assign(get('right_hand'),{x:H[0],y:H[1],rotation:a+65});let g=rot(0,-26,a);Object.assign(get('sword'),{x:H[0]+g[0],y:H[1]+g[1],rotation:a});return {poses,hand:H,tip,angle:a,branch,error,wrist,elbow:E,shoulder:S,twist:t};
}
// Empirical initial envelope; the unchanged IK still enforces anatomy.
const envelope=(()=>{const bins=Array.from({length:360},()=>[]), L1=Math.hypot(38.8,20.5),L2=Math.hypot(28.1,-36.3);
for(let t=-30;t<=30;t+=6)for(let u=-25;u<=155;u+=5)for(let bend=5;bend<=130;bend+=5){const S=rot(58,0,t),v=rot(0,-L1,t+u),E=[S[0]+v[0],S[1]+v[1]],f=t+u-bend,z=rot(0,-L2,f),H=[E[0]+z[0],E[1]+z[1]];if(Math.hypot(...H)<42||Math.hypot(H[0]-S[0],H[1]-S[1])<38)continue;for(let wrist=-65;wrist<=65;wrist+=5){let a=f+wrist,off=rot(0,-230,a),tip=[H[0]+off[0],H[1]+off[1]],i=(Math.round(angle(...tip))+360)%360;bins[i].push(Math.hypot(...tip));}}
return bins.map(b=>b.length?[Math.min(...b),Math.max(...b)]:null);})();
function limitedAngle(raw,track){let a=delta(raw,0);if(track.limit===undefined)track.limit=clamp(a,-115,155);else track.limit=clamp(track.limit+delta(a,track.lastRaw),-115,155);track.lastRaw=a;return track.limit;}
function legGeometry(hip,foot,side,lift=0){let dx=foot[0]-hip[0],dy=foot[1]-hip[1],d=Math.hypot(dx,dy),bias=Math.min(10,d*.12)*(1+lift*.5);let knee=[hip[0]+dx*.53+side*bias,hip[1]+dy*.53];return [hip,knee,foot];}
function mapPad(x,y,w,h,face,track={}){let scale=Math.min(w/4,h/2)*.65,u=(x-w*.75)/scale,v=(y-h*.5)/scale,r=Math.hypot(u,v);if(r>.045)track.raw=angle(u,v);let a=limitedAngle((track.raw??face)-face,track),i=(Math.round(a)%360+360)%360;let k=i;if(!envelope[k]){for(let d=1;d<=180;d++){if(envelope[(i+d)%360]){k=(i+d)%360;break}if(envelope[(i-d+360)%360]){k=(i-d+360)%360;break}}}let f=Math.floor(a), frac=a-f, left=envelope[(f%360+360)%360], right=envelope[((f+1)%360+360)%360]; let [lo,hi]=left&&right?left.map((v,i)=>v+(right[i]-v)*frac):envelope[k],q=clamp((r-.045)/.955,0,1),reach=lo+(hi-lo)*q;return rot(0,-reach,left&&right?a:k);}
function orientationMemory(d, radial, prior, memory){
 const n=Math.hypot(...d); if(n<1)return memory.heading??prior;
 const axis=rot(0,-1,memory.lock??prior), along=d[0]*axis[0]+d[1]*axis[1], across=d[0]*(-axis[1])+d[1]*axis[0];
 if(Math.abs(across)<=Math.abs(along)*(memory.lock!==undefined?.55:.25) && (along<0||memory.lock!==undefined)){
  memory.lock=memory.lock??prior; memory.heading=memory.lock; return memory.heading;
 }
 delete memory.lock;
 const tangent=angle(...d), alignment=Math.cos(rad(delta(tangent,radial)));
 memory.heading=alignment>.65?tangent:radial; return memory.heading;
}
function coherentBlade(target, preferred, previous, lock, cache){
 const unchanged=cache.target&&Math.hypot(target[0]-cache.target[0],target[1]-cache.target[1])<.75&&Math.abs(delta(preferred,cache.preferred))<1&&lock===cache.lock;
 if(unchanged)return previous;
 const next=blade(target,preferred,previous,lock);
 cache.target=[...target];cache.preferred=preferred;cache.lock=lock;
 return next;
}
function articulation(goal, previous, dt){
 const L1=Math.hypot(38.8,20.5), L2=Math.hypot(28.1,-36.3);
 const joints=p=>[p.twist,delta(angle(p.elbow[0]-p.shoulder[0],p.elbow[1]-p.shoulder[1]),p.twist),delta(angle(p.hand[0]-p.elbow[0],p.hand[1]-p.elbow[1]),angle(p.elbow[0]-p.shoulder[0],p.elbow[1]-p.shoulder[1])),p.wrist];
 const old=joints(previous), want=joints(goal), rates=[240,720,900,1080];
 const [t,u,b,w]=old.map((v,i)=>v+clamp(delta(want[i],v),-rates[i]*dt,rates[i]*dt));
 const a=t+u+b+w;if(delta(a,0)<-145||delta(a,0)>165)return previous;const S=rot(58,0,t),v=rot(0,-L1,t+u),E=[S[0]+v[0],S[1]+v[1]],z=rot(0,-L2,t+u+b),H=[E[0]+z[0],E[1]+z[1]],off=rot(0,-230,a),tip=[H[0]+off[0],H[1]+off[1]];
 if(Math.hypot(...H)<42||Math.hypot(H[0]-S[0],H[1]-S[1])<38)return previous;
 const poses=solve(t,clamp(delta(a,68),-120,120),0),get=id=>poses.find(p=>p.id===id);
 Object.assign(get('right_upper'),{x:S[0],y:S[1],rotation:t+u-180});Object.assign(get('right_forearm'),{x:E[0],y:E[1],rotation:t+u+b-180});Object.assign(get('right_hand'),{x:H[0],y:H[1],rotation:a+65});const g=rot(0,-26,a);Object.assign(get('sword'),{x:H[0]+g[0],y:H[1]+g[1],rotation:a});return {poses,hand:H,tip,angle:a,branch:1,error:goal.error,wrist:w,elbow:E,shoulder:S,twist:t};
}
function gestureDelta(touch,lastTouch,w,h,face){if(!lastTouch)return [0,0];return rot((touch[0]-lastTouch[0])*2,(touch[1]-lastTouch[1])*2,-face);}
function observe(prev,next,dt,was){let vx=(next.hand[0]-prev.hand[0])/dt,vy=(next.hand[1]-prev.hand[1])/dt,tip=Math.hypot(next.tip[0]-prev.tip[0],next.tip[1]-prev.tip[1])/dt;let radial=(Math.hypot(...next.hand)-Math.hypot(...prev.hand))/dt,angular=delta(next.angle,prev.angle)/dt;let speed=Math.hypot(vx,vy);let state=speed>100||Math.abs(angular)>100?(radial< -65&&Math.abs(angular)<100?'windup':'attack'):was==='attack'&&tip>35?'recovery':'guard';return {state,speed,tip,radial,angular,potential:tip*tip/100000};}
function thrustGesture(dx,dy,face){let [x,y]=rot(dx,dy,-face);return -y>=18&&Math.abs(x)<=-y*.42;}
const guardTargets=[[-235,-55],[0,-255],[285,-125]];
function restingGuard(p){return guardTargets.reduce((a,b)=>Math.hypot(a[0]-p[0],a[1]-p[1])<=Math.hypot(b[0]-p[0],b[1]-p[1])?a:b).slice();}
function thrustTarget(dx,dy,face){let [x,y]=rot(dx,dy,-face),a=clamp(angle(x,y),-18,18),r=265+clamp((-y-18)/65,0,1)*55;return {target:rot(0,-r,a),preferred:a};}
function handGoal(a,depth){
 const L1=Math.hypot(38.8,20.5),L2=Math.hypot(28.1,-36.3),t=0,S=[58,0],H=rot(48,-depth,a),d=[H[0]-S[0],H[1]-S[1]],len=Math.hypot(...d),A=Math.atan2(d[1],d[0]),B=Math.acos(clamp((L1*L1+len*len-L2*L2)/(2*L1*len),-1,1)),E=[S[0]+L1*Math.cos(A+B),S[1]+L1*Math.sin(A+B)],wrist=delta(a,angle(H[0]-E[0],H[1]-E[1])),u=angle(E[0]-S[0],E[1]-S[1]);
 if(len> L1+L2-.2||len<38||Math.abs(wrist)>65||u< -25||u>155) return null;
 const poses=solve(t,clamp(delta(a,68),-120,120),0),get=id=>poses.find(p=>p.id===id),g=rot(0,-26,a),off=rot(0,-230,a);
 Object.assign(get('right_upper'),{x:S[0],y:S[1],rotation:u-180});Object.assign(get('right_forearm'),{x:E[0],y:E[1],rotation:angle(H[0]-E[0],H[1]-E[1])-180});Object.assign(get('right_hand'),{x:H[0],y:H[1],rotation:a+65});Object.assign(get('sword'),{x:H[0]+g[0],y:H[1]+g[1],rotation:a});return {poses,hand:H,tip:[H[0]+off[0],H[1]+off[1]],angle:a,branch:1,error:0,wrist,elbow:E,shoulder:S,twist:t};
}
function startThrust(){return {phase:'gather',elapsed:0};}
function thrustFrame(c,prev,dt){
 const gather=handGoal(0,50),extend=handGoal(0,85);if(!gather||!extend)throw Error('thrust geometry');
 c.elapsed+=dt;let goal=gather;
 if(c.phase==='gather'){let next=articulation(gather,prev,dt);if(Math.hypot(next.hand[0]-gather.hand[0],next.hand[1]-gather.hand[1])<2&&Math.abs(delta(next.angle,0))<3){c.phase='extend';c.elapsed=0;}return next;}
 if(c.phase==='extend'){let k=clamp(c.elapsed/.10,0,1);goal=handGoal(0,50+35*k);if(k===1){c.phase='recover';c.elapsed=0;}return goal;}
 let k=clamp(c.elapsed/.24,0,1);goal=handGoal(0,85-35*k*k*(3-2*k));if(k===1)c.done=true;return goal;
}
function repose(r,dt){r.elapsed+=dt;let k=clamp((r.elapsed-2)/1.5,0,1);k=k*k*(3-2*k);return r.from.map((v,i)=>v+(r.to[i]-v)*k);}
if(typeof module==='object')module.exports={handGoal,startThrust,thrustFrame,repose,thrustGesture,restingGuard,thrustTarget,requestFlick,vectorStep,combatCycle,burstStep,stance,blade,mapPad,orientationMemory,coherentBlade,articulation,gestureDelta,observe,gait,P,envelope,limitedAngle,legGeometry};else{
let root=[0,0],face=0,move=[0,0],target=[0,-270],last=performance.now(),feet=P.filter(p=>p.id.endsWith('boot')).map(p=>({id:p.id,pos:stance(p,[0,0],0).pos,angle:stance(p,[0,0],0).angle,step:null})),nodes={},active=new Map(),touch=null,prev=blade(target),state='guard',preferred=0,padTrack={},memory={},lastTarget=[...target],lastTouch=null,coherence={},idlePeak=0,idleJoint=0,stepBurst={armed:true,remaining:0}, gaitState={lead:"left_boot",engaged:true,pulse:0};
for(let p of [...P.filter(p=>p.id.endsWith('boot')),...P.filter(p=>!p.id.endsWith('boot'))]){let n=document.createElementNS(ns,'use');n.setAttribute('href','#'+p.asset);el('actor').append(n);nodes[p.id]=n}
const legNodes={};for(const side of [-1,1]){let g=document.createElementNS(ns,'g');for(const part of ['cuisses','greaves','poleyn']){let n=document.createElementNS(ns,'use');n.setAttribute('href','#leg-'+part);g.append(n);}el('actor').insertBefore(g,el('actor').firstChild);legNodes[side]=g;}
function renderLeg(f,off){let side=f.id==='left_boot'?-1:1,hip=[side*24,8],lift=f.step?Math.sin(Math.PI*f.step.t):0;let [a,k,z]=legGeometry(hip,off,side,lift),g=legNodes[side];function segment(n,p,q,len){let d=Math.hypot(q[0]-p[0],q[1]-p[1]);n.setAttribute('transform',`translate(${p[0]} ${p[1]}) rotate(${angle(q[0]-p[0],q[1]-p[1])-180}) scale(1 ${Math.max(.12,d/len)})`);}segment(g.children[0],a,k,46);segment(g.children[1],k,z,46);g.children[2].setAttribute('transform',`translate(${k[0]} ${k[1]}) rotate(${angle(z[0]-a[0],z[1]-a[1])-180})`);}
let attackIntent=null, settle=null, thrust=null;let stage=el('stage');function marker(p){let n=el('finger');n.style.display=p?'block':'none';if(p){n.style.left=p[0]+'px';n.style.top=p[1]+'px';}}const targets=[{id:'dummy',pos:[0,-390]}], selection={hard:null,last:null};let soft=null;
function hit(e){const p=new DOMPoint(e.clientX,e.clientY).matrixTransform(stage.getScreenCTM().inverse());return targets.find(t=>Targeting.dist(t.pos,[p.x,p.y])<=105)?.id||null;}
function beginAttack(e,a){a.kind='attack';attackIntent={x:a.x,y:a.y,mode:null};settle=null;thrust=null;touch=[e.clientX,e.clientY];lastTouch=null;padTrack={};memory={};coherence={};preferred=prev.angle;marker(touch);}
function beginMove(a){a.kind='move';let ring=el('move');ring.style.display='block';ring.style.left=a.x+'px';ring.style.top=a.y+'px';}
stage.onpointerdown=e=>{let side=e.clientX<innerWidth/2?'move':'attack';if([...active.values()].some(a=>a.side===side))return;if(side==='attack'){settle=null;}stage.setPointerCapture(e.pointerId);active.set(e.pointerId,{x:e.clientX,y:e.clientY,side,kind:'pending',time:performance.now(),enemy:hit(e)});};
stage.onpointermove=e=>{let a=active.get(e.pointerId);if(!a)return;let dx=e.clientX-a.x,dy=e.clientY-a.y;if(a.kind==='pending'){if(Math.hypot(dx,dy)<10)return;selection.last=null;if(a.side==='attack')beginAttack(e,a);else beginMove(a);}if(a.kind==='attack'){touch=[e.clientX,e.clientY];if(attackIntent?.mode===null&&Math.hypot(dx,dy)>=18){attackIntent.mode=thrustGesture(dx,dy,face)?'thrust':'direct';if(attackIntent.mode==='thrust')thrust=startThrust();}marker(touch);return;}if(!a.flicked&&requestFlick(gaitState,dx,dy,performance.now()-a.time))a.flicked=true;let l=Math.max(65,Math.hypot(dx,dy));move=[dx/l,dy/l];el('move').firstElementChild.style.transform=`translate(${dx/l*42}px,${dy/l*42}px)`;};
function end(e){let a=active.get(e.pointerId);if(!a)return;active.delete(e.pointerId);if(a.kind==='move'){move=[0,0];el('move').style.display='none';}else if(a.kind==='attack'){if(e.type==='pointerup'&&attackIntent?.mode!=='thrust')target=mapPad(e.clientX,e.clientY,innerWidth,innerHeight,face,padTrack);touch=null;attackIntent=null;settle={elapsed:0,from:[...target],to:restingGuard(prev.tip)};memory={};marker(null);}else if(e.type==='pointerup'&&performance.now()-a.time<350&&Math.hypot(e.clientX-a.x,e.clientY-a.y)<10){let result=Targeting.tap(selection,hit(e)||a.enemy,[e.clientX,e.clientY],performance.now());if(result==='weapon'&&a.side==='attack')target=mapPad(e.clientX,e.clientY,innerWidth,innerHeight,face,{});}}stage.onpointerup=end;stage.onpointercancel=end;stage.onlostpointercapture=end;
function tick(now){let real=Math.max(.001,Math.min(.04,(now-last)/1000));last=now;let dt=Juice.frame(real);if(dt===0){requestAnimationFrame(tick);return;}let burst=burstStep(stepBurst,move,dt);let hard=targets.find(t=>t.id===selection.hard);if(hard&&Targeting.dist(root,hard.pos)>900){selection.hard=null;hard=null;}soft=Targeting.pick(root,targets,soft?.id);let focus=hard||soft;let velocity=vectorStep(gaitState,feet,root,face,move,dt,!!focus);let heading=focus?angle(focus.pos[0]-root[0],focus.pos[1]-root[1]):Math.hypot(...move)>.04?angle(...move):face;face+=clamp(delta(heading,face),-240*dt,240*dt);let ring=el('target-ring');ring.setAttribute('visibility',focus?'visible':'hidden');ring.setAttribute('stroke',hard?'#e9ba62':'#a7aeb8');ring.setAttribute('stroke-dasharray',hard?'none':'9 8');el('lock-state').textContent=hard?'HARD LOCK':soft?'SOFT TARGET':'FREE';if(touch){target=mapPad(...touch,innerWidth,innerHeight,face,padTrack);if(lastTouch){let d=gestureDelta(touch,lastTouch,innerWidth,innerHeight,face);if(Math.hypot(...d)>1){preferred=orientationMemory(d,angle(...target),prev.angle,memory);}}lastTouch=[...touch];lastTarget=[...target];}else if(settle&&!thrust){if(settle.elapsed+real>2){target=repose(settle,real);preferred=angle(...target);}else settle.elapsed+=real;}let stationary=coherence.target&&Math.hypot(target[0]-coherence.target[0],target[1]-coherence.target[1])<.75;let goal=coherentBlade(target,preferred,coherence.goal??prev,attackIntent?.mode==='thrust'?'thrust':memory.lock!==undefined,coherence);coherence.goal=goal;let next=thrust?thrustFrame(thrust,prev,dt):articulation(goal,prev,dt);if(thrust){target=[...next.tip];preferred=next.angle;if(thrust.done){thrust=null;coherence={};if(!touch)settle={elapsed:0,from:[...target],to:restingGuard(target)};}}next.error=Math.hypot(next.tip[0]-target[0],next.tip[1]-target[1]);let obs=observe(prev,next,dt,state);if(stationary){idlePeak=Math.max(idlePeak,Math.abs(delta(next.angle,prev.angle)));idleJoint=Math.max(idleJoint,Math.hypot(next.elbow[0]-prev.elbow[0],next.elbow[1]-prev.elbow[1]));}state=obs.state;prev=next;el('telemetry').textContent=`${focus?"COMBAT":"TRAVERSE"} ${gaitState.phase} ${Math.round(Math.hypot(...velocity))} u/s | ${state} | tip ${Math.round(obs.tip)} u/s | energy proxy ${obs.potential.toFixed(2)} | tip error ${next.error.toFixed(1)} | idle peak ${idlePeak.toFixed(1)}° / ${idleJoint.toFixed(1)}u`;for(let f of feet){let q=next.poses.find(q=>q.id===f.id),off=rot(f.pos[0]-root[0],f.pos[1]-root[1],-face);renderLeg(f,off);q.x=off[0];q.y=off[1];q.rotation=180+f.angle-face;}for(let p of next.poses)nodes[p.id].setAttribute('transform',`translate(${p.x} ${p.y}) rotate(${p.rotation}) scale(${p.scaleX} ${p.scaleY})`);el('actor').setAttribute('transform',`translate(${root[0]} ${root[1]}) rotate(${face})`);for(let [id,p] of [['wanted',target],['actual',next.tip]]){let v=rot(...p,face),n=el(id);n.setAttribute('cx',root[0]+v[0]);n.setAttribute('cy',root[1]+v[1]);}window.trainingFrame(next,root,face,dt);let H=1000,W=H*innerWidth/innerHeight;stage.setAttribute('viewBox',`${root[0]-W/2} ${root[1]-H/2} ${W} ${H}`);requestAnimationFrame(tick)}requestAnimationFrame(tick)}
