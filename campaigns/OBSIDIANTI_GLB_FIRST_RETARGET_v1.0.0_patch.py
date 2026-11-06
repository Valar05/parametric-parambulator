"""Append constraint-baked donor GLB clips through original Ares-style pose rebase.
No skeleton/mesh changes. Existing GLB animations untouched. New actions are review-only.
"""
import importlib.util,json,sys,pathlib,copy,hashlib,math
repo,model,samples,out,report=sys.argv[1:]
p=pathlib.Path(repo)/'campaigns/OBSIDIANTI_GLTF_LIBRARY_v1.1.0.py'
spec=importlib.util.spec_from_file_location('historical_library',p);lib=importlib.util.module_from_spec(spec);spec.loader.exec_module(lib)
assert lib.sha(model)=='955e424172da09cbff1182f260c7053389d2fa623657a62a4d03dd78f5fa1b32','BASE_MODEL_IDENTITY_WRONG'
g,b=lib.glb_load(model)
original=bytes(b);locks={k:copy.deepcopy(g[k]) for k in ('nodes','skins','meshes','scenes')};original_anims=copy.deepcopy(g['animations'])
assert len(original_anims)==23,'BASELINE_ANIMATION_COUNT_WRONG'
raw=json.loads(pathlib.Path(samples).read_text());actions=lib.parse_samples(raw,lib.ANIM_LABELS)
assert 'Idle' in raw['actions'],'SOURCE_GLTF_IDLE_NOT_EXPORTED'
base=raw['actions']['Idle']['frames'][0]
assert len(base['bones'])>=25,'GLB_DONOR_BONES_INCOMPLETE'
names=lib.nmap(g);rest=lib.ref_quats(g);approved,positions=lib.approved_idle(g,b)
hip=names['mixamorig:Hips'];p0=positions[hip];r0=base['bones']['mixamorig:Hips']['worldPosition']
w=lib.Writer(g,b)
ratio=.8700185743929264  # exact previously measured Ares-path ratio, not another guessed scale
rows=[]
for name in lib.ANIM_LABELS:
 frames=actions[name]['frames'];times=[float(f['time'])-float(frames[0]['time']) for f in frames]
 rots={j:[] for j in approved};poss={hip:[]}
 for f in frames:
  mapped=lib.rebase_source_pose(f,base,g,rest,approved,frames)
  for j in approved:
   rots[j].append(mapped.get(j,approved[j]))
  hp=f['bones']['mixamorig:Hips']['worldPosition'];delta=[hp[k]-r0[k] for k in range(3)]
  assert max(map(abs,delta))<3,'ROOT_DELTA_UNREASONABLE '+name
  poss[hip].append([p0[k]+ratio*delta[k] for k in range(3)])
  # Maintain separate weapon controls with original library's weapon-local mapping.
  for wb in ('Weapon.L','Weapon.R'):
   j=lib.map_bone(wb,names)
   if j is None:continue
   one=f['bones'].get(wb);zero=base['bones'].get(wb)
   origin=g['nodes'][j].get('translation',[0,0,0]);pos=list(origin)
   if one and zero:
    pos=[origin[k]+one['localDeltaPosition'][k]-zero['localDeltaPosition'][k] for k in range(3)]
   poss.setdefault(j,[]).append(pos)
 clip='LionheartGLBBake_'+name
 w.animation(clip,times,rots,poss)
 rows.append({'name':clip,'samples':len(times),'duration':times[-1],'source':'NATIVE_LIONHEART_EXPORTED_GLB_REIMPORTED_AS_ARES'})
new=lib.glb_bytes(g,b);g2,b2=lib.glb_load_bytes(new)
assert bytes(b2[:len(original)])==original,'ORIGINAL_BIN_MUTATED'
assert all(g2[k]==locks[k] for k in locks),'RIG_OR_MESH_MUTATED'
assert g2['animations'][:len(original_anims)]==original_anims,'ORIGINAL_ACTION_MUTATED'
assert len(g2['animations'])==33,'CANDIDATE_CLIP_COUNT_WRONG'
assert all(len(a['channels'])>=20 for a in g2['animations'][23:]),'CANDIDATE_CLIP_TRACKS_MISSING'
pathlib.Path(out).write_bytes(new)
assert pathlib.Path(out).read_bytes()[:4]==b'glTF'
sha=hashlib.sha256(new).hexdigest()
meta={'status':'REVIEW_CANDIDATE_NOT_CANONICAL','method':'ARES_V1_1_REST_POSE_REBASE_ON_EXPORTED_GLTF_DONOR','originalSourceSha256':lib.sha(model),'candidateSha256':sha,'donorSampleSha256':lib.sha(samples),'scaleRatio':ratio,'preservedClips':len(original_anims),'candidateClips':rows,'canonicalUnchanged':True,'originalBinaryPrefixUnchanged':True,'changedSkeleton':False}
pathlib.Path(report).write_text(json.dumps(meta,indent=2)+'\n')
print('TRANSFER_CANDIDATE_SHA256='+sha,flush=True)
print('REVIEW_CLIPS=33 CANDIDATE_CLIPS=10 ORIGINALS_UNCHANGED=YES',flush=True)
