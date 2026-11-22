/* Hareworks 0.1.22: true physical, easily readable longitudinal terrain.
 * The three PROFILE_* surfaces are extruded identically across X.
 * One analytic height drives visible geometry and the physical IK/test surface.
 * Older v0.1.21 surfaces and flat controls remain available unchanged. */
export const TERRAIN_MODES=Object.freeze([
 'flat','uphill','downhill','cross-slope','rough',
 'profile-ridges','profile-steps','profile-ramp'
]);
export const isProfileTerrain=mode=>mode.startsWith('profile-');
export const validTerrain=(mode,intensity)=>TERRAIN_MODES.includes(mode)&&Number.isFinite(intensity)&&intensity>=0&&intensity<=3;
const clamp=(v,lo,hi)=>Math.min(hi,Math.max(lo,v));
const smooth=t=>{const u=clamp(t,0,1);return u*u*(3-2*u)};
const step=(z,z0,width)=>smooth((z-z0)/width);
// Cyclic step course: climb two blocks, descend two blocks; no unbounded rise.
// The 0.58-unit ramps have a finite slope and are not vertical teleportations.
function stairCourse(z){
 const t=((z-1.10)%12+12)%12;
 const safe=z>=1.10?1:0;
 return safe*(step(t,0,.58)+step(t,2.75,.58)-step(t,6.0,.58)-step(t,8.80,.58));
}
export function terrainHeight(x,z,mode='profile-ridges',intensity=1.1){
 if(!validTerrain(mode,intensity)||![x,z].every(Number.isFinite))throw Error('TERRAIN_INPUT_INVALID');
 const s=intensity;
 switch(mode){
  case 'flat':return 0;
  case 'uphill':return .085*s*z;
  case 'downhill':return -.085*s*z;
  case 'cross-slope':return .105*s*x;
  case 'rough':return s*(.026*Math.sin(2.0*z+.43*x)+.013*Math.sin(3.7*z-.81*x)+.009*(Math.cos(2.3*x+1.4*z)-1));
  case 'profile-ridges':{
   // A real heightfield with pronounced sequential obstacles, identical for both feet.
   const onset=smooth((z-.15)/.90);
   return s*onset*(.135*Math.sin(1.92*(z-.15))+.066*Math.sin(4.10*(z-.15)));
  }
  case 'profile-steps':return .205*s*stairCourse(z);
  case 'profile-ramp':return .16*s*(z>0?z:0);
 }
 throw Error('TERRAIN_MODE_UNREACHABLE');
}
export function terrainNormal(x,z,mode='profile-ridges',intensity=1.1){
 const e=.002;
 const dx=(terrainHeight(x+e,z,mode,intensity)-terrainHeight(x-e,z,mode,intensity))/(2*e);
 const dz=(terrainHeight(x,z+e,mode,intensity)-terrainHeight(x,z-e,mode,intensity))/(2*e);
 const length=Math.hypot(dx,1,dz);
 return [-dx/length,1/length,-dz/length];
}
export function terrainBodyLift(previous,desired,dt){
 if(![previous,desired,dt].every(Number.isFinite)||dt<0||dt>.25)throw Error('TERRAIN_LIFT_INPUT_INVALID');
 // Up to 1.5 surface-units/s on hard steps; finite, bounded and continuous.
 const maxChange=1.50*dt;
 return previous+clamp(desired-previous,-maxChange,maxChange);
}
export function terrainGrid(mode='profile-ridges',intensity=1.1,centerZ=0,nx=12,nz=400){
 if(!validTerrain(mode,intensity)||!Number.isFinite(centerZ)||!Number.isInteger(nx)||!Number.isInteger(nz)||nx<2||nx>96||nz<2||nz>400)
  throw Error('TERRAIN_GRID_CONFIG_INVALID');
 const profile=isProfileTerrain(mode),start=profile?centerZ-6:centerZ-10,extent=profile?24:54;
 const halfWidth=profile?1.35:2.65,positions=[],colors=[],indices=[];
 for(let iz=0;iz<=nz;iz++){
  const z=start+iz*extent/nz;
  for(let ix=0;ix<=nx;ix++){
   const x=-halfWidth+ix*2*halfWidth/nx, y=terrainHeight(x,z,mode,intensity);
   positions.push(x,y,z);
   // No lateral striping in PROFILE modes: the silhouette is the actual height.
   const contour=.5+.5*Math.sin(10*y+1.30*z),light=.80+.16*contour;
   colors.push(.21*light,.30*light,.29*light);
  }
 }
 for(let iz=0;iz<nz;iz++)for(let ix=0;ix<nx;ix++){
  const a=iz*(nx+1)+ix,b=a+1,c=a+(nx+1),d=c+1;
  indices.push(a,c,b,b,c,d);
 }
 return {positions,colors,indices,centerZ,start,extent,halfWidth,triangles:indices.length/3};
}
export function longitudinalProfile(mode,intensity,centerZ=0,count=400){
 if(!validTerrain(mode,intensity)||!Number.isInteger(count)||count<2||count>1000)throw Error('TERRAIN_PROFILE_CONFIG_INVALID');
 const g=terrainGrid(mode,intensity,centerZ,2,Math.min(count,400));
 return Array.from({length:count+1},(_,i)=>{
  const z=g.start+i*g.extent/count;
  return {z,y:terrainHeight(0,z,mode,intensity)};
 });
}
