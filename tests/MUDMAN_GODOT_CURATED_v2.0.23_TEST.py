import os,sys,tempfile,pathlib,json,struct,zipfile,hashlib,copy,argparse
sys.path.insert(0,str(pathlib.Path(__file__).parent))
import patch_glb as p

def fixture(root):
 js={'asset':{'version':'2.0'},'scene':0,'scenes':[{'nodes':[0]}],
 'nodes':[{'name':'Root','children':[1,2]},{'name':'mixamorig:Hips'}, {'name':'MudmanMesh','mesh':0,'skin':0}],
 'meshes':[{'name':'Mudman','primitives':[{'attributes':{},'mode':4}]}],
 'skins':[{'joints':[1]}],'materials':[], 'bufferViews':[],'accessors':[],'buffers':[{'byteLength':0}], 'animations':[]}
 data=bytearray()
 def add(rows,typ='VEC3',comp=5126,normalized=False):
  nonlocal data
  fmt={5126:'f',5123:'H',5121:'B'}[comp];count=len(rows[0]);assert count==p.WIDTH[typ]
  raw=b''.join(struct.pack('<'+fmt*count,*row) for row in rows)
  data+=b'\0'*((-len(data))%4);off=len(data);data.extend(raw)
  vi=len(js['bufferViews']);js['bufferViews'].append({'buffer':0,'byteOffset':off,'byteLength':len(raw)})
  ai=len(js['accessors']);js['accessors'].append({'bufferView':vi,'componentType':comp,'count':len(rows),'type':typ,**({'normalized':True} if normalized else {})})
  return ai
 pos=add([(-1.,.25,0.),(1.,1.35,0.),(0.,.25,1.)]*40)
 joints=add([(0,0,0,0)]*120,'VEC4',5123)
 weights=add([(1.,0.,0.,0.)]*120,'VEC4')
 uvs=add([(.2,.3)]*120,'VEC2')
 js['meshes'][0]['primitives'][0]['attributes']={'POSITION':pos,'JOINTS_0':joints,'WEIGHTS_0':weights,'TEXCOORD_0':uvs}
 timestamps=add([(0.,),(1.,)],'SCALAR')
 rootloc=add([(0.,0.,0.),(0.,0.,0.)])
 for name in list(p.MAP)+['Mudman_extra_'+str(i) for i in range(77-len(p.MAP))]:
  js['animations'].append({'name':name,'channels':[{'sampler':0,'target':{'node':1,'path':'translation'}}], 'samplers':[{'input':timestamps,'output':rootloc,'interpolation':'LINEAR'}]})
 input_glb=root/'base.glb';p.glb_save(js,bytes(data),input_glb)
 return input_glb

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--mesh-zip',default='/mnt/data/Meshy_AI_Mudstone_Golem_20261107_animated_mixamo_Running.zip');args=parser.parse_args()
 zipname=args.mesh_zip
 assert os.path.isfile(zipname)
 with tempfile.TemporaryDirectory() as t:
  root=pathlib.Path(t);source=fixture(root)
  p.OLD_GLB=p.sha(source);p.OWNER_ZIP=p.sha(zipname)
  out=root/'out.glb';report=root/'report.json'
  r=p.apply(source,zipname,out,report)
  assert len(r['animationMap'])==23 and len(r['excludedAnimationNames'])==54
  assert abs(r['skinnedGroundAfter']['minY'])<.002
  assert abs(r['groundOffsetMeters']+.25)<.002
  js,bin=p.glb_load(out);assert len(js['animations'])==23
  assert len(js['images'])==1 and len(js['textures'])==1
  assert bin.startswith(p.glb_load(source)[1])
  assert js['materials'][0]['pbrMetallicRoughness']['baseColorTexture']['index']==0
  try:p.apply(source,zipname,out,report)
  except RuntimeError as ex:assert 'OUTPUT_COLLISION' in str(ex)
  else:raise AssertionError('overwrite not blocked')
  old=p.OWNER_PNG;p.OWNER_PNG='0'*64
  try:p.apply(source,zipname,root/'bad.png.glb',root/'bad.json')
  except RuntimeError as ex:assert 'SHA_OR_SIGNATURE' in str(ex)
  else:raise AssertionError('texture SHA not blocked')
  p.OWNER_PNG=old
  altered,bd=p.glb_load(source);del altered['meshes'][0]['primitives'][0]['attributes']['TEXCOORD_0'];bad=root/'no_uv.glb';p.glb_save(altered,bd,bad);p.OLD_GLB=p.sha(bad)
  try:p.apply(bad,zipname,root/'no_uv_out.glb',root/'bad2.json')
  except RuntimeError as ex:assert 'WITHOUT_UV0' in str(ex)
  else:raise AssertionError('missing UV not blocked')
 print('V2.0.23_PATCH_TESTS_OK synthetic_skin=YES actual_owner_texture_sha=YES filtered=23 preserved=YES bad_uv=BLOCKED bad_sha=BLOCKED collision=BLOCKED')
if __name__=='__main__':main()
