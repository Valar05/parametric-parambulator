/* Hareworks left STEP v0.2.7. Reconstruct original Cautious_Crouch_Walk_Left_inplace
   as an independent 74-joint continuous mathematical curve. The traveling
   Cautious_Crouch_Walk_Left is diagnostic only. No slide_right anywhere. */
export const ROOT='mixamorigHips';
export const CLIPS=['Cautious_Crouch_Walk_Left','Cautious_Crouch_Walk_Left_inplace'];
export const mod1=v=>((v%1)+1)%1;
const finite=(a,n)=>Array.isArray(a)&&a.length===n&&a.every(Number.isFinite);
function norm(a){if(!finite(a,4))throw Error('INVALID_QUAT');const l=Math.hypot(...a);if(l<1e-12)throw Error('ZERO_QUAT');return a.map(x=>x/l)}
export function qm(a,b){const [x,y,z,w]=a,[X,Y,Z,W]=b;return [w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z]}
export const qc=a=>[-a[0],-a[1],-a[2],a[3]];
export function angleDeg(a,b){const x=norm(a),y=norm(b);const d=Math.min(1,Math.abs(x.reduce((s,v,i)=>s+v*y[i],0)));return 2*Math.acos(d)*180/Math.PI}
function slerp(A,B,t){const a=norm(A);let b=norm(B);let dot=a.reduce((s,v,i)=>s+v*b[i],0);if(dot<0){b=b.map(x=>-x);dot=-dot}if(dot>.9995)return norm(a.map((v,i)=>v*(1-t)+t*b[i]));const theta=Math.acos(Math.min(1,dot)),sin=Math.sin(theta);return norm(a.map((v,i)=>(Math.sin((1-t)*theta)*v+Math.sin(t*theta)*b[i])/sin))}
const lerp=(a,b,u)=>a.map((v,i)=>v+(b[i]-v)*u);
const hermite=(a,b,da,db,u,h)=>a.map((v,i)=>(2*u**3-3*u*u+1)*v+(u**3-2*u*u+u)*h*da[i]+(-2*u**3+3*u*u)*b[i]+(u**3-u*u)*h*db[i]);
function qlog(A){let q=norm(A);if(q[3]<0)q=q.map(x=>-x);const sin=Math.hypot(q[0],q[1],q[2]);if(sin<1e-10)return q.slice(0,3).map(x=>2*x);const a=2*Math.atan2(sin,q[3]);return q.slice(0,3).map(x=>x*a/sin)}
function qexp(v){if(!finite(v,3))throw Error('BAD_QEXP');const a=Math.hypot(...v),s=a<1e-9?.5:Math.sin(a/2)/a;return norm([...v.map(x=>x*s),Math.cos(a/2)])}
export function sample(clip,name,p){const n=clip?.sampleCount,s=clip?.bones?.[name];if(!s||!Number.isInteger(n)||n<120)throw Error('MISSING_SOURCE_BONE '+name);const u=Math.max(0,Math.min(n-1,p*n)),i=Math.floor(u),j=Math.min(n-1,i+1),t=u-i;return {position:lerp(s.pos[i],s.pos[j],t),quaternion:slerp(s.quat[i],s.quat[j],t),scale:lerp(s.scale[i],s.scale[j],t)}}
export function validate(clip){const n=clip?.sampleCount;if(!Number.isInteger(n)||n<240||Object.keys(clip.bones||{}).length!==74||!clip.bones[ROOT])throw Error('SOURCE_NOT_74_JOINT_240_SAMPLE');for(const [name,s] of Object.entries(clip.bones))if(s.pos?.length!==n||s.quat?.length!==n||s.scale?.length!==n||!s.pos.every(x=>finite(x,3))||!s.quat.every(x=>finite(x,4))||!s.scale.every(x=>finite(x,3)))throw Error('CORRUPT_SOURCE_'+name);return true}
export function calibrate(clip,seamStart=.93){validate(clip);if(!Number.isFinite(seamStart)||seamStart<.80||seamStart>.97)throw Error('SEAM_START_OUT_OF_RANGE');const n=clip.sampleCount,e=1/n,anchor=sample(clip,ROOT,0).position;
 // Measure noncyclic trend from the surviving endpoint just BEFORE the last
 // source key, never from the potentially teleported terminal key.
 const sampledEnd=sample(clip,ROOT,(n-1)/n).position;
 const endPhase=(n-1)/n;
 const trend=[(sampledEnd[0]-anchor[0])/endPhase,0,(sampledEnd[2]-anchor[2])/endPhase];
 const terminal=clip.terminalRootTrack||null;
 function detrend(name,p){const result=sample(clip,name,p);if(name===ROOT){result.position[0]-=trend[0]*p;result.position[2]-=trend[2]*p;}return result}
 const paths=Object.fromEntries(Object.keys(clip.bones).map(name=>{
  const start=detrend(name,0),s0=detrend(name,seamStart),sm=detrend(name,seamStart-e),sp=detrend(name,seamStart+e),startPlus=detrend(name,e);
  const deriv=(a,b)=>a.map((v,i)=>(v-b[i])/(2*e));
  const d0=deriv(sp.position,sm.position),d1=startPlus.position.map((v,i)=>(v-start.position[i])/e);
  const sc0=deriv(sp.scale,sm.scale),sc1=startPlus.scale.map((v,i)=>(v-start.scale[i])/e);
  const q0=norm(s0.quaternion),q1=norm(start.quaternion),qm0=norm(sm.quaternion),qp=norm(sp.quaternion),qep=norm(startPlus.quaternion);
  return [name,{p0:s0.position,p1:start.position,d0,d1,sc0:s0.scale,sc1:start.scale,ds0:sc0,ds1:sc1,q0,q1,delta:qlog(qm(qc(q0),q1)),w0:qlog(qm(qc(qm0),qp)).map(x=>x/(2*e)),w1:qlog(qm(qc(q1),qep)).map(x=>x/e)}]
 }));
 return {clip:clip.name,seamStart,anchor,trend,paths,rootMotionDetrended:true,sampledLast:sampledEnd,terminal};}
export function pose(clip,plan,phase){if(!plan||plan.clip!==clip.name||!finite(plan.anchor,3)||!finite(plan.trend,3))throw Error('WRONG_CALIBRATION');if(!Number.isFinite(phase))throw Error('BAD_PHASE');const p=mod1(phase),out={};for(const name of Object.keys(clip.bones)){
  let x;if(p<plan.seamStart){x=sample(clip,name,p);if(name===ROOT){x.position[0]-=plan.trend[0]*p;x.position[2]-=plan.trend[2]*p}}
  else{const a=plan.paths[name],u=(p-plan.seamStart)/(1-plan.seamStart),h=1-plan.seamStart;
   x={position:hermite(a.p0,a.p1,a.d0,a.d1,u,h),quaternion:norm(qm(a.q0,qexp(hermite([0,0,0],a.delta,a.w0,a.w1,u,h)))),scale:hermite(a.sc0,a.sc1,a.ds0,a.ds1,u,h)};
  }
  if(!finite(x.position,3)||!finite(x.quaternion,4)||!finite(x.scale,3))throw Error('NONFINITE_POSE_'+name);out[name]=x;
 }
 return {bones:out,phase:p,seamModified:p>=plan.seamStart};}
