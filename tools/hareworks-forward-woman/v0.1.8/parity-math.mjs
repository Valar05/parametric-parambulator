/* Exact-time source-versus-generated scalar error accumulator. Pure JS.
   The caller must sample independently posed real rig joints. */
export function createAudit(){return Object.create(null)}
export function observe(audit,bone,measurement,error,rateHz,timeSeconds){
 if(!bone||!measurement||!Number.isFinite(error)||error<0||!Number.isFinite(rateHz)||rateHz<=0||!Number.isFinite(timeSeconds)||timeSeconds<0)throw Error('PARITY_INVALID_OBSERVATION');
 const group=audit[bone]??(audit[bone]=Object.create(null));
 const a=group[measurement]??(group[measurement]={n:0,sumSq:0,max:-Infinity,worst:null,byRate:Object.create(null)});
 a.n++;a.sumSq+=error*error;
 if(error>a.max){a.max=error;a.worst={t:timeSeconds,rateHz,error}}
 const r=a.byRate[rateHz]??(a.byRate[rateHz]={n:0,sumSq:0,max:0});
 r.n++;r.sumSq+=error*error;r.max=Math.max(r.max,error);
}
export function finalizeAudit(audit){
 const out=Object.create(null);
 for(const [bone,kinds] of Object.entries(audit)){
  out[bone]=Object.create(null);
  for(const [kind,a] of Object.entries(kinds)){
   if(!a.n)throw Error('PARITY_EMPTY_METRIC');
   const byRate=Object.create(null);
   for(const [rate,r] of Object.entries(a.byRate))byRate[rate]={n:r.n,rms:Math.sqrt(r.sumSq/r.n),max:r.max};
   out[bone][kind]={samples:a.n,rms:Math.sqrt(a.sumSq/a.n),max:a.max,worst:a.worst,byRate};
  }
 }
 return out;
}
export function rankOffenders(report,metric,count=10){
 return Object.entries(report).filter(([_,m])=>m[metric]).map(([bone,m])=>({bone,...m[metric]})).sort((a,b)=>b.rms-a.rms).slice(0,count);
}
