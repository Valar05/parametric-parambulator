/* Hareworks v0.1.21. The SAME deterministic height function drives visible
 * terrain triangles, world-space touchdown anchors, pelvis elevation and the
 * heel/sole/toe terrain clearance audit. No randomized scene-only bumps. */
export const TERRAIN_MODES=Object.freeze(['flat','uphill','downhill','cross-slope','rough']);
export const validTerrain=(mode,intensity)=>TERRAIN_MODES.includes(mode)&&Number.isFinite(intensity)&&intensity>=0&&intensity<=1.25;
export function terrainHeight(x,z,mode='flat',intensity=.65){
 if(!validTerrain(mode,intensity)||![x,z].every(Number.isFinite))throw Error('TERRAIN_INPUT_INVALID');
 const s=intensity;
 switch(mode){
  case 'flat':return 0;
  case 'uphill':return .085*s*z;
  case 'downhill':return -.085*s*z;
  case 'cross-slope':return .105*s*x;
  case 'rough':return s*(.026*Math.sin(2.0*z+.43*x)+.013*Math.sin(3.7*z-.81*x)+.009*(Math.cos(2.3*x+1.4*z)-1));
 }
 throw Error('TERRAIN_UNREACHABLE');
}
export function terrainNormal(x,z,mode='flat',intensity=.65){
 const e=.002;
 const dx=(terrainHeight(x+e,z,mode,intensity)-terrainHeight(x-e,z,mode,intensity))/(2*e),
       dz=(terrainHeight(x,z+e,mode,intensity)-terrainHeight(x,z-e,mode,intensity))/(2*e);
 const d=Math.hypot(dx,1,dz);
 return [-dx/d,1/d,-dz/d];
}
export function terrainBodyLift(previous,desired,dt){
 if(![previous,desired,dt].every(Number.isFinite)||dt<0||dt>.25)throw Error('TERRAIN_LIFT_INPUT_INVALID');
 const maxChange=.40*dt;
 return previous+Math.max(-maxChange,Math.min(maxChange,desired-previous));
}
export function terrainGrid(mode='rough',intensity=.65,centerZ=0,nx=24,nz=176){
 if(!validTerrain(mode,intensity)||!Number.isFinite(centerZ)||!Number.isInteger(nx)||!Number.isInteger(nz)||nx<2||nx>96||nz<2||nz>400)
  throw Error('TERRAIN_GRID_CONFIG_INVALID');
 const positions=[],colors=[],indices=[];
 for(let iz=0;iz<=nz;iz++){
  const z=centerZ-10+iz*54/nz;
  for(let ix=0;ix<=nx;ix++){
   const x=-2.65+ix*5.30/nx, y=terrainHeight(x,z,mode,intensity);
   positions.push(x,y,z);
   const contour=.5+.5*Math.sin(9.0*y+2.1*x),light=.86+.12*contour;
   colors.push(.23*light,.33*light,.30*light);
  }
 }
 for(let iz=0;iz<nz;iz++)for(let ix=0;ix<nx;ix++){
  const a=iz*(nx+1)+ix,b=a+1,c=a+(nx+1),d=c+1;
  indices.push(a,c,b,b,c,d);
 }
 return {positions,colors,indices,centerZ,triangles:indices.length/3};
}
