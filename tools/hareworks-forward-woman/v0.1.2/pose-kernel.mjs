/* v0.1.2: source-calibrated, phase-driven procedural pelvis + foot pose.
 * No keyframe sampling at runtime; explicit parameter curves, not clip tracks.
 * One forward Walking_Woman cycle ONLY. No world contact, aim or turn controller. */
export const clamp=(v,lo,hi)=>Math.max(lo,Math.min(hi,v));
export const angleDiff=(a,b)=>Math.atan2(Math.sin(a-b),Math.cos(a-b));
export const phase=(t,d)=>clamp(t/d,0,1-1e-10);
export function curve(c,q){
 let v=c.start;
 for(let i=0;i<c.sin.length;i++){
   const n=i+1,theta=2*Math.PI*n*q;
   v+=c.sin[i]*Math.sin(theta)+c.cosMinusOne[i]*(Math.cos(theta)-1);
 }
 return v;
}
export function independentPose(p,t){
 const q=phase(t,p.duration);
 const pelvis=[curve(p.pelvis.x,q),curve(p.pelvis.y,q),curve(p.pelvis.z,q)];
 const yaw=curve(p.pelvis.yaw,q);
 const feet={};
 for(const side of ['left','right']){
  const f=p.feet[side];
  feet[side]={toeVector:[curve(f.toeVectorX,q),curve(f.toeVectorY,q),curve(f.toeVectorZ,q)],ankleYaw:curve(f.ankleYaw,q)};
 }
 return {q,pelvis,pelvisYaw:yaw,feet};
}
export function validateProfile(p){
 if(p.schema!=='hareworks-forward-woman-independent-pelvis-foot-v0.1.2')throw Error('POSE_PROFILE_SCHEMA');
 if(p.clip!=='Walking_Woman'||p.sourceSha256!=='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6')throw Error('POSE_PROFILE_SOURCE');
 if(Math.abs(p.duration-.966667)>.0001)throw Error('POSE_PROFILE_DURATION');
 for(const ch of [p.pelvis.x,p.pelvis.y,p.pelvis.z,p.pelvis.yaw,...['left','right'].flatMap(side=>['toeVectorX','toeVectorY','toeVectorZ','ankleYaw'].map(name=>p.feet[side][name]))]){
  if(!Number.isFinite(ch.start)||ch.sin.length!==4||ch.cosMinusOne.length!==4||![...ch.sin,...ch.cosMinusOne].every(Number.isFinite))throw Error('POSE_PROFILE_COEFFICIENTS');
 }
 return true;
}
