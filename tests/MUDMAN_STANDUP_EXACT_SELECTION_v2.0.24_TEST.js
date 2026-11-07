const assert=require('node:assert/strict');
const fs=require('node:fs');
const data=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
const picker=fs.readFileSync(process.argv[3],'utf8');
const fn=(new Function('return ('+picker+')'))();
const gltf={animations:data.map(name=>({name,signature:'clip-'+name}))};
for(const name of data){assert.equal(fn(gltf,name).name,name)}
assert.equal(fn(gltf,'StandUp').name,'StandUp');
assert.equal(fn(gltf,'ProneBackStandUp').name,'ProneBackStandUp');
assert.throws(()=>fn(gltf,'Stand'),/EXACT_ANIMATION_SELECTION_FAILED/);
assert.throws(()=>fn({animations:[{name:'StandUp'},{name:'StandUp'}]},'StandUp'),/count=2/);
assert.throws(()=>fn({animations:[{name:'Other'}]},'StandUp'),/count=0/);
console.log('EXACT_SELECTION_NODE_TESTS_OK 23_CLIPS + STANDUP_COLLISION + UNKNOWN + DUPLICATE');
