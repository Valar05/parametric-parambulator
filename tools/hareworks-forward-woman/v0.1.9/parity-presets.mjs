/* Hareworks v0.1.7: pure verifier settings and double-cover-safe bone rollback audit. */
export function checkedPreset(input) {
  if (!input || typeof input !== 'object' || !Number.isFinite(input.strength)
      || input.strength < 0 || input.strength > 1.5
      || !Number.isInteger(input.harmonics) || input.harmonics < 1 || input.harmonics > 12)
    throw Error('INVALID_VERIFIER_PRESET');
  return Object.freeze({strength:input.strength,harmonics:input.harmonics});
}
export function quaternionDistance(a,b) {
  if (!Array.isArray(a) || !Array.isArray(b) || a.length !== 4 || b.length !== 4
      || ![...a,...b].every(Number.isFinite)) throw Error('BAD_QUATERNION_VECTOR');
  let plus=0,minus=0;
  for(let i=0;i<4;i++){plus+=(a[i]-b[i])**2;minus+=(a[i]+b[i])**2;}
  return Math.sqrt(Math.min(plus,minus));
}
export function presetSeparation(snapshotsA,snapshotsB,minimum=1e-5) {
  if (!Array.isArray(snapshotsA) || !Array.isArray(snapshotsB)
      || !snapshotsA.length || snapshotsA.length!==snapshotsB.length)
    throw Error('PRESET_SENSITIVITY_NO_SAMPLES');
  let maxQuaternionDistance=0,offender=null,checked=0;
  for(let i=0;i<snapshotsA.length;i++){
    const a=snapshotsA[i],b=snapshotsB[i];
    const keys=Object.keys(a);
    if(!keys.length || keys.length!==Object.keys(b).length) throw Error('PRESET_SENSITIVITY_BONE_MISMATCH');
    for(const bone of keys){
      if(!(bone in b))throw Error('PRESET_SENSITIVITY_BONE_MISMATCH '+bone);
      const distance=quaternionDistance(a[bone],b[bone]);checked++;
      if(distance>maxQuaternionDistance){maxQuaternionDistance=distance;offender={bone,sample:i,distance};}
    }
  }
  const pass=maxQuaternionDistance>minimum;
  return {pass,checked,maxQuaternionDistance,offender,minimum,reason:pass?'PRESETS_PHYSICALLY_DIFFERENT':'PRESETS_IDENTICAL_OR_FROZEN'};
}
// Compare restored bone transform COMPONENTS, not quaternion angleTo's
// acos(1-epsilon) which can report nonzero even for an exact copy.
export function compareBonePose(snapshot, current, epsilon=1e-12) {
  if(!Array.isArray(snapshot)||!Array.isArray(current)||snapshot.length!==current.length||!snapshot.length)
    throw Error('ROLLBACK_POSE_SHAPE');
  let max={position:0,scale:0,quaternion:0},firstBad=null,badCount=0;
  for(let i=0;i<snapshot.length;i++){
    const a=snapshot[i],b=current[i];
    if(a.name!==b.name)throw Error('ROLLBACK_BONE_MISMATCH_'+i);
    for(const field of ['position','scale','quaternion']){
      const x=a[field],y=b[field];
      if(!Array.isArray(x)||!Array.isArray(y)||x.length!==y.length||!x.every(Number.isFinite)||!y.every(Number.isFinite))throw Error('ROLLBACK_COMPONENT_INVALID_'+a.name+'_'+field);
      const distance=field==='quaternion'?quaternionDistance(x,y):Math.hypot(...x.map((v,k)=>v-y[k]));
      max[field]=Math.max(max[field],distance);
      if(distance>epsilon){badCount++;if(!firstBad)firstBad={name:a.name,field,error:distance,index:i};}
    }
  }
  return {pass:badCount===0,epsilon,checkedBones:snapshot.length,badCount,firstBad,max};
}
