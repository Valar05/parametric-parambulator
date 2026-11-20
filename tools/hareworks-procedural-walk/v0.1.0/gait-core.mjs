/* Hareworks procedural gait v0.1.0: deterministic, renderer-independent kinematics. */
export const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
export const wrap=a=>Math.atan2(Math.sin(a),Math.cos(a));
export const shortest=(to,from)=>wrap(to-from);
export const smooth=t=>{t=clamp(t,0,1);return t*t*(3-2*t)};
export const add=(a,b)=>[a[0]+b[0],a[1]+b[1],a[2]+b[2]];
export const sub=(a,b)=>[a[0]-b[0],a[1]-b[1],a[2]-b[2]];
export const scale=(a,s)=>a.map(v=>v*s);
export const lengthXZ=a=>Math.hypot(a[0],a[2]);
export const distXZ=(a,b)=>lengthXZ(sub(a,b));
export const yawOf=(v)=>Math.atan2(v[0],v[2]);
export function rotateY(v,a){const c=Math.cos(a),s=Math.sin(a);return [v[0]*c+v[2]*s,v[1],v[2]*c-v[0]*s]}
export function landing(root,rest,yaw,velocity,lead,groundY){const offset=rotateY(rest,yaw);return [root[0]+offset[0]+velocity[0]*lead,groundY,root[2]+offset[2]+velocity[2]*lead]}
export function swing(start,end,u,lift){const k=smooth(u);return [start[0]+(end[0]-start[0])*k,start[1]+(end[1]-start[1])*k+lift*Math.sin(Math.PI*clamp(u,0,1))**1.2,start[2]+(end[2]-start[2])*k]}
export function chooseFoot(leftError,rightError,last,turnDirection=0){if(turnDirection>0.001)return 'left';if(turnDirection< -0.001)return 'right';if(Math.abs(leftError-rightError)<.035)return last==='left'?'right':'left';return leftError>rightError?'left':'right'}
export function targetHeading(bodyYaw,aimYaw,budget){const d=shortest(aimYaw,bodyYaw);return {twist:clamp(d,-budget,budget),excess:d-clamp(d,-budget,budget)}}
export function headingStep(bodyYaw,target,maxRate,dt){return wrap(bodyYaw+clamp(shortest(target,bodyYaw),-maxRate*dt,maxRate*dt))}
export const DEFAULTS={speed:.84,stepLead:.24,stepDuration:.43,footLift:.13,reach:.35,turnRate:1.15,aimTwistBudget:Math.PI/5,actorTurnRate:.8};
