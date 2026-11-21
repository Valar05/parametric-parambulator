/* Hareworks v0.1.12: source-measured task-space trajectory and hybrid contact scheduler.
   No source joint rotations drive the generated character. No generic swing sine. */
export const phase01 = q => ((q % 1) + 1) % 1;
const clamp = (v,a,b) => Math.max(a,Math.min(b,v));
const interp = (a,b,t) => a.map((x,i) => x + (b[i]-x)*t);
const add = (a,b) => a.map((x,i) => x+b[i]);
const sub = (a,b) => a.map((x,i) => x-b[i]);
const mul = (a,t) => a.map(x => x*t);
const finite3 = a => Array.isArray(a)&&a.length===3&&a.every(Number.isFinite);
export function sourceAt(samples,phase){
  const n=samples.length;if(n<60)throw Error('GAIT_SOURCE_TOO_SHORT');
  const x=phase01(phase)*n,i=Math.floor(x),t=x-i;
  const at=j=>samples[(j+n)%n],p0=at(i-1),p1=at(i),p2=at(i+1),p3=at(i+2);
  const spline=(name)=>p1[name].map((_,k)=>{
    const a=p0[name][k],b=p1[name][k],c=p2[name][k],d=p3[name][k];
    return .5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t);
  });
  return {phase:phase01(phase),ankle:spline('ankle'),heel:spline('heel'),sole:spline('sole'),toe:spline('toe'),
    q0:p1.q,q1:p2.q,qt:t};
}
const wrapDelta=(v,start)=>phase01(v-start);
export function inferContacts(samples){
  if(!Array.isArray(samples)||samples.length<180||samples.some(s=>!['ankle','heel','sole','toe'].every(k=>finite3(s[k]))||!Array.isArray(s.q)||s.q.length!==4||!s.q.every(Number.isFinite)))throw Error('INVALID_MEASURED_RIG_SAMPLES');
  const n=samples.length,low=samples.map(s=>Math.min(s.heel[1],s.toe[1])),mn=Math.min(...low),mx=Math.max(...low),span=mx-mn;
  if(span<.008)throw Error('INSUFFICIENT_SOURCE_FOOT_CLEARANCE');
  let best=null;
  // Evaluate real height contours. The duty emerges from source samples, never fixed at 55/60%.
  for(const fraction of [.10,.14,.18,.22,.28,.34,.40]){
    const threshold=mn+Math.max(.006,span*fraction),under=low.map(h=>h<=threshold);
    let runs=[];
    for(let i=0;i<n;i++){
      if(!under[i]||under[(i-1+n)%n])continue;
      let len=0;while(len<n&&under[(i+len)%n])len++;
      runs.push({startIndex:i,count:len,duty:len/n,threshold,fraction});
    }
    for(const run of runs){
      if(run.duty<.30||run.duty>.79)continue;
      const avg=Array.from({length:run.count},(_,k)=>low[(run.startIndex+k)%n]).reduce((a,b)=>a+b,0)/run.count;
      const score=avg-mn + Math.abs(run.duty-.53)*span*.05+fraction*span*.04;
      if(!best||score<best.score)best={...run,score};
    }
  }
  if(!best)throw Error('CONTACT_INFERENCE_AMBIGUOUS__CHECK_SOURCE_AND_GROUND');
  return {start:best.startIndex/n,duty:best.duty,threshold:best.threshold,sourceHeightRange:span,
    lowHeight:mn,method:'continuous skinned heel/toe low-height episode, adaptive threshold',confidence:'kinematic inference, not force sensing'};
}
export function supportMode(sample,ground){
  const heel=sample.heel[1]-ground,toe=sample.toe[1]-ground,delta=heel-toe;
  const threshold=Math.max(.008,Math.min(.024,Math.abs(heel)+Math.abs(toe))*.20);
  return delta < -threshold?'heel': delta > threshold?'toe':'sole';
}
export function swingResidual(samples,gait,phase){
  const u=clamp((wrapDelta(phase,gait.start)-gait.duty)/(1-gait.duty),0,1);
  const liftoff=sourceAt(samples,gait.start+gait.duty),touchdown=sourceAt(samples,gait.start),now=sourceAt(samples,phase);
  return sub(now.ankle,interp(liftoff.ankle,touchdown.ankle,u));
}
export class SourceFootContact{
  constructor({samples,gait,sourceGround,groundY=0,readWitness}){
    this.samples=samples;this.gait=gait;this.sourceGround=sourceGround;this.groundY=groundY;
    this.readWitness=readWitness;this.state='initial';this.pivot='sole';this.anchor=null;
    this.swingFrom=null;this.swingTo=null;this.transitions=0;this.pivotTransitions=0;
  }
  step({phase,worldZ,stride}){
    const s=sourceAt(this.samples,phase),p=wrapDelta(phase,this.gait.start),planted=p<this.gait.duty;
    const nextState=planted?'stance':'swing';let pivot=planted?supportMode(s,this.sourceGround):'air';
    // A contact rolls heel -> sole -> toe, never backwards within one plant.
    if(planted&&this.state==='stance'){
      const order={heel:0,sole:1,toe:2};
      if(order[pivot]<order[this.pivot])pivot=this.pivot;
    }
    if(nextState!==this.state){
      if(planted){this.pivot=pivot;this.anchor=this.readWitness(pivot).slice();this.anchor[1]=this.groundY;}
      else{
        const currentAnkle=this.readWitness('ankle').slice();
        this.swingFrom=currentAnkle;
        const landing=sourceAt(this.samples,this.gait.start).ankle;
        const phaseLeft=1-p;
        this.swingTo=[landing[0],landing[1]-this.sourceGround+this.groundY,landing[2]+worldZ+stride*phaseLeft];
        if(this.state==='initial'){
          // Starting mid-swing must not teleport to the interpolated late-swing pose.
          const u=clamp((p-this.gait.duty)/(1-this.gait.duty),0,.995),r=swingResidual(this.samples,this.gait,phase);
          this.swingFrom=mul(sub(sub(currentAnkle,r),mul(this.swingTo,u)),1/(1-u));
        }
      }
      this.state=nextState;this.transitions++;
    }else if(planted&&pivot!==this.pivot){
      // Heel -> full sole -> toe: transfer the physical pivot at the existing skinned witness.
      this.pivot=pivot;this.anchor=this.readWitness(pivot).slice();this.anchor[1]=this.groundY;this.pivotTransitions++;
    }
    let ankleTarget;
    if(planted){
      const sourcePivot=s[this.pivot];
      ankleTarget=sub(this.anchor,sub(sourcePivot,s.ankle));
    }else{
      const u=clamp((p-this.gait.duty)/(1-this.gait.duty),0,1);
      if(!this.swingFrom||!this.swingTo)throw Error('MISSING_SWING_ENDPOINT');
      ankleTarget=add(interp(this.swingFrom,this.swingTo,u),swingResidual(this.samples,this.gait,phase));
    }
    if(!finite3(ankleTarget))throw Error('NONFINITE_SOURCE_IK_TARGET');
    return {ankleTarget,planted,pivot,anchor:this.anchor?.slice()||null,source:s,
      witnessTarget:planted?this.anchor.slice():ankleTarget.slice(),transitions:this.transitions,pivotTransitions:this.pivotTransitions};
  }
}
