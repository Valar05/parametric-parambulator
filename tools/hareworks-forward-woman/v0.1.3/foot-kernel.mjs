/* v0.1.3 forward-only Woman foot path and anatomical knee plane.
 * Six-harmonic, continuously looping PHASE FUNCTIONS fitted to the source.
 * Never accesses source animation tracks at runtime. The pelvis remains v0.1.2.
 * Source space: Y up; X lateral; Z forward; local offsets rotate by pelvis yaw.
 */
export function fourier(coeff, q) {
  if (!Array.isArray(coeff) || coeff.length !== 13) throw Error('FOOT_COEFFICIENT_SHAPE');
  let result = coeff[0];
  for (let n = 1; n <= 6; n++) {
    const angle = 2 * Math.PI * n * q;
    result += coeff[2*n-1]*Math.sin(angle) + coeff[2*n]*Math.cos(angle);
  }
  return result;
}
export const cyc = (t, duration) => ((t / duration) % 1 + 1) % 1;
export const rotateY = (v, yaw) => {
  const c=Math.cos(yaw),s=Math.sin(yaw);
  return [v[0]*c + v[2]*s,v[1],-v[0]*s + v[2]*c];
};
export const magnitude = v => Math.hypot(...v);
export const dot=(a,b)=>a[0]*b[0]+a[1]*b[1]+a[2]*b[2];
export const scale=(a,f)=>a.map(v=>v*f);
export const sub=(a,b)=>a.map((v,i)=>v-b[i]);
export const add=(a,b)=>a.map((v,i)=>v+b[i]);
export function legAt(profile, side, t) {
  const p=profile[side];if (!p) throw Error('UNKNOWN_LEG_'+side);
  const q=cyc(t,profile.duration);
  return {
    q,
    ankleLocal:p.ankle.map(coeff=>fourier(coeff,q)),
    poleLocal:p.pole.map(coeff=>fourier(coeff,q)),
  };
}
// Explicitly no hidden reach clamp: an out-of-range request must fail the gate.
// Pole is the fitted knee plane projected orthogonally to hip-to-ankle axis.
export function kneeFromTarget(hip,ankle,l1,l2,pole,eps=1e-5) {
  const dvec=sub(ankle,hip),d=magnitude(dvec),total=l1+l2;
  if (!(d < total + eps && d > Math.abs(l1-l2) + eps)) throw Error('UNREACHABLE_KNEE_'+d.toFixed(6)+'_REACH_'+total.toFixed(6));
  const u=scale(dvec,1/d), a=(l1*l1-l2*l2+d*d)/(2*d),height=Math.sqrt(Math.max(0,l1*l1-a*a));
  const projected=sub(pole,scale(u,dot(pole,u))),norm=magnitude(projected);
  if (norm < 1e-5) throw Error('KNEE_POLE_SINGULAR');
  return add(add(hip,scale(u,a)),scale(projected,height/norm));
}
export function validateFootProfile(p) {
 if (p.schema!=='hareworks-forward-woman-foot-pole-v0.1.3'||p.sourceSha256!=='a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6'||p.clip!=='Walking_Woman'||Math.abs(p.duration-.966667)>1e-4) throw Error('FOOT_PROFILE_IDENTITY');
 for(const side of ['left','right']){
   const s=p[side];if (!(s.upperLength>.2&&s.lowerLength>.2))throw Error('FOOT_LENGTH_INVALID');
   for(const ch of [...s.ankle,...s.pole]) if(ch.length!==13||!ch.every(Number.isFinite))throw Error('FOOT_FOURIER_INVALID');
 }
 return true;
}
