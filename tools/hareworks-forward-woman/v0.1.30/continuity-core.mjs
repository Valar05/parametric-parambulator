// Smooth input gain for source-derived ankle pinning. No side effects.
export const clamp01=x=>Math.max(0,Math.min(1,x));
export const smoothstep=x=>{const t=clamp01(x);return t*t*(3-2*t);};
export function stanceWeight(phase,window){
 if(!Number.isFinite(phase)||!window||!(window.duty>0&&window.duty<1))throw Error('INVALID_STANCE_WINDOW');
 const q=((phase-window.start)%1+1)%1;
 if(q>=window.duty)return 0;
 const ramp=Math.min(window.duty*.24,.12);
 return smoothstep(q/ramp)*smoothstep((window.duty-q)/ramp);
}
export function correctionWeight(distance,maximum){
 if(!Number.isFinite(distance)||!(maximum>0))throw Error('INVALID_CORRECTION');
 // Fade BEFORE threshold: 65% -> 100% of the established hard envelope.
 return 1-smoothstep((distance/maximum-.65)/.35);
}
