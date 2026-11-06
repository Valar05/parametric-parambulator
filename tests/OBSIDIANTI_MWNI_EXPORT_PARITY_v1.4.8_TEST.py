#!/usr/bin/env python3
"""v1.4.8 offline tests: real glTF binary buffer decoding, negative motion, provenance safety."""
import hashlib,json,math,pathlib,struct,sys,tempfile,shutil,os,subprocess,time,urllib.request,urllib.error,socket
import glb_scan
import driver

J=['LeftUpLeg','LeftLeg','LeftFoot','RightUpLeg','RightLeg','RightFoot','LeftArm','RightArm','RightForeArm','Spine2']
def glb(path,moving=True,skin_all=True):
  nodes=[{'name':'mixamorig:'+j} for j in J]
  raw=b'';views=[];accessors=[];samplers=[];channels=[]
  def add(values, typ):
    nonlocal raw
    count=len(values);size={'SCALAR':1,'VEC4':4}[typ]
    b=b''.join(struct.pack('<'+'f'*size,*v) for v in values)
    offset=len(raw);raw+=b;views.append({'buffer':0,'byteOffset':offset,'byteLength':len(b)})
    accessors.append({'bufferView':len(views)-1,'componentType':5126,'count':count,'type':typ})
    return len(accessors)-1
  t=add([(0.,),(1.,),(2.,)],'SCALAR')
  for i,j in enumerate(J):
    rot=lambda a:(math.sin(a/2),0.,0.,math.cos(a/2))
    values=[rot(0),rot((.3 if moving else 0)* (i%3+1)),rot(0)]
    o=add(values,'VEC4');samplers.append({'input':t,'output':o,'interpolation':'LINEAR'})
    channels.append({'sampler':len(samplers)-1,'target':{'node':i,'path':'rotation'}})
  g={'asset':{'version':'2.0'},'buffers':[{'byteLength':len(raw)}],'bufferViews':views,'accessors':accessors,
     'nodes':nodes,'animations':[{'name':'Animation','samplers':samplers,'channels':channels}],
     'meshes':[{'primitives':[{'attributes':{}}]}],'skins':[{'joints':list(range(len(J))) if skin_all else [0]}]}
  js=json.dumps(g,separators=(',',':')).encode();js+=b' '*( (-len(js))%4 )
  payload=struct.pack('<I4s',len(js),b'JSON')+js+struct.pack('<I4s',len(raw),b'BIN\x00')+raw
  path.write_bytes(struct.pack('<4sII',b'glTF',2,12+len(payload))+payload)

def run():
  with tempfile.TemporaryDirectory(prefix='mwni148-tests-') as tmp:
    r=pathlib.Path(tmp);good=r/'good.glb';static=r/'static.glb';unskinned=r/'unskinned.glb';glb(good,True);glb(static,False);glb(unskinned,True,False)
    g=glb_scan.scan(good,'Light1');n=glb_scan.scan(static,'Light1')
    assert g['movingJointCount']>=6 and g['animatedLimbs']
    assert n['movingJointCount']==0 and not n['animatedLimbs']
    other=glb_scan.scan(unskinned,'Light1')
    assert other['movingJointCount']<=1 and not other['animatedLimbs'], 'Animation of unskinned dummy bones falsely accepted'
    assert len(g['channelDetails'])==len(J)
    assert driver.validate_glb(good,driver.sha(good),good.stat().st_size)['skins']==1
    wrong=r/'wrong.glb';shutil.copyfile(good,wrong)
    raw=wrong.read_bytes();wrong.write_bytes(raw[:-1]+b'!')
    try:driver.validate_glb(wrong,driver.sha(good),good.stat().st_size)
    except RuntimeError:pass
    else:raise AssertionError('Tampered GLB accepted')
    try:glb_scan.scan(r/'not-existing.glb','Light1')
    except FileNotFoundError:pass
    else:raise AssertionError('Missing GLB accepted')
    # Supply names corresponding to previous bytes; invalid input must be blocked.
    bad=r/'dest';bad.write_text('unrelated user content')
    try:driver.safe_copy(good,bad)
    except RuntimeError:pass
    else:raise AssertionError('Destination overwrite allowed')
    fresh=r/'new.glb';driver.safe_copy(good,fresh)
    assert driver.sha(fresh)==driver.sha(good)
    driver.safe_copy(good,fresh)
    for c in ('Kick','Light1'):
      assert len(driver.INPUTS[c]['blend'])==64 and len(driver.INPUTS[c]['glb'])==64
    assert driver.V.endswith('v1.4.8')
    # Both publication paths and previous protected assets must be distinct.
    assert len(driver.SRC)==len(set(driver.SRC)) and not set(driver.SRC)&set(driver.LOCKED)
    assert len(driver.VARIANTS)==len(set(driver.VARIANTS))
    # Immutable source check confirms launcher isn't used as a substitute for a Git receipt.
    assert driver.BASE_COMMIT=='32d751466f940a0ad3d9caffae5a43db409ea7d0'
    # Real isolated Git fixture: source publication and exact remote readback,
    # then reject any attempt to republish different bytes at the same path.
    remote=r/'remote.git';work=r/'repo'; packet=r/'packet';packet.mkdir()
    def git(*args):
      run=subprocess.run(['git',*map(str,args)],capture_output=True,text=True)
      if run.returncode:raise AssertionError('git '+repr(args)+' '+run.stderr)
      return run.stdout.strip()
    git('init','--bare','--initial-branch=main',remote)
    git('clone',remote,work)
    git('-C',work,'config','user.name','Test Operator')
    git('-C',work,'config','user.email','test@example.invalid')
    (work/'baseline').write_text('source baseline\n')
    git('-C',work,'add','baseline');git('-C',work,'commit','-m','init baseline')
    git('-C',work,'push','origin','HEAD:refs/heads/main')
    launcher=r/'launcher.sh';launcher.write_text('#!/bin/sh\n')
    (packet/'test.py').write_text('print(1)\n')
    oldpaths=driver.SRC
    try:
      driver.SRC={'campaigns/test.sh':'LAUNCHER','tests/test.py':'test.py'}
      commit=driver.source_commit(work,launcher,packet)
      assert commit==git('-C',work,'rev-parse','HEAD')
      assert commit==git('--git-dir',remote,'rev-parse','refs/heads/main')
      assert driver.source_commit(work,launcher,packet)==commit
      (packet/'test.py').write_text('print(2)\n')
      try:driver.source_commit(work,launcher,packet)
      except RuntimeError as e:assert 'VERSIONED_SOURCE_COLLISION' in str(e)
      else:raise AssertionError('Versioned Git source overwrite accepted')
    finally:driver.SRC=oldpaths
    # Real localhost HTTP viewer. Verify no-cache identity, correct model hash,
    # and tampered URL failure, without network or Blender assumptions.
    (r/'viewer.html').write_text('<html>viewer</html>')
    ready=r/'ready.json';config=r/'config.json'
    with socket.socket() as sock:
      sock.bind(('127.0.0.1',0));port=sock.getsockname()[1]
    cfg={'runId':'test-export-parity','buildToken':'build123','sourceCommit':commit,
      'htmlPath':str(r/'viewer.html'),'modelPaths':{'candidateLight1':str(good)},
      'models':{'candidateLight1':{'sha256':driver.sha(good),'bytes':good.stat().st_size}},
      'launcherSHA256':'0'*64}
    config.write_text(json.dumps(cfg))
    cmd=[sys.executable,str(pathlib.Path(__file__).resolve().parent/'server.py'),
       '--config',str(config),'--ready',str(ready),'--port-base',str(port)]
    proc=subprocess.Popen(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
    try:
      for _ in range(65):
        if ready.exists():break
        if proc.poll() is not None:raise AssertionError('HTTP fixture server died: '+proc.stderr.read().decode())
        time.sleep(.06)
      assert ready.exists(),'HTTP server readiness missing'
      ticket=json.loads(ready.read_text());base='http://127.0.0.1:'+str(ticket['port'])
      with urllib.request.urlopen(base+'/manifest.json',timeout=4) as h:
        manifest=json.loads(h.read());assert manifest['buildToken']=='build123'
        assert 'no-store' in h.headers['Cache-Control']
      with urllib.request.urlopen(base+'/models/candidateLight1.glb',timeout=4) as h:
        assert hashlib.sha256(h.read()).hexdigest()==driver.sha(good)
        assert h.headers['X-Model-SHA256']==driver.sha(good)
      try:urllib.request.urlopen(base+'/models/stale.glb',timeout=3)
      except urllib.error.HTTPError as e:assert e.code==404
      else:raise AssertionError('Stale model key returned data')
    finally:
      proc.terminate()
      try:proc.wait(timeout=3)
      except subprocess.TimeoutExpired:proc.kill();proc.wait()
  print('TESTS_PASSED=GLTF_SKINNED_ROTATION_VALUES STATIC_NEGATIVE SHA_AND_COLLISION ISOLATED_GIT_REMOTE_READBACK HTTP_IDENTITY')
if __name__=='__main__':run()
