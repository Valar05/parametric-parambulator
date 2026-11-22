/* v0.1.20: Stable forward-facing local knee poles and source ankle trajectory have
 * authority. Contact physics may adjust an ankle only inside the anatomical
 * source-knee envelope. NO previous-frame knee, radial smoothing, post-solve
 * centerline projection, or skinned witness error feedback into thigh/shin IK.
 * A conflict is evidence, not permission to silently contort a leg. */
import {kneeFromTarget} from './ik-core.mjs';
// Per the owner: the poles remain stationary in character-local space, well
// ANTERIOR (+Z), and never follow an animated foot, knee, or prior frame.
// Asymmetry is fitted to the original 60-frame Walking_Woman knee witnesses.
export const STABLE_LOCAL_POLES=Object.freeze({left:Object.freeze([-.20,-.05,.90]),right:Object.freeze([.10,.15,.90])});
export function stableForwardPole(side,pelvisYaw){
 const p=STABLE_LOCAL_POLES[side];if(!p||!Number.isFinite(pelvisYaw))throw Error('STABLE_FORWARD_POLE_INVALID');
 const c=Math.cos(pelvisYaw),s=Math.sin(pelvisYaw);
 return [p[0]*c+p[2]*s,p[1],-p[0]*s+p[2]*c];
}
const sub=(a,b)=>a.map((v,i)=>v-b[i]);
const add=(a,b)=>a.map((v,i)=>v+b[i]);
const scale=(a,n)=>a.map(v=>v*n);
const norm=a=>Math.hypot(...a);
const lerp=(a,b,t)=>a.map((v,i)=>v+(b[i]-v)*t);
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
function fitReach(H,A,l1,l2){
 const v=sub(A,H),d=norm(v),lo=Math.abs(l1-l2)+.0003,hi=l1+l2-.0003;
 if(!Number.isFinite(d)||d<1e-9)throw Error('SOURCE_KNEE_ZERO_REACH');
 return add(H,scale(v,clamp(d,lo,hi)/d));
}
export function chooseSourceKnee({hip,sourceHip,sourceKnee,sourceAnkle,contactAnkle,pole,
 upperLength,lowerLength,side,centerX,maxKneeDeviation=.025,minSideClearance=.012}){
 const positions=[hip,sourceHip,sourceKnee,sourceAnkle,contactAnkle,pole];
 if(!positions.every(a=>Array.isArray(a)&&a.length===3&&a.every(Number.isFinite))||
   ![upperLength,lowerLength,centerX,maxKneeDeviation,minSideClearance].every(Number.isFinite)||
   upperLength<=0||lowerLength<=0||maxKneeDeviation<=0|| !['left','right'].includes(side))
   throw Error('SOURCE_KNEE_GOVERNOR_BAD_INPUT');
 const sign=side==='left'?1:-1;
 const expectedAnkle=fitReach(hip,add(hip,sub(sourceAnkle,sourceHip)),upperLength,lowerLength);
 const expectedKnee=add(hip,sub(sourceKnee,sourceHip));
 const requestedDelta=norm(sub(contactAnkle,expectedAnkle));
 const calc=t=>{
  const A=fitReach(hip,lerp(expectedAnkle,contactAnkle,t),upperLength,lowerLength);
  const K=kneeFromTarget(hip,A,upperLength,lowerLength,pole);
  const error=norm(sub(K,expectedKnee)),signed=sign*(K[0]-centerX);
  return {ankle:A,knee:K,kneeSourceError:error,signedKneeClearance:signed,
   valid:error<=maxKneeDeviation&&signed>=minSideClearance};
 };
 let best=calc(0);
 // Baseline reconstruction itself should not fail just because a foot is planted.
 // Report the source/rig discrepancy, but do not make a visually catastrophic
 // discontinuous decision using the previous physical frame.
 const baselineMismatch=!best.valid;
 if(!baselineMismatch){
  const full=calc(1);
  if(full.valid){best=full;best.acceptedFraction=1;}
  else{
   let lo=0,hi=1;
   for(let i=0;i<18;i++){
    const mid=(lo+hi)*.5,next=calc(mid);
    if(next.valid){lo=mid;best=next;}else hi=mid;
   }
   best.acceptedFraction=lo;
  }
 }else best.acceptedFraction=0;
 return {...best,baselineMismatch,requestedContactDelta:requestedDelta,
  unfulfilledContactDelta:norm(sub(contactAnkle,best.ankle)),
  sourceKnee:expectedKnee};
}
