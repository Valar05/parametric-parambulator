/* Hareworks v0.2.5: source-calibrated, pose-offset-free, independently gated
 * gait-character experiments. Never touches the accepted backward solver. */
export const LAYERS=['pelvis','legs','torso','arms'];
export const PHASE_OFFSET=0.9777777777777777; // exact v0.2.3 measured alignment
const E=[0,0,0,1];
export const mod1=p=>((p%1)+1)%1;
export function groupOf(n){
 if(n==='mixamorigHips')return 'pelvis';
 if(/UpLeg|Leg|Foot|ToeBase/.test(n))return 'legs';
 if(/Spine|Neck|Head/.test(n))return 'torso';
 if(/Shoulder|Arm|Hand/.test(n))return 'arms';
 return null;
}
function finite(v,n){return Array.isArray(v)&&v.length===n&&v.every(Number.isFinite)}
export function qnorm(q){if(!finite(q,4))throw Error('QUAT_INVALID');const l=Math.hypot(...q);if(l<1e-9)throw Error('QUAT_ZERO');return q.map(x=>x/l)}
export const qconj=q=>[-q[0],-q[1],-q[2],q[3]];
export function qmul(a,b){const [x,y,z,w]=a,[X,Y,Z,W]=b;return [w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z]}
export function qslerp(a0,b0,t){if(!Number.isFinite(t)||t<0||t>1)throw Error('SLERP_GAIN_INVALID');const a=qnorm(a0);let b=qnorm(b0);let d=a.reduce((s,x,i)=>s+x*b[i],0);if(d<0){b=b.map(x=>-x);d=-d}if(d>.9995)return qnorm(a.map((x,i)=>x+(b[i]-x)*t));const phi=Math.acos(Math.min(1,d)),denom=Math.sin(phi);return qnorm(a.map((x,i)=>(Math.sin((1-t)*phi)*x+Math.sin(t*phi)*b[i])/denom))}
export function qangleDeg(a,b){const d=Math.min(1,Math.abs(qnorm(a).reduce((s,x,i)=>s+x*qnorm(b)[i],0)));return 2*Math.acos(d)*180/Math.PI}
const lerp=(a,b,t)=>a.map((x,i)=>x*(1-t)+b[i]*t);
const smooth=x=>{const y=Math.max(0,Math.min(1,x));return y*y*(3-2*y)};
export function sampleSource(clip,bone,p){
 const s=clip?.bones?.[bone],n=clip?.sampleCount;
 if(!s||!Number.isInteger(n)||n<120)throw Error('SOURCE_BONE_MISSING_'+bone);
 const q=mod1(p);let a,b,t;
 // Source authored clips can contain a terminal key reset. Blend the last
 // 7% back to sample zero instead of interpolating across that teleport.
 if(q>=.93){const u=smooth((q-.93)/.07),last=Math.min(n-1,Math.floor(.93*n));a=last;b=0;t=u;}
 else{const idx=q*n;a=Math.min(n-1,Math.floor(idx));b=Math.min(n-1,a+1);t=idx-a;}
 return {quaternion:qslerp(s.quat[a],s.quat[b],t),position:lerp(s.pos[a],s.pos[b],t),scale:lerp(s.scale[a],s.scale[b],t)};
}
export function sourceSignature(normal,woman,bone,p,phaseOffset=PHASE_OFFSET){
 const n0=sampleSource(normal,bone,0),w0=sampleSource(woman,bone,phaseOffset);
 const n=sampleSource(normal,bone,p),w=sampleSource(woman,bone,mod1(p+phaseOffset));
 const nn=qnorm(qmul(qconj(n0.quaternion),n.quaternion));
 const ww=qnorm(qmul(qconj(w0.quaternion),w.quaternion));
 const dynamic=qnorm(qmul(qconj(nn),ww));
 const displacement=n.position.map((x,i)=>(w.position[i]-w0.position[i])-(x-n0.position[i]));
 return {dynamic,displacement,rawStaticOffsetDeg:qangleDeg(n0.quaternion,w0.quaternion)};
}
export function stylePose(base,normal,woman,p,gains,phaseOffset=PHASE_OFFSET){
 if(!base?.bones||!normal?.bones||!woman?.bones||Object.keys(base.bones).length!==74)throw Error('SOURCE_TOPOLOGY_NOT_74');
 const weights={};for(const l of LAYERS){const g=Number(gains?.[l]??0);if(!Number.isFinite(g)||g<0||g>1)throw Error('GAIN_OUT_OF_RANGE_'+l);weights[l]=g}
 const out={};for(const [name,b] of Object.entries(base.bones)){
  const group=groupOf(name),gain=group?weights[group]:0;
  if(!gain){out[name]={quaternion:b.quaternion.slice(),position:b.position.slice(),scale:b.scale.slice()};continue}
  const delta=sourceSignature(normal,woman,name,p,phaseOffset);
  const quaternion=qnorm(qmul(b.quaternion,qslerp(E,delta.dynamic,gain)));
  const position=b.position.slice();
  if(group==='pelvis'){
   position[0]+=gain*delta.displacement[0];position[1]+=gain*delta.displacement[1];
   // Absolutely no root travel: retain original backward in-place Z.
   position[2]=b.position[2];
  }
  out[name]={quaternion,position,scale:b.scale.slice()};
 }
 if(out.mixamorigHips.position[2]!==base.bones.mixamorigHips.position[2])throw Error('ROOT_DIRECTION_CHANGED');
 return {bones:out,gains:weights,phase:mod1(p),sourcePhaseWoman:mod1(p+phaseOffset)};
}
export function zeroGains(){return {pelvis:0,legs:0,torso:0,arms:0}}
