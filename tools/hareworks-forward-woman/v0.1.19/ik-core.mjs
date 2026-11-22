/* True world-space two-segment inverse kinematics, no animation-pose lookup. */
const add=(a,b)=>a.map((x,i)=>x+b[i]);
const sub=(a,b)=>a.map((x,i)=>x-b[i]);
const scale=(v,s)=>v.map(x=>x*s);
const dot=(a,b)=>a.reduce((s,x,i)=>s+x*b[i],0);
const norm=a=>Math.hypot(...a);
export function kneeFromTarget(hip,ankle,l1,l2,pole,eps=1e-5){
 if(![l1,l2].every(x=>Number.isFinite(x)&&x>0)||![hip,ankle,pole].every(a=>Array.isArray(a)&&a.length===3&&a.every(Number.isFinite)))throw Error('INVALID_WORLD_IK_INPUT');
 const axis=sub(ankle,hip),distance=norm(axis),limit=l1+l2;
 if(!(distance<limit+eps&&distance>Math.abs(l1-l2)+eps))throw Error('UNREACHABLE_WORLD_IK_'+distance.toFixed(6)+'_MAX_'+limit.toFixed(6));
 const u=scale(axis,1/distance),along=(l1*l1-l2*l2+distance*distance)/(2*distance),height=Math.sqrt(Math.max(0,l1*l1-along*along));
 const planar=sub(pole,scale(u,dot(pole,u))),p=norm(planar);
 if(p<1e-6)throw Error('IK_POLE_SINGULAR');
 return add(add(hip,scale(u,along)),scale(planar,height/p));
}
