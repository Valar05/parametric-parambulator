/* Pure forward-only gait math. World convention: Three.js +Y up, +Z forward,
 * positive body yaw carries +Z toward +X. No browser or rig dependency. */
export function harmonic(coeff,q){let out=coeff[0];for(let i=1;i<coeff.length;i+=2){let n=(i+1)/2;out+=coeff[i]*Math.sin(2*Math.PI*n*q)+coeff[i+1]*Math.cos(2*Math.PI*n*q)}return out}
export function trajectory(t,profile,side){
 const p=profile[side],beta=profile.beta,L=p.front-p.rear;
 const q=((t/profile.clipDuration-p.phaseOffset)%1+1)%1;
 let z;
 if(q<beta)z=p.front-L*q/beta;
 else{let s=(q-beta)/(1-beta),m=-L*(1-beta)/beta;
  z=(2*s**3-3*s*s+1)*p.rear+(s**3-2*s*s+s)*m+(-2*s**3+3*s*s)*p.front+(s**3-s*s)*m;
 }
 return {x:harmonic(p.xFourier,q),y:harmonic(p.yFourier,q),z,q};
}
export function worldOffset(f,yaw,hipY){const c=Math.cos(yaw),s=Math.sin(yaw);return [f.x*c+f.z*s,f.y-hipY,-f.x*s+f.z*c]}
export function inverseWorldOffset(d,yaw){const c=Math.cos(yaw),s=Math.sin(yaw);return {x:d[0]*c-d[2]*s,z:d[0]*s+d[2]*c}}
