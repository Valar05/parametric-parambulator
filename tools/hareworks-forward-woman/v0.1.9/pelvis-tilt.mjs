/* v0.1.9: preserve source pelvis world yaw while fitting the yaw-neutral
 * pitch/roll remainder from the real GLB source. Pure quaternion math.
 * This is a source-calibrated phase controller, NOT runtime clip playback.
 */
import {quatConjugate,quatMultiply,quatAngle} from '../v0.1.5/upper-kernel.mjs';
import {fitSourceAnchoredTrack,evalSourceAnchoredTrack} from '../v0.1.8/upper-anchor.mjs';
function norm(q){if(!Array.isArray(q)||q.length!==4||!q.every(Number.isFinite))throw Error('PELVIS_QUAT_INVALID');const m=Math.hypot(...q);if(m<1e-12)throw Error('PELVIS_QUAT_ZERO');return q.map(v=>v/m)}
export function yawQuat(yaw){if(!Number.isFinite(yaw))throw Error('PELVIS_YAW_NONFINITE');return [0,Math.sin(yaw/2),0,Math.cos(yaw/2)]}
export function rotateVec(q,v){const p=quatMultiply(quatMultiply(norm(q),[...v,0]),quatConjugate(norm(q)));return p.slice(0,3)}
export function decomposeWorldPelvis(q){
 const unit=norm(q),front=rotateVec(unit,[0,0,1]);
 const yaw=Math.atan2(front[0],front[2]);
 const tilt=norm(quatMultiply(quatConjugate(yawQuat(yaw)),unit));
 const up=rotateVec(tilt,[0,1,0]);
 return {yaw,tilt,sideLeanRad:Math.atan2(up[0],up[1]),forwardLeanRad:Math.atan2(up[2],up[1])};
}
export function fitSourcePelvisTilt(sourceWorldQuats,maxHarmonics=12){
 if(!Array.isArray(sourceWorldQuats)||sourceWorldQuats.length<2*maxHarmonics+4)throw Error('PELVIS_SOURCE_SAMPLES');
 const splits=sourceWorldQuats.map(decomposeWorldPelvis),fit=fitSourceAnchoredTrack(splits.map(v=>({quaternion:v.tilt,position:[0,0,0]})),maxHarmonics);
 const first=splits[0].tilt;
 const variationDeg=Math.max(...splits.map(s=>quatAngle(first,s.tilt)))*180/Math.PI;
 return {fit,variationDeg,sourceCount:splits.length,baselineSideLeanDeg:splits[0].sideLeanRad*180/Math.PI,baselineForwardLeanDeg:splits[0].forwardLeanRad*180/Math.PI};
}
export function evaluatePelvisWorld(fit,phase,preservedYaw,harmonics){
 const tilt=evalSourceAnchoredTrack(fit.fit,phase,harmonics,1).quaternion;
 return norm(quatMultiply(yawQuat(preservedYaw),tilt));
}
export function decodePelvisMode(mode){
 if(mode==='off')return {harmonics:0,gain:0};
 if(mode==='tilt4')return {harmonics:4,gain:1};
 if(mode==='tilt12')return {harmonics:12,gain:1};
 if(mode==='tilt12-half')return {harmonics:12,gain:.5};
 throw Error('UNAUTHORIZED_PELVIS_MODE_'+String(mode));
}
