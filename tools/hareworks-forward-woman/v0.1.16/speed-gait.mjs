/* v0.1.16: speed is distance/time, not an AnimationMixer playback multiplier.
 * Full stride is TWO steps (one left and one right). Alter stride, cadence,
 * fore-aft reach and lateral lead geometry together; retain v0.1.9 source curves.
 * No here-defined profile is owner-accepted until real skinned contact passes. */
export const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const smooth=x=>{const t=clamp(x,0,1);return t*t*(3-2*t)};
export const REF_WALK_SPEED=1.26677;
export function speedGait(speed,referenceStride){
 if(!Number.isFinite(speed)||speed<0||speed>5||!Number.isFinite(referenceStride)||referenceStride<.9||referenceStride>1.55)
  throw Error('DYNAMIC_GAIT_INPUT_INVALID');
 const ratio=clamp(speed/REF_WALK_SPEED,0,1);
 // At the reference source speed the original procedural reach is unchanged.
 // Slow: shorter step and greater cycles per DISTANCE than slowed reference clip.
 const stride=referenceStride*(.42+.58*ratio);
 const cadence=speed>0?speed/stride:0;
 const lead=smooth((ratio-.22)/.95);
 return {speed,stride,cadence,scale:stride/referenceStride,
  crossover:.012+.050*lead,stanceDuty:.615-.035*lead,
  liftFactor:.88+.23*lead,phaseRate:cadence,
  referenceStride,source:'accepted v0.1.9 hip-relative procedural gait'};
}
export function blendMotion(previous,target,dt){
 if(!previous)return {...target};
 if(!Number.isFinite(dt)||dt<0)throw Error('DYNAMIC_GAIT_DT_INVALID');
 const k=1-Math.exp(-Math.min(dt,.1)/.22),out={...target};
 for(const key of ['stride','scale','crossover','stanceDuty','liftFactor'])
  out[key]=previous[key]+(target[key]-previous[key])*k;
 out.cadence=out.stride>0?target.speed/out.stride:0;
 out.phaseRate=out.cadence;
 return out;
}
export function adjustAnkleForSpeed(hip,ankle,side,motion){
 if(!['left','right'].includes(side)||!hip||!ankle||hip.length!==3||ankle.length!==3||!motion)
  throw Error('DYNAMIC_GAIT_LANDMARK_INVALID');
 const z=ankle[2]-hip[2],leading=smooth((z+.07)/.34);
 const sign=side==='left'?-1:1;
 return [hip[0]+(ankle[0]-hip[0])*.94+sign*motion.crossover*(.28+.72*leading),
   ankle[1],hip[2]+z*motion.scale];
}
export function transformSourceFoot(s,side,motion){
 if(!motion||!s||!s.ankle||!s.hip)throw Error('DYNAMIC_SOURCE_MISSING');
 const a=adjustAnkleForSpeed(s.hip,s.ankle,side,motion),shiftX=a[0]-s.ankle[0];
 const adapt=(name)=>{
  const p=s[name]; if(!p||p.length!==3)throw Error('DYNAMIC_SOURCE_NO_'+name);
  return [p[0]+shiftX,p[1],s.hip[2]+(p[2]-s.hip[2])*motion.scale];
 };
 return {...s,ankle:a,heel:adapt('heel'),sole:adapt('sole'),toe:adapt('toe')};
}
export function rootStepDistance(rootAt,curve,oldPhase,newPhase,motion){
 if(newPhase<oldPhase||!curve||!motion||motion.referenceStride!==curve.stride)
  throw Error('DYNAMIC_ROOT_PHASE_OR_CONTRACT');
 return (rootAt(curve,newPhase)-rootAt(curve,oldPhase))*motion.scale;
}
