/* Hareworks v0.1.26: source-derived LEFT contact, never a generic forward-walk strafe.
 * The real Cautious_Crouch_Walk_Left clip supplies actual traveling foot trajectories.
 * Source is calibration only; generated rig is solved procedurally each frame. */
export const mod1=v=>((v%1)+1)%1;
export const distance=(a,b)=>Math.hypot(...a.map((v,i)=>v-b[i]));
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const dot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0);
const sub=(a,b)=>a.map((v,i)=>v-b[i]);
const add=(a,b)=>a.map((v,i)=>v+b[i]);
const scale=(a,s)=>a.map(v=>v*s);
export function sourceContactWindow(points,duration){
 const n=points?.length;
 if(!Number.isInteger(n)||n<120||!(duration>.1)||points.some(p=>!p||!Array.isArray(p.ankle)||p.ankle.length!==3||!p.ankle.every(Number.isFinite)))throw Error('LEFT_SOURCE_CONTACT_INVALID');
 const Y=points.map(p=>p.ankle[1]),X=points.map(p=>p.ankle[0]),bottom=Math.min(...Y),dt=duration/n;
 const vx=points.map((p,i)=>{let a=X[(i-1+n)%n],b=X[(i+1)%n];return (b-a)/(2*dt)});
 // Avoid the source clip's documented terminal root teleport in differentiation.
 for(let i=Math.floor(n*.93);i<n;i++)vx[i]=NaN;
 const runs=(mask)=>{let result=[];for(let i=0;i<n;i++){if(!mask[i]||mask[(i-1+n)%n])continue;let k=0;while(k<n&&mask[(i+k)%n])k++;result.push({start:i/n,duty:k/n,frames:k});}return result;};
 let best=null,method='ANALYTIC_SOURCE_GROUND_VELOCITY';
 for(let height of [.035,.06,.09,.13]){for(let threshold of [.25,.45,.7,1.05]){
   let candidates=runs(points.map((_,i)=>Y[i]-bottom<=height&&Math.abs(vx[i])<=threshold));
   let eligible=candidates.filter(x=>x.duty>=.25&&x.duty<=.75).sort((a,b)=>b.frames-a.frames);
   if(eligible.length){let candidate=eligible[0];if(!best||candidate.frames>best.frames)best={...candidate,height,velocityThreshold:threshold};}
 }}
 if(!best){
   // Still derive timing from the actual left clip, NEVER infer it from Walking_Woman.
   method='SOURCE_HEIGHT_FALLBACK__CONTACT_UNVERIFIED';let lo=Y.map(y=>y-bottom<=.055),candidates=runs(lo).sort((a,b)=>b.frames-a.frames);
   best=candidates[0]||null;
   if(!best||best.duty<.15){
     const k=Y.indexOf(bottom);best={start:mod1(k/n-.25),duty:.50,frames:Math.round(n*.5)};
     method='SOURCE_HEIGHT_MINIMUM_TIMING__NO_CONTACT_PROOF';
   }
   best={...best,height:.055,velocityThreshold:null};
 }
 return {start:best.start,duty:best.duty,frames:best.frames,method,minAnkleY:bottom,sourceClip:'Cautious_Crouch_Walk_Left',velocityThreshold:best.velocityThreshold,heightThreshold:best.height};
}
export function isSourcePlanted(q,window){return mod1(q-window.start)<window.duty;}
export function projectedSourceKnee(hip,knee,ankle,desired){
 for(let p of [hip,knee,ankle,desired])if(!Array.isArray(p)||p.length!==3||p.some(v=>!Number.isFinite(v)))throw Error('LEFT_IK_BAD_VECTOR');
 const l1=distance(hip,knee),l2=distance(knee,ankle),v=sub(desired,hip),d=Math.hypot(...v);
 if(!(l1>.12&&l2>.12&&d>Math.abs(l1-l2)+.0001&&d<l1+l2-.0001))return {valid:false,reason:'REACH',reach:d,maxReach:l1+l2};
 const u=scale(v,1/d),a=(l1*l1-l2*l2+d*d)/(2*d),radius=Math.sqrt(Math.max(0,l1*l1-a*a));
 const known=sub(knee,hip),normal=sub(known,scale(u,dot(known,u))),length=Math.hypot(...normal);
 if(length<.0001)return {valid:false,reason:'POLE_SINGULAR'};
 const K=add(add(hip,scale(u,a)),scale(normal,radius/length));
 return {valid:true,knee:K,upperLength:l1,lowerLength:l2,sourceKneeDisplacement:distance(K,knee)};
}
export function targetTravelX({totalPhase,travelPerCycle,speed}){
 if(!Number.isFinite(totalPhase)||!Number.isFinite(travelPerCycle)||!Number.isFinite(speed)||travelPerCycle<.5||speed<0)throw Error('LEFT_WORLD_TRAVEL_INVALID');
 return totalPhase*travelPerCycle;
}
export function travelPhaseRate(speed,sourceTravelPerCycle){
 if(!Number.isFinite(speed)||!Number.isFinite(sourceTravelPerCycle)||speed<0||sourceTravelPerCycle<.5)throw Error('LEFT_RATE_INVALID');
 return speed/sourceTravelPerCycle;
}
