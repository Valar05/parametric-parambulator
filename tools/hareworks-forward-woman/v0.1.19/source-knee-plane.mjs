/* Hareworks v0.1.19: original source knee is the IK bending-plane authority.
 * Distal foot heading never enters this solver. Real two-bone lengths and
 * exact world-space ankle target remain immutable through this computation.
 * The centerline boundary applies in character +X (left) / -X (right),
 * using the actual midpoint between the world-space hip joints.
 */
const sub=(a,b)=>a.map((x,i)=>x-b[i]);
const add=(a,b)=>a.map((x,i)=>x+b[i]);
const scale=(a,n)=>a.map(x=>x*n);
const dot=(a,b)=>a.reduce((v,x,i)=>v+x*b[i],0);
const norm=a=>Math.hypot(...a);
const unit=a=>{let d=norm(a);if(d<1e-10)throw Error('KNEE_PLANE_ZERO_AXIS');return scale(a,1/d)};
const clamp=(x,a,b)=>Math.max(a,Math.min(b,x));
const project=(x,u)=>sub(x,scale(u,dot(x,u)));
function enforceSide(radial,center,radius,axis,sideSign,centerX,clearance){
 const outer=project([sideSign,0,0],axis),reach=norm(outer);
 if(reach<1e-6)throw Error('KNEE_CENTERLINE_AXIS_PARALLEL');
 const out=scale(outer,1/reach),signedCenter=sideSign*(center[0]-centerX),maxSide=signedCenter+radius*reach;
 if(maxSide<clearance-1e-8)throw Error('KNEE_CENTERLINE_GEOMETRY_INFEASIBLE_'+maxSide.toFixed(6));
 const currentSide=signedCenter+radius*sideSign*radial[0];
 if(currentSide>=clearance-1e-9)return {radial,corrected:false,maxSide};
 const target=clamp((clearance-signedCenter)/(radius*reach),-1,1);
 const component=sub(radial,scale(out,dot(radial,out)));
 const tangent=norm(component)>1e-8?unit(component):unit(project([0,0,1],axis).map((v,i)=>v-dot(project([0,0,1],axis),out)*out[i]));
 const corrected=unit(add(scale(out,target),scale(tangent,Math.sqrt(Math.max(0,1-target*target)))));
 return {radial:corrected,corrected:true,maxSide};
}
export function sourceKneePlane(hip,ankle,sourceHip,sourceKnee,l1,l2,side,centerX,previousKnee=null,dt=1/120,clearance=.018){
 if(!['left','right'].includes(side)||![hip,ankle,sourceHip,sourceKnee].every(a=>Array.isArray(a)&&a.length===3&&a.every(Number.isFinite))||
  ![l1,l2,centerX,dt,clearance].every(Number.isFinite)||l1<=0||l2<=0||dt<0||clearance<0)
  throw Error('KNEE_PLANE_INPUT_INVALID');
 const sg=side==='left'?1:-1,delta=sub(ankle,hip),distance=norm(delta);
 if(!(distance<l1+l2+1e-5&&distance>Math.abs(l1-l2)+1e-5))
  throw Error('KNEE_PLANE_UNREACHABLE_'+distance.toFixed(5));
 const axis=scale(delta,1/distance),along=(l1*l1-l2*l2+distance*distance)/(2*distance),
  radius=Math.sqrt(Math.max(0,l1*l1-along*along)),center=add(hip,scale(axis,along));
 // Original knee-relative-to-hip vector is correct even though the source
 // reference rig is invisible and rooted at the world origin.
 const sourceDirection=project(sub(sourceKnee,sourceHip),axis);
 if(norm(sourceDirection)<1e-8)throw Error('KNEE_SOURCE_BEND_PLANE_DEGENERATE');
 let radial=unit(sourceDirection),corrected=false;
 if(previousKnee&&previousKnee.length===3&&previousKnee.every(Number.isFinite)&&dt>0){
  const last=project(sub(previousKnee,center),axis);
  if(norm(last)>1e-8){
   const previous=unit(last),angle=Math.acos(clamp(dot(previous,radial),-1,1));
   const maximumAngle=dt*10; // 10 rad/s: stop abrupt pole flipping, not normal walk motion
   if(angle>maximumAngle&&maximumAngle>1e-6){
    const t=maximumAngle/angle,perp=sub(radial,scale(previous,Math.cos(angle)));
    if(norm(perp)>1e-8)radial=unit(add(scale(previous,Math.cos(maximumAngle)),scale(unit(perp),Math.sin(maximumAngle))));
   }
  }
 }
 // Guard applies AFTER continuity damping, never by moving the planted foot.
 if(radius>.0005){const out=enforceSide(radial,center,radius,axis,sg,centerX,clearance);radial=out.radial;corrected=out.corrected;}
 else if(sg*(center[0]-centerX)<clearance-1e-8)throw Error('KNEE_STRAIGHT_LEG_CENTERLINE_INFEASIBLE');
 const knee=add(center,scale(radial,radius));
 const signed=sg*(knee[0]-centerX);
 if(signed<clearance-2e-6)throw Error('KNEE_CROSSED_CENTERLINE_'+side+'_'+signed.toFixed(6));
 const sourcePoint=add(hip,sub(sourceKnee,sourceHip));
 return {knee,sideClearance:signed,centerlineCorrected:corrected,
  sourceKneeDisplacement:norm(sub(knee,sourcePoint)),sourceKnee:sourcePoint,
  hipToKnee:Math.abs(norm(sub(knee,hip))-l1),kneeToAnkle:Math.abs(norm(sub(knee,ankle))-l2)};
}
