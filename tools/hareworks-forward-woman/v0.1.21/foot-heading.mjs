/* Hareworks v0.1.18: Foot heading is distal orientation, not a knee IK input.
 * The source left/right bone heading values are mirrored about the direction
 * of travel; correct the right's mean heading without altering the left.
 * Source phase-varying right roll, rocker and toe-vector remain intact.
 */
export const wrapAngle=x=>Math.atan2(Math.sin(x),Math.cos(x));
export function mirrorRightHeadingBias(leftMean,rightMean){
 if(![leftMean,rightMean].every(Number.isFinite))throw Error('FOOT_HEADING_SOURCE_INVALID');
 if(!(leftMean>0&&rightMean<0))throw Error('FOOT_HEADING_SOURCE_SYMMETRY_UNEXPECTED');
 const delta=wrapAngle(-leftMean-rightMean);
 if(Math.abs(delta)>.45)throw Error('FOOT_HEADING_BIAS_EXCEEDS_SOURCE_EVIDENCE');
 return delta;
}
export function distalHeading(side,fit,profile){
 if(side!=='left'&&side!=='right'||!fit||!Number.isFinite(fit.ankleYaw)||!profile?.feet)
  throw Error('FOOT_HEADING_ARGS_INVALID');
 if(side==='left')return fit.ankleYaw;
 return fit.ankleYaw+mirrorRightHeadingBias(profile.feet.left.ankleYaw.start,profile.feet.right.ankleYaw.start);
}
