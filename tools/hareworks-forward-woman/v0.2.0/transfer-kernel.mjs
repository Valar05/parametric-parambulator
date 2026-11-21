/* Hareworks v0.2.0. Source-calibrated three-clip directional style transfer.
 * NORMAL_FORWARD -> WOMAN_FORWARD provides local delta transforms.
 * NORMAL_BACKWARD is the destination pose. No reverse clip is ever substituted.
 * The clip-time axis is warped by source-measured contact-event anchors. */
const TAU=2*Math.PI;
export const CLIPS=['Walking','Walking_Woman','Walk_Backward'];
export const CONTACT={
  // Ground-near start times from exact source GLB's 61-sample v1.0.8
  // skinned-witness extraction; heuristic events, NOT verified force contacts.
  normal:{left:0.316667/1.033333,right:0.766667/1.033333},
  woman:{left:0.29/0.966667,right:0.821667/0.966667},
  backward:{left:0.173333/0.866667,right:0.635556/0.866667},
};
export const mod1=x=>((x%1)+1)%1;
function checkNum(x){if(!Number.isFinite(x))throw Error('NONFINITE_STYLE_INPUT');return x}
export function contactWarp(p,source,target){
 checkNum(p);const [a,b]=[source.left,source.right], [A,B]=[target.left,target.right];
 if(![a,b,A,B].every(x=>Number.isFinite(x)&&x>=0&&x<1)||!(a<b&&A<B))throw Error('BAD_CONTACT_ANCHORS');
 const phase=mod1(p),x=phase<a?phase+1:phase;
 const value=x<=b?A+(x-a)*(B-A)/(b-a):B+(x-b)*(A+1-B)/(a+1-b);
 return mod1(value);
}
export function phaseTriplet(backPhase){
 const backward=mod1(backPhase);
 const normal=contactWarp(backward,CONTACT.backward,CONTACT.normal);
 const woman=contactWarp(normal,CONTACT.normal,CONTACT.woman);
 return {backward,normal,woman};
}
export function quatNormalize(q){
 if(!Array.isArray(q)||q.length!==4||!q.every(Number.isFinite))throw Error('BAD_STYLE_QUAT');
 const n=Math.hypot(...q);if(n<1e-12)throw Error('ZERO_STYLE_QUAT');return q.map(v=>v/n);
}
export const quatConj=q=>[-q[0],-q[1],-q[2],q[3]];
export function quatMul(a,b){const [x,y,z,w]=a,[X,Y,Z,W]=b;
 return [w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z];}
export function quatSlerp(a0,b0,f){
 let a=quatNormalize(a0),b=quatNormalize(b0);checkNum(f);
 let dot=a.reduce((s,v,i)=>s+v*b[i],0);
 if(dot<0){b=b.map(x=>-x);dot=-dot}
 if(dot>0.9995)return quatNormalize(a.map((v,i)=>v+(b[i]-v)*f));
 const alpha=Math.acos(Math.max(-1,Math.min(1,dot))),sa=Math.sin(alpha);
 const wa=Math.sin((1-f)*alpha)/sa,wb=Math.sin(f*alpha)/sa;
 return quatNormalize(a.map((v,i)=>wa*v+wb*b[i]));
}
export function quatAngle(a0,b0){const a=quatNormalize(a0),b=quatNormalize(b0);let d=Math.abs(a.reduce((s,x,i)=>s+x*b[i],0));return 2*Math.acos(Math.min(1,Math.max(0,d)))}
function lerp3(a,b,t){return a.map((x,i)=>x+(b[i]-x)*t)}
function finite3(a){return Array.isArray(a)&&a.length===3&&a.every(Number.isFinite)}
export function sampleBone(clip,boneName,phase){
 const s=clip?.bones?.[boneName];if(!s)throw Error('MISSING_TRACK_BONE '+boneName);
 const n=clip.sampleCount;if(!Number.isInteger(n)||n<8||s.quat?.length!==n||s.pos?.length!==n)throw Error('CORRUPT_SOURCE_SAMPLE '+boneName);
 const scaled=mod1(phase)*n,i=Math.floor(scaled)%n,j=(i+1)%n,t=scaled-i;
 return {quat:quatSlerp(s.quat[i],s.quat[j],t),pos:lerp3(s.pos[i],s.pos[j],t)};
}
export function transferBone(back,normal,woman,strength,boneName){
 if(![back,normal,woman].every(x=>Array.isArray(x?.quat)&&finite3(x?.pos)))throw Error('TRANSFER_POSE_MISSING');
 checkNum(strength);if(strength<0||strength>1)throw Error('STYLE_GAIN_OUT_OF_RANGE');
 // Quaternion delta is in the bone's own parent-local coordinate space.
 // Correct noncommuting order: B * inverse(N) * W.
 const relative=quatNormalize(quatMul(quatConj(quatNormalize(normal.quat)),quatNormalize(woman.quat)));
 const weighted=quatSlerp([0,0,0,1],relative,strength);
 const quat=quatNormalize(quatMul(back.quat,weighted));
 const pos=back.pos.map((v,i)=>v+strength*(woman.pos[i]-normal.pos[i]));
 // Absolute forward/back locomotion is NEVER inherited from the forward clips.
 // Preserve the backward pelvis Z path; X sway and Y bounce may transfer.
 if(boneName==='mixamorigHips')pos[2]=back.pos[2];
 return {quat,pos,rotationDeltaRad:quatAngle([0,0,0,1],relative)};
}
export function transferPose(clips,backPhase,strength=1){
 const phases=phaseTriplet(backPhase);
 const backward=clips?.Walk_Backward,normal=clips?.Walking,woman=clips?.Walking_Woman;
 if(!backward||!normal||!woman)throw Error('THREE_SOURCE_CLIPS_REQUIRED');
 const bones={};let peakDelta=0,peakBone='',nonzero=0;
 const names=Object.keys(backward.bones);
 if(names.length!==74||Object.keys(normal.bones).length!==74||Object.keys(woman.bones).length!==74)throw Error('THREE_RIGS_MUST_HAVE_74_BONES');
 for(const name of names){
  const base=sampleBone(backward,name,phases.backward);
  const n=sampleBone(normal,name,phases.normal);
  const w=sampleBone(woman,name,phases.woman);
  const styled=transferBone(base,n,w,strength,name);
  bones[name]=styled;
  if(styled.rotationDeltaRad>1e-3){nonzero++}
  if(styled.rotationDeltaRad>peakDelta){peakDelta=styled.rotationDeltaRad;peakBone=name}
 }
 return {bones,phases,strength,peakBone,peakDeltaRad:peakDelta,nonzeroBoneCount:nonzero};
}
