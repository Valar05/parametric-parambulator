/* Hareworks v0.1.10: WORLD-SPACE contact authority, not source pose playback. */
export const mod1=x=>((x%1)+1)%1;
export const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
export const smooth=x=>{const t=clamp(x,0,1);return t*t*(3-2*t)};
export const mix=(a,b,t)=>a.map((v,i)=>v*(1-t)+b[i]*t);
export function forwardPhase(q,start){return mod1(q-start)}
export function stanceAt(q,start,duty){if(!(duty>.1&&duty<.85))throw Error('BAD_STANCE_DUTY');return forwardPhase(q,start)<duty}
export function swingProgress(q,start,duty){const s=forwardPhase(q,start);return clamp((s-duty)/(1-duty),0,1)}
export function swingPoint(from,to,progress,lift){const s=smooth(progress),v=mix(from,to,s);v[1]+=Math.sin(Math.PI*clamp(progress,0,1))*lift;return v}
export function nextStartDelta(q,start){const p=mod1(start-q);return p<1e-10?1:p}
export function followCamera(root,offset,focusHeight=.9){if(root.length!==3||offset.length!==3||![...root,...offset,focusHeight].every(Number.isFinite))throw Error('BAD_CAMERA_FOLLOW');return {position:[root[0]+offset[0],root[1]+focusHeight+offset[1],root[2]+offset[2]],target:[root[0],root[1]+focusHeight,root[2]]}}
// One world anchor persists for the whole stance. No source animation input.
export class WorldContact {
 constructor({side,start,duty=.55,sole,groundY}){
  if(!Array.isArray(sole)||sole.length!==3||!sole.every(Number.isFinite))throw Error('INITIAL_SOLE_INVALID');
  this.side=side;this.start=mod1(start);this.duty=duty;this.groundY=groundY;
  this.anchor=sole.slice();this.target=sole.slice();this.swingFrom=sole.slice();this.swingTo=sole.slice();
  this.isStance=stanceAt(0,this.start,this.duty);this.transitions=0;this.lastPlanted=null;
 }
 step({phase,nominalLanding,footLift=.11}){
  if(!Number.isFinite(phase)||!Array.isArray(nominalLanding)||nominalLanding.length!==3||!nominalLanding.every(Number.isFinite))throw Error('FOOT_TARGET_INVALID');
  const planted=stanceAt(phase,this.start,this.duty);
  if(planted!==this.isStance){
   if(planted){this.anchor=this.swingTo.slice();this.anchor[1]=this.groundY;this.lastPlanted=this.anchor.slice();}
   else{this.swingFrom=this.anchor.slice();this.swingTo=nominalLanding.slice();this.swingTo[1]=this.groundY;}
   this.isStance=planted;this.transitions++;
  }
  if(planted)this.target=this.anchor.slice();
  else{const u=swingProgress(phase,this.start,this.duty);this.target=swingPoint(this.swingFrom,this.swingTo,u,footLift)}
  return {target:this.target.slice(),planted,anchor:this.anchor.slice(),transitions:this.transitions};
 }
}
