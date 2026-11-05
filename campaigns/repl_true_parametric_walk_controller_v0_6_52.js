// Repl v0.6.52. Runtime gait is analytically evaluated Fourier basis,
// fitted separately from the approved GLB by the Termux campaign. No AnimationMixer
// or GLTF animation track is used to drive the fitted horse. The reference horse
// in the viewer may use a mixer ONLY when comparison is explicitly requested.
import * as THREE from 'three';
const clamp=(v,a,b)=>Math.max(a,Math.min(b,v));
const semantic={LF:['Bone_016','Bone_015','Bone_014','Bone_013','Bone_012'],RF:['Bone_022','Bone_021','Bone_020','Bone_019','Bone_018'],LH:['Bone_027','Bone_026','Bone_025','Bone_024','Bone_023'],RH:['Bone_032','Bone_031','Bone_030','Bone_029','Bone_028']};
const drivenNames=new Set(Object.values(semantic).flat());
const FOURIER=(c,phase)=>{const out=[];for(const cc of c){let v=cc[0];for(let k=1;k<cc.length/2+.01;k++){const idx=1+2*(k-1);v+=cc[idx]*Math.cos(2*Math.PI*k*phase)+cc[idx+1]*Math.sin(2*Math.PI*k*phase)}out.push(v)}return out};
const Q=new THREE.Quaternion();
const AX=new THREE.Vector3();
export const MODE='EXTRACTED_ANALYTIC_GAIT_NO_BAKED_DRIVER';
export class EquineGaitBasis {
 constructor(spec){if(spec.format!=='REPL_PARAMETRIC_FOURIER_V1')throw Error('FIT_FORMAT_INVALID');this.spec=spec;this.period=spec.duration/3;this.defaultStride=spec.root_advance[2]/3;this.defaultCadence=1/this.period;}
 evaluate(track,phase){return FOURIER(track.coefficients,phase)}
 // Three source cycles are fitted as one periodic analytic pattern. Cadence and
 // per-cycle travel are independent; contact-aware retiming will be a later stage.
}
export class ReplRigAdapter {
 constructor(scene,spec){this.scene=scene;this.nodes={};this.base={};scene.traverse(o=>{if(o.name){this.nodes[o.name]=o;this.base[o.name]={p:o.position.clone(),q:o.quaternion.clone(),s:o.scale.clone()}}});
  for(const [key,chain] of Object.entries(semantic))if(chain.some(n=>!this.nodes[n]))throw Error('MISSING_REPL_RIG_'+key);
  if(!this.nodes[spec.root_node])throw Error('MISSING_ROOT');this.root=this.nodes[spec.root_node];this.chains=semantic;
  for(const track of spec.tracks)if(!this.nodes[track.node])throw Error('MISSING_FITTED_NODE:'+track.node);
 }
 reset(){for(const [n,b] of Object.entries(this.base)){const o=this.nodes[n];o.position.copy(b.p);o.quaternion.copy(b.q);o.scale.copy(b.s)}}
}
export class FittedParametricWalk {
 constructor(gltf,spec){this.model=gltf.scene;this.basis=new EquineGaitBasis(spec);this.rig=new ReplRigAdapter(gltf.scene,spec);this.elapsed=0;this.paused=false;this.params={stride:this.basis.defaultStride,cadence:this.basis.defaultCadence,amplitude:1,body:1};this.status={};this.evaluate(0)}
 setParams(p){this.params={stride:clamp(+p.stride,.10,.55),cadence:clamp(+p.cadence,.4,1.6),amplitude:clamp(+p.amplitude,.65,1.4),body:clamp(+p.body,0,1.8)}}
 seek(t){this.elapsed=Math.max(0,t);this.evaluate(this.elapsed)}
 update(dt){if(!this.paused)this.elapsed+=clamp(dt,0,.07);return this.evaluate(this.elapsed)}
 evaluate(time){const s=this.basis.spec,p=this.params,b=this.basis,cycle=time*p.cadence,phase=((cycle/3)%1+1)%1,scale=p.stride/b.defaultStride;
  this.rig.reset();const root=this.rig.root;
  for(const tr of s.tracks){const node=this.rig.nodes[tr.node],v=b.evaluate(tr,phase);if(tr.path==='rotation'){
    let k=1;if(drivenNames.has(tr.node))k=p.amplitude*(.78+.22*scale);
    else if(tr.node.startsWith('Bone_'))k=p.body;
    const vec=new THREE.Vector3(v[0]*k,v[1]*k,v[2]*k);const len=vec.length();
    Q.identity();if(len>1e-10){AX.copy(vec).multiplyScalar(1/len);Q.setFromAxisAngle(AX,len)}
    node.quaternion.copy(this.rig.base[tr.node].q).multiply(Q).normalize();
   }else if(tr.path==='translation'){
    node.position.set(v[0],v[1],v[2]);if(tr.node===s.root_node){node.position.x+=s.root_start[0];node.position.y+=s.root_start[1]+(v[1]*0)*(p.body-1);node.position.z=s.root_start[2]+cycle*p.stride+v[2]*scale;}
   }
  }
  this.model.updateMatrixWorld(true);
  this.status={mode:MODE,phase,cycle,stride:p.stride,cadence:p.cadence,body:p.body,amplitude:p.amplitude,velocity:p.stride*p.cadence,referenceStride:b.defaultStride,referenceCadence:b.defaultCadence};return this.status;
 }
}
