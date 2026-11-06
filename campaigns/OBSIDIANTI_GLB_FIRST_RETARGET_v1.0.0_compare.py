"""Compare the original live-IK evaluated Blender source to its constraint-baked GLB."""
import json,math,pathlib,sys
src,dst,output=sys.argv[1:]
a=json.loads(pathlib.Path(src).read_text());b=json.loads(pathlib.Path(dst).read_text())
names=('Cast','Heavy1','Heavy2','Heavy3','Kick','Light1','Light2','Light3','SpringAttack','Stomp')
rows=[];global_max=0
for name in names:
 s=a['actions'][name]['frames'];t=b['actions'][name]['frames']
 assert len(s)>2 and len(t)>2,'INSUFFICIENT_MOTION_SAMPLES '+name
 # Compare equivalent normalized timeline locations to accommodate differing import FPS.
 se=s[-1]['time'];te=t[-1]['time'];assert se>0 and te>0
 clip={'name':name,'sourceDuration':se,'exportDuration':te,'feet':{}}
 for side in ('Left','Right'):
  bone='mixamorig:'+side+'Foot';errors=[]
  for i in range(11):
   u=i/10
   x=min(s,key=lambda r:abs(r['time']/se-u))['bones'][bone]['worldPosition']
   y=min(t,key=lambda r:abs(r['time']/te-u))['bones'][bone]['worldPosition']
   errors.append(math.dist(x,y))
  worst=max(errors);clip['feet'][side]={'maxError_m':worst,'meanError_m':sum(errors)/len(errors)}
  global_max=max(global_max,worst)
 rows.append(clip)
# Original importer never passed through this export, and this is independent causality evidence.
report={'source':'BLENDER_EVALUATED_IK','comparison':'EXPORTED_GLB_IMPORTED_AS_ARES','maxFootError_m':global_max,'clips':rows,'note':'Normalized-time samples; differences can include source/export timebase and skeleton scale; not yet proof of retarget contact.'}
pathlib.Path(output).write_text(json.dumps(report,indent=2)+'\n')
print('SOURCE_TO_EXPORTED_GLB_MAX_FOOT_ERROR_M='+str(round(global_max,6)),flush=True)
