#!/usr/bin/env python3
"""Strict source-blob-pinned recovery of v0.1.13, into immutable v0.1.14 only."""
from pathlib import Path
import json,sys
root=Path(sys.argv[1]).resolve()
target=root/'tools/hareworks-forward-woman/v0.1.14'
p=target/'viewer.mjs'
s=p.read_text()
def once(old,new):
 global s
 if s.count(old)!=1:raise RuntimeError('PATCH_ANCHOR_COUNT_'+str(s.count(old))+' '+old[:90])
 s=s.replace(old,new,1)
def region(first,end,replacement):
 global s
 if s.count(first)!=1 or s.count(end)!=1:raise RuntimeError('PATCH_REGION_NOT_UNIQUE '+first[:40])
 a=s.index(first);b=s.index(end,a)
 s=s[:a]+replacement+s[b:]
# Preserve every accepted gait curve, the phase-integrated inverse root, original camera orbit and contact core.
once("import {OrbitControls} from 'three/addons/controls/OrbitControls.js';", "import {OrbitControls} from 'three/addons/controls/OrbitControls.js';\nimport {selectShoeWitnesses} from './shoe-witness.mjs';")
region('function splitFootPatches(meshes,foot,toe,all){','function measuredFootQ(s){', """function splitFootPatches(meshes,foot,toe,all){
 // The v0.1.13 bug partitioned only 20 points from the ALREADY-selected sole.
 // Select the actual whole shoe through the skinned vertex weights and spatial bounds.
 const ankle=wpos(foot),toePos=wpos(toe),boneNames=new Set([foot.name,toe.name]);
 const profiles=[];
 for(let mi=0;mi<meshes.length;mi++){
  const m=meshes[mi],position=m.geometry.getAttribute('position'),skinIdx=m.geometry.getAttribute('skinIndex'),skinW=m.geometry.getAttribute('skinWeight');
  if(!position)continue;
  const bones=m.skeleton?.bones||[],footBones=new Set(bones.map((b,i)=>boneNames.has(b.name)?i:-1).filter(i=>i>=0));
  const step=Math.max(1,Math.floor(position.count/40000));
  for(let j=0;j<position.count;j+=step){
   const p=m.getVertexPosition(j,V());m.localToWorld(p);
   const r=Math.min(p.distanceTo(ankle),p.distanceTo(toePos));
   if(r>.42||p.y>ankle.y+.14||Math.abs(p.x-ankle.x)>.24)continue;
   let influence=0;
   if(skinIdx&&skinW&&footBones.size){
    for(let k=0;k<4;k++)if(footBones.has(skinIdx.getComponent(j,k)))influence+=skinW.getComponent(j,k);
   }
   profiles.push({mi,j,xyz:p.toArray(),influence,radialDistance:r});
  }
 }
 let last='',chosen=null;
 // Prefer genuine foot/toe SKIN influence; adapt the selection without inventing geometry.
 for(const gate of [.20,.10,.04,0]){
  const a=profiles.filter(p=>p.influence>=gate&&(gate>0||p.radialDistance<.33));
  if(a.length<24){last='INSUFFICIENT_FOOT_INFLUENCE gate='+gate+' count='+a.length;continue;}
  try{chosen=selectShoeWitnesses(a,toePos.clone().sub(ankle).toArray());
   chosen.evidence.weightThreshold=gate;
   chosen.evidence.sampledCandidateVertices=profiles.length;
   break;
  }catch(e){last=e.message;}
 }
 if(!chosen)throw Error('REAL_SHOE_GEOMETRY_CANNOT_SPLIT_'+foot.name+' '+last);
 console.info('REAL_SHOE_WITNESSES '+foot.name,chosen.evidence);
 return chosen;
}
""")
# Do not leave users with a blank screen if an unrelated calibration gate trips.
once("actor.updateMatrixWorld(true);rest=captureSeed();", "actor.updateMatrixWorld(true);rest=captureSeed();\n scene.add(actor);actor.updateMatrixWorld(true); // verified 3D model remains visible even if calibration later fails\n $('identity').textContent='v0.1.14 · ORIGINAL SKINNED 3D MODEL HASH '+SOURCE_SHA+' · SOURCE MATH AND CONTACT AUDIT PENDING';")
once("}catch(e){status('REAL_MODEL_CALIBRATION_BLOCKED '+e.message);console.error(e)}", "}catch(e){playing=false;ready=false;if(actor&&!actor.parent){scene.add(actor);actor.updateMatrixWorld(true);}\n status('REAL_MODEL_CALIBRATION_BLOCKED '+e.message+' · ORIGINAL RIG VISIBLE (STATIC DIAGNOSTIC; NOT A WALK)');console.error(e)}")
once("/* v0.1.13. ONE moving Walking_Woman.","/* v0.1.14. ONE moving Walking_Woman.")
once("v0.1.13 ACCEPTED V019 INVERSE SUPPORT ROOT","v0.1.14 ACCEPTED V019 INVERSE SUPPORT ROOT + REAL SHOE WITNESSES")
once("a.download='hareworks-woman-accepted-v019-world-pin-v0.1.13.json'", "a.download='hareworks-woman-accepted-v019-world-pin-v0.1.14.json'")
once("schema:'hareworks-woman-accepted-v019-world-pin-v0.1.13'", "schema:'hareworks-woman-accepted-v019-world-pin-v0.1.14'")
p.write_text(s)
# Retain original viewer interface, add identity and calibration semantics, distinct cache key.
html=target/'index.html';h=html.read_text().replace('v0.1.13','v0.1.14')
h=h.replace('src="./viewer.mjs?build=v0.1.14-inverse-root"','src="./viewer.mjs?build=v0.1.14-geometry-fix"')
h=h.replace('src="./viewer.mjs?build=v0.1.14"','src="./viewer.mjs?build=v0.1.14-geometry-fix"')
h=h.replace('One source-measured','One source-measured')
html.write_text(h)
# Audits are explicitly versioned; browser evidence never impersonates user visual acceptance.
rp=target/'review-server.py';r=rp.read_text().replace('v0.1.13','v0.1.14');rp.write_text(r)
# Reuse v0.1.13's original mathematical modules and tests unchanged (only local schema version).
rm=target/'root-motion.mjs';rm.write_text(rm.read_text().replace("root-v0.1.13","root-v0.1.14"))
# Update the immutable top-level contract for the new scoped publication.
contract=target/'contract.json';j=json.loads(contract.read_text());j['schema']='hareworks-woman-accepted-v019-shoe-recovery-v0.1.14';j['parent']='480780cf2c6c78227d8c27e227a31204e303666d';j['mutablePaths']=['tools/hareworks-forward-woman/v0.1.14/'];j['witnessMethod']='whole skinned shoe vertices, skin-weight preference, horizontal PCA, three distinct low-surface longitudinal bands';j['calibrationErrorBehavior']='source model remains visible but static, audit not passed';j['ownerVisualAcceptance']=False
contract.write_text(json.dumps(j,indent=2)+'\n')
readme=target/'README.md';readme.write_text("""# Hareworks v0.1.14: restore visible model and fix shoe witnesses

Published v0.1.13 fails early with `SKINNED_HEEL_TOE_SEPARATION_INSUFFICIENT_mixamorigLeftFoot` because it tries to divide twenty already-selected lowest sole points. This is a classification defect, not evidence that the model GLB is missing. The v0.1.13 viewer deferred adding the actor to the scene until all calibration gates passed, creating a blank view.

v0.1.14 preserves the source-derived accepted v0.1.9 gait, inverse stance-driven world-root, true IK solver, phase-varying advance, actor travel, and touch/mouse camera orbit from v0.1.13. Only the shoe witness selection and empty-screen behavior change. It classifies full skinned shoe vertices by horizontal principal axis and low-surface longitudinal bands, preferring actual foot/toe skin weights. All three patches must have unique indices and spatially separated centroids. A calibration failure now leaves the correct hash-verified 3D model visible in a STATIC, explicitly failed diagnostic state; it does not claim the gait works.

Model SHA: `a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6`. Target only: `Valar05/parametric-parambulator`, persistent checkout in Android `Documents/GodotProjects/parametric-parambulator`. Immutable parent: `480780cf2c6c78227d8c27e227a31204e303666d`. No GLB duplication, no unrelated LFS fetch, no temporary clones, no old-version mutations. Numeric witness tests are synthetic. Actual skinned moving contact physics, compatibility of the vertex groups and visual likeness remain browser/owner acceptance gates; they are not proven by static tests.
""")
print('PATCH_V014_GEOMETRY_VISIBILITY_COMPLETE')
