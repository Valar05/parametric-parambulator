/* Hareworks 0.1.13: reconstruct world-root travel by inverting the accepted ankle trajectory.
   Phase is a complete LEFT+RIGHT gait cycle, not the movement of one ankle.
   No source animation tracks run on the visible actor. */
export const phase01=q=>((q%1)+1)%1;
export const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
export const smooth01=x=>{const t=clamp(x,0,1);return t*t*(3-2*t)};
export const gap=(q,start)=>phase01(q-start);
export const inside=(q,g)=>gap(q,g.start)<g.duty;
const v3=v=>Array.isArray(v)&&v.length===3&&v.every(Number.isFinite);
const st=(a,i)=>a[(i%a.length+a.length)%a.length];
export function derivative(samples,i,kind='ankle',component=2){
 const n=samples.length;
 return (st(samples,i+1)[kind][component]-st(samples,i-1)[kind][component])*n/2;
}
function contiguous(mask){
 const n=mask.length,out=[];
 for(let i=0;i<n;i++){
  if(!mask[i]||mask[(i-1+n)%n])continue;
  let length=0;while(length<n&&mask[(i+length)%n])length++;
  out.push({start:i/n,duty:length/n,count:length});
 }
 return out;
}
export function inferVelocityContact(samples){
 if(!Array.isArray(samples)||samples.length<60||samples.some(s=>!v3(s.ankle)||!v3(s.heel)||!v3(s.sole)||!v3(s.toe)))throw Error('SOURCE_WITNESS_SCHEMA_INVALID');
 const n=samples.length,v=samples.map((_,i)=>derivative(samples,i));
 const low=Math.min(...v),cut=Math.min(-.25,low*.22),runs=contiguous(v.map(z=>z<cut));
 const ranges=runs.filter(g=>g.duty>=.47&&g.duty<=.70);
 if(!ranges.length)throw Error('SOURCE_CONTACT_VELOCITY_AMBIGUOUS '+JSON.stringify({minVelocity:low,threshold:cut,runs}));
 ranges.sort((a,b)=>b.duty-a.duty);
 const g=ranges[0];
 const floor=Math.min(...samples.flatMap(s=>[s.heel[1],s.toe[1]]));
 const supportHeights=[];const swingHeights=[];
 for(let i=0;i<n;i++){
  const h=Math.min(samples[i].heel[1],samples[i].toe[1])-floor;
  (inside(i/n,g)?supportHeights:swingHeights).push(h);
 }
 const mean=x=>x.reduce((a,b)=>a+b,0)/x.length;
 return {...g,method:'circular backward-ankle velocity, with independent heel/toe height diagnostics',
  thresholdVelocity:cut,sourceMinDerivative:low,meanContactHeight:mean(supportHeights),meanSwingHeight:mean(swingHeights),
  groundCandidate:floor,confidence:'kinematic window only; physical skinned witness audit required'};
}
export function buildRootCurve(feet,gaits){
 const n=feet.left.length;
 if(n<60||feet.right.length!==n)throw Error('ROOT_SAMPLE_COUNT_MISMATCH');
 const speeds=[];
 for(let i=0;i<=n;i++){
  const q=i/n,vs=['left','right'].map(side=>derivative(feet[side],i)),weights=['left','right'].map((side,j)=>{
   const g=gaits[side],u=gap(q,g.start),edge=Math.min(u,g.duty-u),window=inside(q,g)?(.12+.88*smooth01(edge/.035)):0;
   return window*smooth01((-vs[j]-.22)/.75);
  });
  if(weights[0]+weights[1]<1e-10){
   const candidate=vs[0]<vs[1]?0:1;
   weights[candidate]=1;
  }
  speeds.push(-(vs[0]*weights[0]+vs[1]*weights[1])/(weights[0]+weights[1]));
 }
 // Periodicity is required for a seamless cycle; the terminal derivative equals the first.
 speeds[n]=speeds[0];
 if(speeds.some(v=>!Number.isFinite(v)||v<-.1||v>5))throw Error('ROOT_VELOCITY_NONPHYSICAL');
 const positions=[0];for(let i=1;i<=n;i++)positions.push(positions[i-1]+(speeds[i-1]+speeds[i])/(2*n));
 const stride=positions[n];
 if(!(stride>.9&&stride<1.55))throw Error('ROOT_STRIDE_OUTSIDE_MEASURED_BIPED_RANGE '+stride);
 return {schema:'hareworks-accepted-v019-inverted-support-root-v0.1.14',n,speeds,positions,stride,
  method:'integral of negative fitted stance-ankle phase velocity; double support weighted by measured backward velocity',
  sourceFootSampleCount:n,ownerVisualAcceptance:false};
}
export function rootAt(curve,totalPhase){
 const cycles=Math.floor(totalPhase),q=phase01(totalPhase),x=q*curve.n,i=Math.floor(x),t=x-i;
 return cycles*curve.stride+curve.positions[i]*(1-t)+curve.positions[i+1]*t;
}
export function kneeFlexion(l1,l2,hip,ankle){
 if(!v3(hip)||!v3(ankle)||!(l1>0&&l2>0))throw Error('INVALID_LEG_GEOMETRY');
 const d=Math.hypot(...hip.map((x,i)=>x-ankle[i]));
 const c=clamp((l1*l1+l2*l2-d*d)/(2*l1*l2),-1,1);
 return (Math.PI-Math.acos(c))*180/Math.PI;
}
