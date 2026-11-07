#!/usr/bin/env python3
"""Run real GLB structural verification with intentionally synthetic action content.
Actual donor/canonical GLB success is verified only by the owner Termux campaign.
"""
import argparse,copy,math,pathlib,tempfile
import compose as c

VN=['0T-Pose','ClubIdle','Idle','Jump','JumpCrouch','JumpForward','Land',
    'LedgeClimb','LedgeGrab','LedgeGrabHang','Midair','MidairSwordAttack1',
    'MidairSwordAttack2','RunForwardOld','SpinAttack','SwordAttack1',
    'SwordAttack2','SwordAttack4','SwordAttack5']

def fixture(real,root):
    original,buf=c.read_glb(real)
    ids=c.name_ids(original)
    ref=original['animations'][0]
    assert ref['name']=='AxeKick_remap'
    assert len(original['meshes'])>=4
    j=copy.deepcopy(original)
    j['animations']=[]
    app=c.Appender(j,buf)
    run=copy.deepcopy(ref);run['name']='Running';app.js['animations'].append(run)
    guard={'name':c.GUARD,'channels':[],'samplers':[]}
    for bone in [c.HIPS,c.SPINE,'mixamorig:Spine1','mixamorig:Spine2',
                 'mixamorig:LeftArm','mixamorig:RightArm',
                 'mixamorig:LeftWeapon.L','mixamorig:RightWeapon.R']:
        i=ids[bone];base=original['nodes'][i].get('rotation',[0,0,0,1])
        app.add(guard,i,'rotation',[0,.033],[base,base])
    app.js['animations'].append(guard)
    idle={'name':c.AUTHORED,'channels':[],'samplers':[]}
    times=[i/30 for i in range(91)]
    for bone,amp in [('mixamorig:Spine1',.012),('mixamorig:Spine2',.016),('mixamorig:Neck',-.004)]:
        i=ids[bone];q=original['nodes'][i].get('rotation',[0,0,0,1])
        vals=[c.qm(q,(math.sin(.5*amp*math.sin(2*math.pi*t/3)),0,0,math.cos(.5*amp*math.sin(2*math.pi*t/3)))) for t in times]
        app.add(idle,i,'rotation',times,vals)
    app.js['animations'].append(idle)
    ghip=c.normq(c.at_time(app.js,app.bin,guard,ids[c.HIPS],'rotation',0))
    gsp=c.normq(c.at_time(app.js,app.bin,guard,ids[c.SPINE],'rotation',0))
    for ind,step in enumerate(c.STEPS):
        clip={'name':'Ares_'+step+'_Lower','channels':[],'samplers':[]}
        ts=[i*.8/24 for i in range(25)]
        hbase=ghip
        swing=[c.qm(hbase,(0,0,math.sin(.5*.035*math.sin(t*2*math.pi/.8)),math.cos(.5*.035*math.sin(t*2*math.pi/.8)))) for t in ts]
        app.add(clip,ids[c.HIPS],'rotation',ts,swing)
        app.add(clip,ids[c.SPINE],'rotation',ts,[c.qm(c.qm(c.qi(q),ghip),gsp) for q in swing])
        for bone in ['mixamorig:LeftUpLeg','mixamorig:RightUpLeg','mixamorig:LeftFoot','mixamorig:RightFoot']:
            b=ids[bone];q=c.at_time(original,buf,ref,b,'rotation',0)
            app.add(clip,b,'rotation',ts,[c.qm(q,(math.sin(.1*math.sin(t*2*math.pi/.8)),0,0,math.cos(.1*math.sin(t*2*math.pi/.8)))) for t in ts])
        app.js['animations'].append(clip)
    while len(app.js['animations'])<23:
        cpy=copy.deepcopy(ref);cpy['name']='Lionheart_OLD_'+str(len(app.js['animations']))
        app.js['animations'].append(cpy)
    assert len(app.js['animations'])==23
    canon=root/'canonical.glb';c.glb_save(app.js,bytes(app.bin),canon)
    v=copy.deepcopy(original);v['animations']=[copy.deepcopy(ref) for _ in VN]
    for x,n in zip(v['animations'],VN):x['name']='Vanguard_'+n
    # Vanguard source uses a shieldless export; only animation tracks are copied.
    # Delete an unreferenced mesh here to verify the merger does not copy donor mesh geometry.
    v['meshes']=v['meshes'][:-1]
    van=root/'vanguard.glb';c.glb_save(v,buf,van)
    return canon,van,real

def main():
    p=argparse.ArgumentParser();p.add_argument('--real',required=True)
    r=pathlib.Path(p.parse_args().real);assert r.is_file()
    with tempfile.TemporaryDirectory(prefix='obs30test-') as temp:
        root=pathlib.Path(temp);canon,van,kick=fixture(r,root)
        kw={'expected_source':c.digest(canon),'expected_vanguard':c.digest(van),'expected_axekick':c.digest(kick)}
        out=root/'done.glb';rep=root/'proof.json'
        result=c.compose(canon,van,kick,out,rep,**kw)
        assert result['count']==30 and result['shieldRetained'] and result['lanceRetained']
        assert len(result['vanguardVerified'])==19 and len(result['originalGuardedStepWitnesses'])==8
        j,b=c.read_glb(out)
        assert [a['name'] for a in j['animations']]==list(c.SELECT_CANON)+['Vanguard_'+n for n in VN]+['AxeKick']
        assert j['meshes']==c.read_glb(canon)[0]['meshes']
        assert len(j['meshes'])>len(c.read_glb(van)[0]['meshes'])
        print('PASS: 30 clips, original guarded Ares steps, 3s animated idle, shield mesh retained, Vanguard 19, accepted AxeKick')
        try:c.compose(canon,van,kick,root/'bad.glb',root/'bad.json',expected_source='0'*64,
                      expected_vanguard=kw['expected_vanguard'],expected_axekick=kw['expected_axekick'])
        except ValueError as e:assert 'SHA_MISMATCH' in str(e)
        else:raise AssertionError('WRONG_SHA_ACCEPTED')
        try:c.compose(canon,van,kick,out,root/'twice.json',**kw)
        except ValueError as e:assert 'OUTPUT_COLLISION' in str(e)
        else:raise AssertionError('COLLISION_ACCEPTED')
        bad,_=c.read_glb(van);bad['animations'].pop()
        badpath=root/'missing.glb';c.glb_save(bad,b,badpath)
        try:c.compose(canon,badpath,kick,root/'miss.glb',root/'miss.json',
                      expected_source=kw['expected_source'],expected_vanguard=c.digest(badpath),expected_axekick=kw['expected_axekick'])
        except ValueError as e:assert 'VANGUARD_ACTION_INVENTORY_INVALID' in str(e)
        else:raise AssertionError('MISSING_ACTION_ACCEPTED')
        print('PASS: wrong SHA, collision, and missing Vanguard action are rejected')
    print('V230_30_CLIP_REAL_RIG_TESTS_OK')
if __name__=='__main__':main()
