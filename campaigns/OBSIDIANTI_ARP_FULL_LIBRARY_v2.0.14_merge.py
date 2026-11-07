#!/usr/bin/env python3
"""glTF2 animation-only GLB merger. No bone edits, no geometry mutations."""
import argparse,copy,hashlib,json,math,pathlib,struct,sys

def sha(p):
 h=hashlib.sha256()
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()

def load(path):
 path=pathlib.Path(path)
 b=path.read_bytes()
 if len(b)<32 or b[:4]!=b'glTF':raise ValueError('INVALID_GLB_MAGIC_'+str(path))
 magic,version,n=struct.unpack_from('<4sII',b,0)
 if version!=2 or n!=len(b):raise ValueError('INVALID_GLB_LENGTH_'+str(path))
 jlen,jtyp=struct.unpack_from('<I4s',b,12)
 if jtyp!=b'JSON' or jlen>20000000:raise ValueError('NO_VALID_JSON_CHUNK')
 js=json.loads(b[20:20+jlen]); pos=20+jlen
 if pos+8>len(b):raise ValueError('NO_BIN_CHUNK')
 blen,btyp=struct.unpack_from('<I4s',b,pos)
 if btyp!=b'BIN\0' or pos+8+blen!=len(b):raise ValueError('INVALID_BIN_CHUNK')
 data=b[pos+8:];
 if not js.get('animations') or len(js.get('buffers',[]))!=1 or not js.get('skins') or not js.get('meshes'):
  raise ValueError('NO_USABLE_SKIN_ANIMATION')
 return js,data

def assemble(js,data,path):
 js['buffers'][0]['byteLength']=len(data)
 j=json.dumps(js,separators=(',',':'),ensure_ascii=False).encode()
 j+=b' ' * ((-len(j))%4)
 data+=b'\0' * ((-len(data))%4)
 size=12+8+len(j)+8+len(data)
 out=struct.pack('<4sII',b'glTF',2,size)+struct.pack('<I4s',len(j),b'JSON')+j+struct.pack('<I4s',len(data),b'BIN\0')+data
 pathlib.Path(path).write_bytes(out)
 return len(out)

def skeleton(js):
 names=[n.get('name','') for n in js['nodes']]
 if len(names)!=len(set(names)) or not all(names):raise ValueError('NONUNIQUE_OR_EMPTY_NODE_NAMES')
 return names

def check_skeleton(base,other):
 bn=skeleton(base);on=skeleton(other)
 if set(bn)!=set(on):raise ValueError('NONIDENTICAL_NODE_SET')
 bs=base['skins'];os=other['skins']
 if len(bs)!=len(os):raise ValueError('SKIN_COUNT_CHANGED')
 for a,b in zip(bs,os):
  if [bn[k] for k in a['joints']] != [on[k] for k in b['joints']]:raise ValueError('SKIN_BONE_ORDER_CHANGED')
 # Same rest transforms and parent hierarchy, even if export node indices differ.
 for name in bn:
  a=base['nodes'][bn.index(name)];b=other['nodes'][on.index(name)]
  for key in ('translation','rotation','scale','matrix'):
   aa=a.get(key);bb=b.get(key)
   if aa is None and bb is None:continue
   if aa is None or bb is None or len(aa)!=len(bb) or any(abs(float(x)-float(y))>0.00005 for x,y in zip(aa,bb)):
    raise ValueError('REST_NODE_TRANSFORM_CHANGED_'+name+'_'+key)
  if sorted(bn[k] for k in a.get('children',[]))!=sorted(on[k] for k in b.get('children',[])):
   raise ValueError('NODE_HIERARCHY_CHANGED_'+name)
 return {i:bn.index(name) for i,name in enumerate(on)}

def stat_accessor(js,data,index):
 a=js['accessors'][index];bv=js['bufferViews'][a['bufferView']]
 if a['componentType']!=5126 or a['type'] not in ('SCALAR','VEC3','VEC4') or 'sparse' in a:
  return {'count':a['count'],'type':a['type'],'reason':'UNSUPPORTED_KEY_STATS'}
 n={'SCALAR':1,'VEC3':3,'VEC4':4}[a['type']]
 stride=bv.get('byteStride',n*4)
 start=bv.get('byteOffset',0)+a.get('byteOffset',0)
 rows=[struct.unpack_from('<'+'f'*n,data,start+i*stride) for i in range(a['count'])]
 if not rows or any(not math.isfinite(v) for row in rows for v in row):raise ValueError('NONFINITE_KEY_DATA')
 xyz=list(zip(*rows))
 return {'count':len(rows),'type':a['type'],'min':[round(min(v),6) for v in xyz],
  'max':[round(max(v),6) for v in xyz],
  'first':[round(v,6) for v in rows[0]], 'last':[round(v,6) for v in rows[-1]],
  'maxDisplacementFromFirst':round(max(math.dist(row,rows[0]) for row in rows),6)}

def merge(entries,out,report):
 if not entries:raise ValueError('NO_INPUTS')
 first=entries[0]
 base,bindata=load(first['path']);base=copy.deepcopy(base)
 names=skeleton(base)
 report_data={'schema':'obsidianti-arp-full-library-v2.0.14','inputs':{},'clips':{},'canonicalMutation':False}
 seen=set()
 # All supplied GLBs are single-clip exports for the identical target skeleton.
 original_animations=[]
 base['animations']=[]
 for idx,entry in enumerate(entries):
  name=entry['name'];path=pathlib.Path(entry['path'])
  if name in seen:raise ValueError('DUPLICATE_ANIMATION_NAME_'+name)
  seen.add(name)
  src,bin_src=load(path)
  node_map=check_skeleton(base,src)
  if len(src['animations'])!=1:raise ValueError('MULTIPLE_SOURCE_ACTIONS_'+name)
  old_anim=src['animations'][0]
  cloned={'name':name,'channels':[],'samplers':[]}
  amap={};vmap={};copied_bytes=0
  def copy_accessor(n):
   nonlocal bindata,copied_bytes
   if n in amap:return amap[n]
   accessor=copy.deepcopy(src['accessors'][n])
   if 'sparse' in accessor or 'bufferView' not in accessor:raise ValueError('SPARSE_ACCESSOR_UNSUPPORTED')
   oldview=accessor['bufferView'];v=src['bufferViews'][oldview]
   if v.get('buffer',0)!=0:raise ValueError('MULTIPLE_BUFFER_VIEWS_UNSUPPORTED')
   if oldview not in vmap:
    offset=v.get('byteOffset',0);length=v['byteLength']
    if offset+length>len(bin_src):raise ValueError('SOURCE_BUFFER_OVERRUN')
    padding=(-len(bindata))%4
    bindata+=b'\0'*padding
    new=copy.deepcopy(v);new['buffer']=0;new['byteOffset']=len(bindata)
    bindata+=bin_src[offset:offset+length]
    vmap[oldview]=len(base['bufferViews']);base['bufferViews'].append(new)
    copied_bytes+=length
   accessor['bufferView']=vmap[oldview]
   amap[n]=len(base['accessors']);base['accessors'].append(accessor)
   return amap[n]
  keys={}
  for sample in old_anim['samplers']:
   cloned['samplers'].append({'input':copy_accessor(sample['input']),
    'output':copy_accessor(sample['output']),'interpolation':sample.get('interpolation','LINEAR')})
  for channel in old_anim['channels']:
   target=channel['target'];bone=src['nodes'][target['node']].get('name','');axis=target['path']
   if not bone or bone not in names:raise ValueError('ANIMATED_BONE_MISSING_'+bone)
   cloned['channels'].append({'sampler':channel['sampler'],
     'target':{'node':node_map[target['node']],'path':axis}})
   if bone in ('mixamorig:Hips','mixamorig:LeftFoot','mixamorig:RightFoot') and axis=='translation':
    samp=old_anim['samplers'][channel['sampler']]
    keys[bone]=stat_accessor(src,bin_src,samp['output'])
  if len(cloned['channels'])<8:raise ValueError('UNEXPECTED_TOO_FEW_ANIMATION_CHANNELS_'+name)
  report_data['clips'][name]={'sourceSha256':sha(path),'sourceAnimation':old_anim.get('name'),
       'channels':len(cloned['channels']),'keyTranslations':keys,'addedAnimationBytes':copied_bytes,
       'status':'GLTF_SAMPLERS_COPIED_IDENTICAL_SKELETON'}
  base['animations'].append(cloned)
  report_data['inputs'][name]={'sha256':sha(path),'bytes':path.stat().st_size}
 bytes_out=assemble(base,bindata,out)
 check,_=load(out)
 if len(check['animations'])!=len(entries):raise ValueError('MERGED_CLIP_COUNT_MISMATCH')
 report_data['merged']={'sha256':sha(out),'bytes':bytes_out,'clips':len(entries),'names':[a['name'] for a in check['animations']], 'nodes':len(check['nodes']),'skins':len(check['skins'])}
 pathlib.Path(report).write_text(json.dumps(report_data,indent=2,sort_keys=True)+'\n')
 return report_data

if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--manifest',required=True);ap.add_argument('--output',required=True);ap.add_argument('--report',required=True)
 a=ap.parse_args();d=json.loads(pathlib.Path(a.manifest).read_text());r=merge(d['clips'],a.output,a.report)
 print('COMBINED_REVIEW_GLB='+str(a.output),'SHA256='+r['merged']['sha256'],'ANIMATIONS='+str(r['merged']['clips']))
