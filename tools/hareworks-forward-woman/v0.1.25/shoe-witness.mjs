/* v0.1.14: true skinned footwear witness selection.
 * Partition the ACTUAL whole foot surface, not an already-reduced 20-vertex sole patch.
 * Geometry and provenance reports remain owner-review evidence, never automatic acceptance.
 */
const clamp=(v,lo,hi)=>Math.max(lo,Math.min(hi,v));
const avg=(p,k)=>p.reduce((s,v)=>s+v.xyz[k],0)/p.length;
function eigenAxis(points){
 const mx=avg(points,0),mz=avg(points,2);
 let xx=0,zz=0,xz=0;
 for(const p of points){const x=p.xyz[0]-mx,z=p.xyz[2]-mz;xx+=x*x;zz+=z*z;xz+=x*z;}
 const theta=.5*Math.atan2(2*xz,xx-zz);
 return [Math.cos(theta),Math.sin(theta)];
}
function chooseBin(points,k){
 // A contact witness must represent low, physically skinned surface geometry.
 const low=points.map(p=>p.xyz[1]).sort((a,b)=>a-b);
 const cutoff=low[Math.max(0,Math.min(low.length-1,Math.floor(low.length*.45)))];
 const subset=points.filter(p=>p.xyz[1]<=cutoff+0.012);
 subset.sort((a,b)=>a.xyz[1]-b.xyz[1]||a.mi-b.mi||a.j-b.j);
 return subset.slice(0,Math.min(k,subset.length));
}
export function selectShoeWitnesses(input,rawToeDirection){
 if(!Array.isArray(input)||input.length<24)throw Error('INSUFFICIENT_SKINNED_FOOT_VERTICES_'+input?.length);
 const ids=new Set(),valid=[];
 for(const p of input){
  if(!p||!Array.isArray(p.xyz)||p.xyz.length!==3||!p.xyz.every(Number.isFinite)||!Number.isInteger(p.mi)||!Number.isInteger(p.j))continue;
  const key=p.mi+':'+p.j;if(ids.has(key))continue;ids.add(key);valid.push(p);
 }
 if(valid.length<24)throw Error('INSUFFICIENT_UNIQUE_FOOT_VERTICES_'+valid.length);
 // Restrict the PCA to the lower visible shoe surface; tall shin polygons must not drive direction.
 const bottom=Math.min(...valid.map(p=>p.xyz[1]));
 let low=valid.filter(p=>p.xyz[1]<=bottom+.13);
 if(low.length<24)low=valid.slice();
 let axis=eigenAxis(low);
 const toe=[rawToeDirection?.[0]||0,rawToeDirection?.[2]||0],td=Math.hypot(...toe);
 if(td>.012&&axis[0]*toe[0]+axis[1]*toe[1]<0)axis=axis.map(x=>-x);
 else if(td<=.012&&axis[1]<0)axis=axis.map(x=>-x);
 const points=low.map(p=>({...p,projection:p.xyz[0]*axis[0]+p.xyz[2]*axis[1]}));
 points.sort((a,b)=>a.projection-b.projection);
 const length=points.at(-1).projection-points[0].projection;
 if(length<.065)throw Error('SKINNED_SHOE_LONGITUDINAL_EXTENT_INSUFFICIENT_'+length.toFixed(5));
 // Use non-overlapping spatial bands, THEN choose lower skinned vertices WITHIN each band.
 const n=points.length;
 const lo=points.slice(0,Math.floor(n*.32)),mid=points.slice(Math.floor(n*.38),Math.ceil(n*.62)),hi=points.slice(Math.ceil(n*.68));
 const picked=[chooseBin(lo,14),chooseBin(mid,14),chooseBin(hi,14)];
 if(picked.some(p=>p.length<4))throw Error('SKINNED_SHOE_SURFACE_BAND_MISSING');
 const means=picked.map(group=>group.reduce((s,v)=>s+v.projection,0)/group.length);
 if(means[1]-means[0]<.018||means[2]-means[1]<.018)throw Error('SKINNED_SHOE_PATCH_CENTROIDS_NOT_DISTINCT_'+means.join(','));
 const patch=ps=>({indexes:ps.map(p=>({mi:p.mi,j:p.j})),count:ps.length});
 return {heel:patch(picked[0]),sole:patch(picked[1]),toe:patch(picked[2]),
   evidence:{wholeFootCandidates:valid.length,lowSurfaceCandidates:low.length,shoeLongitudinalExtent:length,
     heelSoleToeLongitudinalCentroids:means,axisXZ:axis,method:'PCA of real skinned shoe vertices in XZ; lowest vertices of independent longitudinal thirds'}};
}
