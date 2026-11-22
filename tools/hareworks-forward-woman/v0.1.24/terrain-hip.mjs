/* A REAL constrained pelvis-height solve against both world-fixed ankle targets.
 * Never edit a knee pole or move planted contact anchors. All units in GLB world coordinates.
 */
export const clamp=(v,a,b)=>Math.min(b,Math.max(a,v));
export function pelvisReachCorrection(hips,ankles,limits,currentLift,groundAt,dt){
 if(!['left','right'].every(s=>hips[s]?.length===3&&ankles[s]?.length===3&&limits[s]?.length===2))throw Error('HIP_REACH_PAIR_REQUIRED');
 if(![currentLift,dt].every(Number.isFinite)||dt<0)throw Error('HIP_REACH_DT_INVALID');
 let lo=-Infinity,hi=Infinity,rawTerrain=0;
 for(const side of ['left','right']){
  const H=hips[side],A=ankles[side],lengths=limits[side];
  if(![...H,...A,...lengths].every(Number.isFinite)||lengths.some(v=>v<=0))throw Error('HIP_REACH_NONFINITE');
  const lateral2=(A[0]-H[0])**2+(A[2]-H[2])**2;
  const maximum=lengths[0]+lengths[1]-.002;
  if(lateral2>=maximum**2)return {feasible:false,reason:'FOOT_OUTSIDE_HORIZONTAL_REACH_'+side,delta:0,lower:NaN,upper:NaN};
  const y= Math.sqrt(maximum**2-lateral2),center=A[1]-H[1];
  lo=Math.max(lo,center-y);hi=Math.min(hi,center+y);
  rawTerrain+=groundAt(A[0],A[2])/2;
 }
 if(!Number.isFinite(rawTerrain)||lo>hi)return {feasible:false,reason:'NO_COMMON_PELVIS_HEIGHT',delta:0,lower:lo,upper:hi};
 // Terrain under BOTH feet, not just the torso's forward Z centerline.
 // Offset is further constrained by physical two-link reach on BOTH legs.
 const desired=clamp(rawTerrain-currentLift,lo,hi);
 const rate=dt===0?.28:1.5*Math.min(dt,.1),delta=clamp(desired,-rate,rate);
 return {feasible:true,delta,desired,lower:lo,upper:hi,groundAverage:rawTerrain,rateLimited:Math.abs(desired)>rate+1e-9};
}
export function segmentTerrainPenetration(a,b,groundAt,radius=.035,samples=9){
 if(a.length!==3||b.length!==3||![...a,...b,radius].every(Number.isFinite))throw Error('LEG_TERRAIN_INPUT_INVALID');
 let maxDepth=0;
 for(let i=0;i<=samples;i++){
  const u=i/samples,x=a[0]+(b[0]-a[0])*u,z=a[2]+(b[2]-a[2])*u,y=a[1]+(b[1]-a[1])*u;
  maxDepth=Math.max(maxDepth,groundAt(x,z)-(y-radius));
 }
 return maxDepth;
}
