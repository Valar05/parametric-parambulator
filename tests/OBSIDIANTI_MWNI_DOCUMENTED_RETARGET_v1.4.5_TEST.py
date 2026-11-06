#!/usr/bin/env python3
"""Offline actual-server, tamper, stale-identity and content-delivery tests.
Not evidence that the owner's Android device has executed anything.
"""
import hashlib,importlib.util,json,os,pathlib,struct,subprocess,sys,tempfile,time,urllib.request,urllib.error

here=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('viewer_driver',here/'driver.py')
driver=importlib.util.module_from_spec(spec);spec.loader.exec_module(driver)

def fake_glb(path,name):
    info={'asset':{'version':'2.0'},'meshes':[{'primitives':[{'attributes':{}}]}],
          'skins':[{'joints':[0]}],'animations':[{'name':name}], 'nodes':[{'name':'root'}],
          'scenes':[{'nodes':[0]}],'scene':0}
    jsonb=json.dumps(info,separators=(',',':')).encode();jsonb+=b' '*((-len(jsonb))%4)
    chunk=struct.pack('<I4s',len(jsonb),b'JSON')+jsonb
    path.write_bytes(struct.pack('<4sII',b'glTF',2,12+len(chunk))+chunk)


def exercise():
    with tempfile.TemporaryDirectory(prefix='obs-mwni-documented-test-') as td:
        root=pathlib.Path(td);f=root/'model.glb';fake_glb(f,'Armature|Kick')
        digest=driver.sha(f);meta=driver.validate_glb(f,digest,f.stat().st_size)
        assert meta['animations']==['Armature|Kick'] and meta['skins']==1
        try:driver.validate_glb(f,'0'*64,f.stat().st_size)
        except RuntimeError:pass
        else:raise AssertionError('tampered SHA incorrectly accepted')
        try:driver.validate_glb(f,digest,f.stat().st_size+1)
        except RuntimeError:pass
        else:raise AssertionError('invalid byte count accepted')
        html=root/'index.html';html.write_text('<!doctype html>VIEWER_INTEGRITY_TEST')
        run='TEST_RUN_A';build='TEST_TOKEN_A';src='0123456789abcdef'*4
        cfg={'schema':'test','runId':run,'buildToken':build,'sourceCommit':src,
             'launcherSHA256':'a'*64,'htmlPath':str(html),
             'modelPaths':{'candidateKick':str(f)},'models':{'candidateKick':{
                 **meta,'url':'/models/candidateKick.glb','role':'test'}}}
        config=root/'manifest.json';config.write_text(json.dumps(cfg));ready=root/'ready.json';log=root/'log.txt'
        with log.open('w') as stdout:
            proc=subprocess.Popen([sys.executable,str(here/'server.py'),'--config',str(config),'--ready',str(ready),'--port-base','19180'],
                stdout=stdout,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL)
        try:
            for _ in range(100):
                if proc.poll() is not None:raise AssertionError('SERVER_FAILED '+log.read_text())
                if ready.is_file():break
                time.sleep(.05)
            else:raise AssertionError('SERVER_START_TIMEOUT')
            r=json.loads(ready.read_text());base='http://127.0.0.1:'+str(r['port'])
            assert r['runId']==run and r['buildToken']==build and r['pid']==proc.pid
            def request(url,method='GET'):
                with urllib.request.urlopen(urllib.request.Request(base+url,method=method),timeout=5) as response:
                    return response.read(),dict(response.headers)
            health,h=request('/health');assert json.loads(health)['pid']==proc.pid
            assert h['X-Obsidianti-Run']==run and h['X-Obsidianti-Build']==build
            page,h=request('/index.html');assert page==html.read_bytes()
            assert 'no-store' in h['Cache-Control']
            mf,h=request('/manifest.json');o=json.loads(mf)
            assert 'modelPaths' not in o and o['buildToken']==build
            data,h=request('/models/candidateKick.glb');assert data==f.read_bytes()
            assert h['X-Model-SHA256']==digest and 'no-store' in h['Cache-Control']
            _,h=request('/models/candidateKick.glb',method='HEAD');assert int(h['Content-Length'])==len(data)
            for path in ['/models/notReal.glb','/noSuchPage.html','/models/../manifest.json']:
                try:request(path)
                except urllib.error.HTTPError as err:assert err.code==404
                else:raise AssertionError('INVALID_ROUTE_ACCEPTED '+path)
            # A second server on the occupied initial port must not spoof the same process.
            ready2=root/'ready2.json'
            cfg2={**cfg,'runId':'TEST_RUN_B','buildToken':'TEST_TOKEN_B'}
            config2=root/'config2.json';config2.write_text(json.dumps(cfg2))
            with (root/'log2.txt').open('w') as out2:
                proc2=subprocess.Popen([sys.executable,str(here/'server.py'),'--config',str(config2),'--ready',str(ready2),'--port-base','19180'],
                    stdout=out2,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL)
            try:
                for _ in range(100):
                    if ready2.is_file():break
                    time.sleep(.05)
                assert ready2.is_file() and proc2.poll() is None
                r2=json.loads(ready2.read_text())
                assert r['port']!=r2['port'] and r2['buildToken']!=r['buildToken']
            finally:
                proc2.terminate();proc2.wait(timeout=3)
            print('TEST_OK_REAL_HTTP_MODEL_BYTES_HASH_HEADERS_STALE_RUN_PORT_COLLISION_AND_TAMPER',flush=True)
        finally:
            proc.terminate();proc.wait(timeout=3)

    # Git source-first publication and idempotent repeat against disposable bare remote.
    with tempfile.TemporaryDirectory(prefix='obs-mwni-documented-git-') as td:
        root=pathlib.Path(td);bare=root/'bare.git';checkout=root/'checkout'
        subprocess.run(['git','init','--bare','--initial-branch=main',str(bare)],check=True,stdout=subprocess.DEVNULL)
        subprocess.run(['git','clone',str(bare),str(checkout)],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        def git(*args):
            return subprocess.run(['git','-C',str(checkout),*args],check=True,capture_output=True,text=True).stdout.strip()
        git('config','user.name','Viewer Test');git('config','user.email','test@example.invalid')
        (checkout/'AGENTS.md').write_text('synthetic disposable test policy')
        git('add','AGENTS.md');git('commit','-m','start');git('push','origin','HEAD:refs/heads/main')
        launch=root/'LAUNCH.sh';launch.write_text('#!/bin/sh\necho SAFE\n')
        first=driver.source_commit(checkout,launch,here)
        assert first==git('rev-parse','HEAD')
        second=driver.source_commit(checkout,launch,here)
        assert first==second
        (checkout/next(iter(driver.SRC))).write_text('altered source content')
        try:driver.source_commit(checkout,launch,here)
        except RuntimeError as e:assert 'VERSIONED_SOURCE_COLLISION' in str(e)
        else:raise AssertionError('collision mutation not caught')
        print('TEST_OK_GIT_SOURCE_PUSH_REMOTE_READBACK_IDEMPOTENT_AND_COLLISION_REJECTION',flush=True)

def test_negative_control():
    import ast
    code=(here/'blender_trial.py').read_text()
    syntax=ast.parse(code)
    fun=next(x for x in syntax.body if isinstance(x,ast.FunctionDef) and x.name=='check')
    compiled=compile(ast.Module(body=[fun],type_ignores=[]),'<extracted-validator>','exec')
    scope={};exec(compiled,scope)
    parts=('LeftUpLeg','LeftLeg','LeftFoot','RightUpLeg','RightLeg','RightFoot','LeftArm','LeftForeArm','RightArm','RightForeArm','Spine','Spine2')
    src={p:20. for p in parts};dst={p:20. for p in parts}
    feet={s:{'sourceHipRelativeExcursion_m':.3,'targetHipRelativeExcursion_m':.3,'hipRelativeMotionErrorMax_m':.01,'maxAbsoluteFootWorldError_m':.01,'bestSoleContactDistance_m':.01} for s in ('Left','Right')}
    good={'sourceExcursionDegrees':src,'targetExcursionDegrees':dst,'maxAbsoluteFootSeparationMismatch_m':.03,'foot':feet}
    assert scope['check'](good,'Kick')==[]
    assert scope['check'](good,'Light1')==[]
    bad={**good,'targetExcursionDegrees':{p:0. for p in parts},'foot':{s:{**feet[s],'targetHipRelativeExcursion_m':0} for s in feet}}
    errors=scope['check'](bad,'Kick')
    assert 'KICK_NO_ARTICULATED_LEG' in errors and any(x.startswith('HIP_ONLY_') for x in errors)
    assert len(errors)>5
    misplaced={**good,'maxAbsoluteFootSeparationMismatch_m':.48,
        'foot':{side:{**good['foot'][side],'maxAbsoluteFootWorldError_m':.45,
                     'bestSoleContactDistance_m':.31} for side in ('Left','Right')}}
    wrong=scope['check'](misplaced,'Kick')
    assert 'FOOT_SEPARATION_MISMATCH_GT_22CM' in wrong
    assert 'FOOT_WORLD_POSITION_NOT_REACHED_Left' in wrong
    assert 'SHOE_NEVER_NEAR_REST_FLOOR_Right' in wrong
    print('TEST_OK_NEGATIVE_CONTROLS_HIP_ONLY_AND_FLOATING_MISPLACED_FEET_REJECTED',flush=True)

if __name__=='__main__':
    test_negative_control()
    exercise()

