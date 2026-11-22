/* v0.1.18: calibrated full left+right gait-cycle step planner.
 * v0.1.16 erroneously multiplied hip-to-ankle Z by 0.66 at ordinary speed,
 * forcing excessive knee flexion. Preserve the source leg's actual anatomical
 * reach and use WORLD footfall distance + cadence to vary travel speed.
 * The viewer keeps the approved v0.1.16 procedural toe/yaw orientation. */
export const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const smooth=x=>{const t=clamp(x,0,1);return t*t*(3-2*t)};
export const REF_WALK_SPEED=.52;
export function speedGait(speed,referenceStride){
 if(!Number.isFinite(speed)||speed<0||speed>5||!Number.isFinite(referenceStride)||referenceStride<.9||referenceStride>1.55)
  throw Error('V018_FOOTFALL_INPUT_INVALID');
 // Do not extrapolate anatomical stride past the nearly fully extended archived legs.
 // For travel speed .52, exactly retain the accepted v0.1.9 leg trajectory.
 // Slow walk: gently shorten WORLD footfall distance, not hip-to-ankle reach.
 const low=clamp(speed/REF_WALK_SPEED,0,1),high=clamp((speed-REF_WALK_SPEED)/.28,0,1);
 const stride=referenceStride*(.90+.10*low+.012*high);
 const cadence=speed>0?speed/stride:0;
 const lead=smooth((speed-.16)/.64);
 return {speed,stride,cadence,phaseRate:cadence,scale:stride/referenceStride,
   crossover:0,stanceDuty:.615-.035*lead,
   liftFactor:.90+.12*lead,referenceStride,
   stepDistance:stride/2,
   source:'original v0.1.9 leg reach; world planted footfalls; no leg-Z compression'};
}
export function blendMotion(previous,target,dt){
 if(!previous)return {...target};
 if(!Number.isFinite(dt)||dt<0)throw Error('V018_DYNAMIC_GAIT_DT_INVALID');
 const k=1-Math.exp(-Math.min(dt,.1)/.22),out={...target};
 for(const key of ['stride','scale','crossover','stanceDuty','liftFactor'])
  out[key]=previous[key]+(target[key]-previous[key])*k;
 out.stepDistance=out.stride/2;
 out.cadence=target.speed>0?target.speed/out.stride:0;
 out.phaseRate=out.cadence;
 return out;
}
export function adjustAnkleForSpeed(hip,ankle,side,motion){
 if(!['left','right'].includes(side)||!hip||!ankle||hip.length!==3||ankle.length!==3||!motion)
  throw Error('V018_SOURCE_LANDMARK_INVALID');
 const leading=smooth(((ankle[2]-hip[2])+.07)/.34),sign=side==='left'?-1:1;
 // Preserve ankle Y and Z EXACTLY. Their 3D distance to the hip determines
 // nearly straight support legs. Only gentle runway placement changes X.
 return [ankle[0],ankle[1],ankle[2]]; // NO knee IK change from foot-heading style
}
export function transformSourceFoot(s,side,motion){
 if(!motion||!s||!s.ankle||!s.hip)throw Error('V018_SOURCE_FOOT_MISSING');
 const a=adjustAnkleForSpeed(s.hip,s.ankle,side,motion),shiftX=a[0]-s.ankle[0];
 const adapt=name=>{
  const p=s[name];if(!p||p.length!==3)throw Error('V018_SOURCE_NO_'+name);
  // Rigid X shift of all skinned foot patches; never shorten toe/heel rocker.
  return [p[0]+shiftX,p[1],p[2]];
 };
 return {...s,ankle:a,heel:adapt('heel'),sole:adapt('sole'),toe:adapt('toe')};
}
export function rootStepDistance(rootAt,curve,oldPhase,newPhase,motion){
 if(newPhase<oldPhase||!curve||!motion||motion.referenceStride!==curve.stride)
  throw Error('V018_WORLD_ROOT_PHASE_CONTRACT');
 // Full-cycle root displacement changes with speed, while world stance anchors
 // do not. The original phase-varying velocity profile remains intact.
 return (rootAt(curve,newPhase)-rootAt(curve,oldPhase))*motion.scale;
}
