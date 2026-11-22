/* Hareworks 0.1.13: phase-independent, continuous contact target projection.
   Swing is the already-accepted source-fitted path with boundary corrections,
   not a new generic sine/smoothstep gait. */
import {phase01,clamp,gap,inside} from './root-motion.mjs';
const add=(a,b)=>a.map((x,i)=>x+b[i]),sub=(a,b)=>a.map((x,i)=>x-b[i]),scale=(a,n)=>a.map(x=>x*n);
const mix=(a,b,t)=>a.map((x,i)=>x+(b[i]-x)*t);
const finite=a=>Array.isArray(a)&&a.length===3&&a.every(Number.isFinite);
export function sourceAt(samples,q){
 const n=samples.length;if(n<60)throw Error('SOURCE_SAMPLES_INSUFFICIENT');
 const x=phase01(q)*n,i=Math.floor(x),t=x-i;
 const at=j=>samples[(j+n)%n],p0=at(i-1),p1=at(i),p2=at(i+1),p3=at(i+2);
 const sample=name=>p1[name].map((_,k)=>{
  const a=p0[name][k],b=p1[name][k],c=p2[name][k],d=p3[name][k];
  return .5*(2*b+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t);
 });
 return {phase:phase01(q),ankle:sample('ankle'),hip:sample('hip'),knee:sample('knee'),
  heel:sample('heel'),sole:sample('sole'),toe:sample('toe'),q0:p1.q,q1:p2.q,qt:t};
}
export function supportMode(s,ground){
 const heel=s.heel[1]-ground,toe=s.toe[1]-ground;
 const th=Math.max(.007,Math.min(.020,(Math.abs(heel)+Math.abs(toe))*.16));
 return heel-toe < -th?'heel':heel-toe>th?'toe':'sole';
}
export class SourceFootContact{
 constructor({samples,gait,sourceGround,readWitness,rootAt,groundY=0,transformSource=null,terrainAt=null}){
  if(!gait||!Number.isFinite(gait.start)||!(gait.duty>.45&&gait.duty<.73))throw Error('INVALID_SOURCE_STANCE_WINDOW');
  this.samples=samples;this.gait=gait;this.sourceGround=sourceGround;this.groundY=groundY;
  this.readWitness=readWitness;this.rootAt=rootAt;this.transformSource=transformSource;this.terrainAt=terrainAt;this.activeDuty=gait.duty;
  this.state='initial';this.pivot='sole';this.anchor=null;this.transitions=0;this.pivotTransitions=0;
  this.swingCorrection=[0,0,0];this.badAnchorHeight=0;this.contactJump=0;
 }
 captureAnchor(kind){
  const anchor=this.readWitness(kind).slice();
  if(this.terrainAt)anchor[1]=this.terrainAt(anchor[0],anchor[2]);
  if(!finite(anchor))throw Error('TERRAIN_CONTACT_ANCHOR_INVALID');
  return anchor;
 }
 step({phase,worldZ,totalPhase,gait}){
  const p=gap(phase,this.gait.start);
  if(this.state!=='stance'&&p<Math.min(this.gait.duty,this.activeDuty))
   this.activeDuty=clamp(this.gait.duty+((gait?.stanceDuty??.60)-.60),.49,.69);
  const planted=p<this.activeDuty;
  const raw=sourceAt(this.samples,phase),s=this.transformSource?this.transformSource(raw,gait,planted):raw;
  const next=planted?'stance':'swing';let pivot=planted?supportMode(s,this.sourceGround):'air';
  if(planted&&this.state==='stance'){
   const order={heel:0,sole:1,toe:2};
   if(order[pivot]<order[this.pivot])pivot=this.pivot;
  }
  const baseline=add(s.ankle,[0,-this.sourceGround,worldZ]);
  if(this.terrainAt)baseline[1]+=this.terrainAt(baseline[0],baseline[2]);
  if(next!==this.state){
   if(planted){
    this.pivot=pivot;this.anchor=this.captureAnchor(pivot);
    this.badAnchorHeight=Math.max(this.badAnchorHeight,Math.abs(this.anchor[1]-(this.terrainAt?this.terrainAt(this.anchor[0],this.anchor[2]):this.groundY)));
   }else{
    // Preserve the exact final solved ankle on the first swing step.
    this.swingCorrection=sub(this.readWitness('ankle'),baseline);
   }
   this.state=next;this.transitions++;
  }else if(planted&&pivot!==this.pivot){
   // Physically transfer support without teleporting the ankle or projecting an anchor to Y=0.
   this.pivot=pivot;this.anchor=this.captureAnchor(pivot);
   this.badAnchorHeight=Math.max(this.badAnchorHeight,Math.abs(this.anchor[1]-(this.terrainAt?this.terrainAt(this.anchor[0],this.anchor[2]):this.groundY)));
   this.pivotTransitions++;
  }
  let target;
  if(planted){
   target=sub(this.anchor,sub(s[this.pivot],s.ankle));
  }else{
   const u=clamp((p-this.activeDuty)/(1-this.activeDuty),0,1),blend=(1-u)*(1-u)*(1+2*u);
   target=add(baseline,scale(this.swingCorrection,blend));
  }
  if(!finite(target))throw Error('NONFINITE_SOURCE_FOOT_TARGET');
  return {ankleTarget:target,planted,pivot,anchor:this.anchor?.slice()||null,source:s,
   witnessTarget:planted?this.anchor.slice():target.slice(),transitions:this.transitions,
   pivotTransitions:this.pivotTransitions,badAnchorHeight:this.badAnchorHeight};
 }
}
