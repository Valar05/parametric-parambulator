/* Hareworks Walk_Backward v0.2.1: full-rig, source-calibrated, independent
 * continuous pose equations. Reference mixer is calibration/evidence ONLY;
 * generated skeleton never runs an animation track. Root horizontal trajectory
 * is detrended, and the source's terminal root-teleport key is excluded.
 */
export const CLIP='Walk_Backward';
export const ROOT='mixamorigHips';
const ID=[0,0,0,1];
export const mod1=x=>((x%1)+1)%1;
const good3=v=>Array.isArray(v)&&v.length===3&&v.every(Number.isFinite);
const good4=v=>Array.isArray(v)&&v.length===4&&v.every(Number.isFinite);
const norm=q=>{if(!good4(q))throw Error('INVALID_QUAT');const n=Math.hypot(...q);if(n<1e-10)throw Error('ZERO_QUAT');return q.map(v=>v/n)};
const conj=q=>[-q[0],-q[1],-q[2],q[3]];
const mul=(a,b)=>{const [x,y,z,w]=a,[X,Y,Z,W]=b;return [w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z]};
function qlog(q0){const raw=norm(q0),q=raw[3]<0?raw.map(x=>-x):raw,s=Math.hypot(q[0],q[1],q[2]);if(s<1e-10)return [q[0]*2,q[1]*2,q[2]*2];const a=2*Math.atan2(s,q[3]);return q.slice(0,3).map(x=>x*a/s)}
function qexp(v){if(!good3(v))throw Error('INVALID_QUAT_LOG');const a=Math.hypot(...v),s=a<1e-9?.5:Math.sin(a/2)/a;return norm([...v.map(x=>x*s),Math.cos(a/2)])}
export function angleDeg(a,b){const x=norm(a),y=norm(b),d=Math.abs(x.reduce((s,v,i)=>s+v*y[i],0));return 2*Math.acos(Math.min(1,d))*180/Math.PI}
function slerp(qa,qb,t){const a=norm(qa);let b=norm(qb);let dot=a.reduce((s,x,i)=>s+x*b[i],0);if(dot<0){b=b.map(x=>-x);dot=-dot}if(dot>.9995)return norm(a.map((x,i)=>x+(b[i]-x)*t));let theta=Math.acos(Math.min(1,Math.max(-1,dot))),d=Math.sin(theta);return norm(a.map((x,i)=>(Math.sin((1-t)*theta)*x+Math.sin(t*theta)*b[i])/d))}
const lerp=(a,b,u)=>a.map((x,i)=>x+(b[i]-x)*u);
function hermite(a,b,da,db,u,h){const v=2*u*u*u-3*u*u+1,w=u*u*u-2*u*u+u,x=-2*u*u*u+3*u*u,y=u*u*u-u*u;return a.map((z,i)=>v*z+w*h*da[i]+x*b[i]+y*h*db[i])}
function sourceSample(clip,bone,p){const n=clip.sampleCount,s=clip.bones[bone];if(!s)throw Error('MISSING_SOURCE_BONE '+bone);const u=Math.max(0,Math.min(n-1,p*n)),i=Math.floor(u),j=Math.min(i+1,n-1),v=u-i;return {position:lerp(s.pos[i],s.pos[j],v),quaternion:slerp(s.quat[i],s.quat[j],v),scale:lerp(s.scale[i],s.scale[j],v)}}
export function deriveInPlace(clip,seamStartOverride=null){
 const n=clip?.sampleCount,rs=clip?.bones?.[ROOT],bones=clip?.bones;
 if(!Number.isInteger(n)||n<240||Object.keys(bones||{}).length!==74||!rs||rs.pos.length!==n||rs.quat.length!==n)throw Error('BAD_REAL_SOURCE_SAMPLE_CONTRACT');
 for(const [name,s] of Object.entries(bones))if(s.pos?.length!==n||s.quat?.length!==n||s.scale?.length!==n||!s.pos.every(good3)||!s.quat.every(good4)||!s.scale.every(good3))throw Error('SOURCE_BONE_CHANNEL_MISMATCH '+name);
 // Detect the artificial last-key reset from a robust normal-speed baseline.
 const diffs=[];for(let i=1;i<n;i++)diffs.push(Math.abs(rs.pos[i][2]-rs.pos[i-1][2]));
 const typical=diffs.slice(Math.floor(n*.12),Math.floor(n*.68)).sort((a,b)=>a-b)[Math.floor(n*.56/2)]||0;
 let resetIndex=-1;for(let i=Math.floor(n*.77);i<n;i++){
  const jump=rs.pos[i][2]-rs.pos[i-1][2];
  if(jump>Math.max(.017,typical*8)){resetIndex=i;break}
 }
 if(resetIndex<0)throw Error('SOURCE_TERMINAL_ROOT_RESET_NOT_DETECTED');
 const cleanIndex=resetIndex-1,cleanPhase=cleanIndex/n;
 if(cleanPhase<.86||cleanPhase>.995)throw Error('SOURCE_RESET_OUTSIDE_TERMINAL_WINDOW '+cleanPhase);
 const prev=Math.max(0,cleanIndex-12),speed=(cleanIndex-prev)/n;
 const last=rs.pos[cleanIndex],earlier=rs.pos[prev],start=rs.pos[0];
 const velocity=[(last[0]-earlier[0])/speed,0,(last[2]-earlier[2])/speed];
 const delta=[last[0]+velocity[0]*(1-cleanPhase)-start[0],0,last[2]+velocity[2]*(1-cleanPhase)-start[2]];
 if(!(delta[2]<-.5&&delta[2]>-3))throw Error('BACKWARD_ROOT_TRAVEL_NOT_FOUND '+delta[2]);
 // The final source reset is a discontinuity, NOT a physical part of the gait.
 // Repair the last ~6% of the cycle with C1 periodic boundary splines.
 const seamStart=seamStartOverride===null?Math.min(.93,cleanPhase-.025):Number(seamStartOverride);
 if(!(seamStart>.85&&seamStart<=Math.min(.93,cleanPhase-.025)))throw Error('SOURCE_NO_SAFE_PRE_RESET_SEAM '+seamStart);
 const h=1-seamStart,eps=1/n;
 const seam={};
 function detrended(name,p){const v=sourceSample(clip,name,p);if(name===ROOT){v.position[0]-=delta[0]*p;v.position[2]-=delta[2]*p}return v}
 for(const name of Object.keys(bones)){
  const startPose=detrended(name,0),s0=detrended(name,seamStart),sPrior=detrended(name,seamStart-eps),sAfter=detrended(name,seamStart+eps),sNext=detrended(name,eps);
  const startDerivative=s0.position.map((x,i)=>(sAfter.position[i]-sPrior.position[i])/(2*eps));
  const endDerivative=startPose.position.map((x,i)=>(sNext.position[i]-x)/eps);
  const scaleD0=s0.scale.map((x,i)=>(sAfter.scale[i]-sPrior.scale[i])/(2*eps));
  const scaleD1=startPose.scale.map((x,i)=>(sNext.scale[i]-x)/eps);
  const q0=norm(s0.quaternion),qEnd=norm(startPose.quaternion),qAfter=norm(sAfter.quaternion),qNext=norm(sNext.quaternion),qBefore=norm(sPrior.quaternion);
  const endVector=qlog(mul(conj(q0),qEnd));
  const omega0=qlog(mul(conj(qBefore),qAfter)).map(x=>x/(2*eps));
  const omega1=qlog(mul(conj(qEnd),qNext)).map(x=>x/eps);
  seam[name]={p0:s0.position,p1:startPose.position,d0:startDerivative,d1:endDerivative,scale0:s0.scale,scale1:startPose.scale,scaleD0,scaleD1,q0,q1:qEnd,v1:endVector,w0:omega0,w1:omega1};
 }
 return {source:CLIP,sampleCount:n,root:ROOT,resetIndex,cleanPhase,typicalRootStep:typical,resetRootStep:rs.pos[resetIndex][2]-rs.pos[resetIndex-1][2],
  seamStart,cycleTravel:delta,cycleTravelMagnitude:Math.hypot(delta[0],delta[2]),horizontalRootTravelRemoved:true,sourceJointCount:74,seam};
}
export function poseInPlace(clip,model,p){if(!Number.isFinite(p))throw Error('NONFINITE_PHASE');if(model?.source!==CLIP||!good3(model.cycleTravel))throw Error('INVALID_SOURCE_TREND');const q=mod1(p),out={};
 for(const name of Object.keys(clip.bones)){
  let t;
  if(q<model.seamStart){t=sourceSample(clip,name,q);if(name===ROOT){t.position[0]-=model.cycleTravel[0]*q;t.position[2]-=model.cycleTravel[2]*q}}
  else{const s=model.seam[name],u=(q-model.seamStart)/(1-model.seamStart),h=1-model.seamStart;
   const r=hermite([0,0,0],s.v1,s.w0,s.w1,u,h);
   t={position:hermite(s.p0,s.p1,s.d0,s.d1,u,h),quaternion:norm(mul(s.q0,qexp(r))),scale:hermite(s.scale0,s.scale1,s.scaleD0,s.scaleD1,u,h)};
  }
  if(!good3(t.position)||!good4(t.quaternion)||!good3(t.scale))throw Error('INVALID_GENERATED_JOINT '+name);
  out[name]=t;
 }
 if(Object.keys(out).length!==74)throw Error('GENERATED_RIG_INCOMPLETE');
 return {phase:q,bones:out,removedCycleTravel:model.cycleTravel.map(x=>x*q),sourceResetSuppressed:q>=model.seamStart};
}
export function exactControlPose(clip,model,p){const t=sourceSample(clip,ROOT,mod1(p));t.position[0]-=model.cycleTravel[0]*mod1(p);t.position[2]-=model.cycleTravel[2]*mod1(p);return t}
