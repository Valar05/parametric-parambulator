/* Hareworks v0.2.3 research mathematics. Pure, source-only measurements.
   No pose creation, style transfer or modification of source clips. */
export const mod1 = x => ((x % 1) + 1) % 1;
const finite3 = v => Array.isArray(v) && v.length === 3 && v.every(Number.isFinite);
const finite4 = v => Array.isArray(v) && v.length === 4 && v.every(Number.isFinite);
export function normalized(q) {
  if (!finite4(q)) throw Error('INVALID_SOURCE_QUATERNION');
  const d=Math.hypot(...q); if(d < 1e-9) throw Error('DEGENERATE_SOURCE_QUATERNION');
  return q.map(x=>x/d);
}
export const conjugate=q=>[-q[0],-q[1],-q[2],q[3]];
export function multiply(a,b){const [x,y,z,w]=a,[X,Y,Z,W]=b;return [w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z]}
export function angleDeg(qa,qb) {const a=normalized(qa),b=normalized(qb);let d=Math.abs(a.reduce((s,x,i)=>s+x*b[i],0));return 2*Math.acos(Math.max(0,Math.min(1,d)))*180/Math.PI;}
export function slerp(qa,qb,t){if(!Number.isFinite(t)||t<0||t>1)throw Error('BAD_INTERPOLATION');const a=normalized(qa);let b=normalized(qb);let dot=a.reduce((s,x,i)=>s+x*b[i],0);if(dot<0){b=b.map(x=>-x);dot=-dot}if(dot>.9995){const q=a.map((v,i)=>v+t*(b[i]-v));return normalized(q)}const th=Math.acos(Math.min(1,dot)),si=Math.sin(th);return normalized(a.map((v,i)=>(Math.sin((1-t)*th)*v+Math.sin(t*th)*b[i])/si))}
export function sample(series,p){const n=series.length;if(!n)throw Error('EMPTY_SAMPLE_ARRAY');if(!Number.isFinite(p))throw Error('NONFINITE_PHASE');const index=mod1(p)*n,i=Math.floor(index)%n,t=index-i,j=(i+1)%n;return {i,j,t}}
export function poseAt(clip,name,p){const rows=clip?.bones?.[name],n=clip?.count;if(!rows||!n||rows.length!==n)throw Error('MISSING_BONE_DATA_'+name);const {i,j,t}=sample(rows,p);const a=rows[i],b=rows[j];const blend=(key)=>a[key].map((x,k)=>x+(b[key][k]-x)*t);
 return {lq:slerp(a.lq,b.lq,t),lp:blend('lp'),wp:blend('wp'),hq:blend('hq'),hp:blend('hp')};}
export function rms(v){if(!v.length)return null;return Math.sqrt(v.reduce((s,x)=>s+x*x,0)/v.length)}
export function range(v){return v.length?Math.max(...v)-Math.min(...v):null}
export function groupBone(name){if(/Hips/.test(name))return 'pelvis';if(/Spine/.test(name))return 'torso';if(/Neck|Head/.test(name))return 'head-and-neck';if(/Shoulder/.test(name))return 'shoulders';if(/ForeArm/.test(name))return 'forearms';if(/UpLeg|Leg/.test(name))return 'legs';if(/Foot|Toe/.test(name))return 'feet';if(/Hand/.test(name)&&/Thumb|Index|Middle|Ring|Pinky/.test(name))return 'fingers';if(/Hand/.test(name))return 'hands';if(/Arm/.test(name))return 'upper-arms';return 'other'}
// One global phase shift is inferred from the two pairs of foot trajectories;
// amplitude and center normalization prevent a smaller stride biasing phase.
function footSignal(clip,foot,axis){const arr=clip.bones[foot].map(r=>r.hp[axis]);const valid=arr.slice(0,Math.floor(arr.length*.94));const mean=valid.reduce((s,v)=>s+v,0)/valid.length;const std=Math.max(0.015,rms(valid.map(v=>v-mean)));return {name:foot,axis,mean,std};}
export function alignPhase(normal,woman){
 const foot=['mixamorigLeftFoot','mixamorigRightFoot'];for(const f of foot)if(!normal.bones[f]||!woman.bones[f])throw Error('FOOT_ALIGNMENT_SOURCE_MISSING_'+f);
 const specs=[];for(const name of foot)for(const axis of [0,2])specs.push({a:footSignal(normal,name,axis),b:footSignal(woman,name,axis)});
 const candidates=[];
 for(let shiftIndex=0;shiftIndex<180;shiftIndex++){
  const shift=shiftIndex/180;let sum=0,n=0;
  for(let i=0;i<180;i++){
   const p=i/180,q=mod1(p+shift);if(p>=.93||q>=.93)continue;
   for(const {a,b} of specs){const nVal=(poseAt(normal,a.name,p).hp[a.axis]-a.mean)/a.std;const wVal=(poseAt(woman,b.name,q).hp[b.axis]-b.mean)/b.std;sum+=(nVal-wVal)**2;n++}
  }
  if(n>=250)candidates.push({shift,cost:sum/n,pairs:n});
 }
 if(!candidates.length)throw Error('NO_VALID_PHASE_ALIGNMENT');candidates.sort((a,b)=>a.cost-b.cost);
 const best=candidates[0],alternative=candidates.find(x=>Math.min(mod1(x.shift-best.shift),mod1(best.shift-x.shift))>.09)||candidates[1];
 return {womanPhaseOffset:best.shift,normalPhaseOffset:0,method:'global offset minimizing normalized hip-relative left/right foot X/Z trajectory differences',cost:best.cost,samplePairs:best.pairs,distinctAlternativeCost:alternative?.cost??null,ambiguityRatio:alternative?alternative.cost/best.cost:null,sourceTerminalWindowExcluded:[.93,1]};
}
export function compareClips(normal,woman,align){if(normal.count!==woman.count||normal.boneNames.length!==74||woman.boneNames.length!==74)throw Error('SOURCE_RIG_RESEARCH_CONTRACT');
 const bones=normal.boneNames;for(const name of bones)if(!woman.bones[name])throw Error('SOURCE_BONE_TOPOLOGY_MISMATCH_'+name);
 const phases=[];for(let i=0;i<240;i++){const p=i/240,q=mod1(p+align.womanPhaseOffset);if(p<.93&&q<.93)phases.push({p,q})}if(phases.length<150)throw Error('INSUFFICIENT_ALIGNED_SOURCE_PHASES');
 const out=[];
 for(const name of bones){
  const p0=phases[0],n0=poseAt(normal,name,p0.p),w0=poseAt(woman,name,p0.q);
  const raw=[],dynamic=[],displacementN=[],displacementW=[],relativePositionDelta=[],translationalDelta=[];
  let peakAt=0,maxDynamic=0;const trajectories={normal:{},woman:{}};
  for(const axis of ['x','y','z']){trajectories.normal[axis]=[];trajectories.woman[axis]=[]}
  for(const {p,q} of phases){const a=poseAt(normal,name,p),b=poseAt(woman,name,q);
   const staticRemovedN=multiply(conjugate(normalized(n0.lq)),normalized(a.lq)),staticRemovedW=multiply(conjugate(normalized(w0.lq)),normalized(b.lq));
   const da=angleDeg(staticRemovedN,staticRemovedW);dynamic.push(da);if(da>maxDynamic){maxDynamic=da;peakAt=p}
   raw.push(angleDeg(a.lq,b.lq));displacementN.push(angleDeg(n0.lq,a.lq));displacementW.push(angleDeg(w0.lq,b.lq));
   relativePositionDelta.push(Math.hypot(...a.hp.map((x,i)=>x-b.hp[i])));
   translationalDelta.push(Math.hypot(...a.lp.map((x,i)=>(x-n0.lp[i])-(b.lp[i]-w0.lp[i]))));
   for(let i=0;i<3;i++){trajectories.normal['xyz'[i]].push(a.hp[i]);trajectories.woman['xyz'[i]].push(b.hp[i])}
  }
  const frameRanges={};for(const a of ['x','y','z'])frameRanges[a]={normal:range(trajectories.normal[a]),woman:range(trajectories.woman[a]),difference:range(trajectories.woman[a])-range(trajectories.normal[a])};
  const result={bone:name,group:groupBone(name),sampledAlignedPhases:phases.length,staticPoseOffsetDeg:angleDeg(n0.lq,w0.lq),meanRawPoseDifferenceDeg:raw.reduce((s,x)=>s+x,0)/raw.length,
   motionDeltaRmsDeg:rms(dynamic),motionDeltaMaxDeg:maxDynamic,phaseOfMaxDynamicDifference:peakAt,
   normalMotionFromAnchorRmsDeg:rms(displacementN),womanMotionFromAnchorRmsDeg:rms(displacementW),motionFromAnchorRmsRatio:rms(displacementN)>1e-3?rms(displacementW)/rms(displacementN):null,
   hipRelativePositionDifferenceRmsUnits:rms(relativePositionDelta),localTranslationMotionDeltaRmsUnits:rms(translationalDelta),hipFramePositionRange:frameRanges};
  out.push(result)
 }
 out.sort((a,b)=>b.motionDeltaRmsDeg-a.motionDeltaRmsDeg);
 const groups={};for(const bone of out){let g=groups[bone.group]??={boneCount:0,motionDeltaRmsValues:[],staticPoseOffsets:[]};g.boneCount++;g.motionDeltaRmsValues.push(bone.motionDeltaRmsDeg);g.staticPoseOffsets.push(bone.staticPoseOffsetDeg)}
 for(const g of Object.values(groups)){g.meanBoneMotionDeltaRmsDeg=g.motionDeltaRmsValues.reduce((s,v)=>s+v,0)/g.boneCount;g.meanBoneStaticPoseOffsetDeg=g.staticPoseOffsets.reduce((s,v)=>s+v,0)/g.boneCount;delete g.motionDeltaRmsValues;delete g.staticPoseOffsets}
 return {sampledMatchedPhases:phases.length,perBone:out,groups};
}
