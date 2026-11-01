"""Synthetic end-to-end v0.6.10 regression: intentionally not production model evidence.

Traverses ALL three candidate stages and the actual mid-swing verifier,
including signed joint angle checking, physical clearance gating, and
preservation of stance/hind/root channels. Uses a deterministic fake glTF
back end that prevents an early exit from concealing verifier bugs.
"""
import copy, hashlib, math, pickle

IDENTITY = (0.,0.,0.,1.)
NFRAMES = 97

def rotation_x(q):
    return math.degrees(2*math.atan2(q[0],q[3]))

def quat_x(deg):
    a=math.radians(deg)/2
    return (math.sin(a),0.,0.,math.cos(a))

class StubBase:
    def axisq(self,axis,deg):
        assert tuple(axis)==(1.,0.,0.)
        return quat_x(deg)
    def qmul(self,a,b):
        x,y,z,w=a; X,Y,Z,W=b
        return (w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,
                w*Z+x*Y-y*X+z*W,w*W-x*X-y*Y-z*Z)
    def world_matrices(self,doc,pose):
        names={v['name']:i for i,v in enumerate(doc['nodes'])}
        points=[(0.,0.,0.) for _ in doc['nodes']]
        for label,sh,mid,dist,hoof,sign in (
                ('LF','Bone_015','Bone_014','Bone_013','Bone_012',-1),
                ('RF','Bone_021','Bone_020','Bone_019','Bone_018',1)):
            a=rotation_x(pose[names[sh]]); b=rotation_x(pose[names[mid]])
            root=(sign*.14,1.2,.75)
            middle=(root[0],root[1]-.26*math.cos(math.radians(a)),
                      root[2]+.26*math.sin(math.radians(a)))
            lower=(middle[0],middle[1]-.22*math.cos(math.radians(a+b)),
                   middle[2]+.22*math.sin(math.radians(a+b)))
            points[names[sh]]=root;points[names[mid]]=middle
            points[names[dist]]=lower
            points[names[hoof]]=(lower[0],lower[1]-.18,lower[2]+.01)
        return [(1.,0.,0.,p[0],0.,1.,0.,p[1],0.,0.,1.,p[2],0.,0.,0.,1.) for p in points]
    def emit_accessor(self,doc,binary,rows,dtype,form):
        assert dtype==5126 and form=='VEC4' and len(rows)==97
        idx=str(len(doc.setdefault('_emitted',{})))
        doc['_emitted'][idx]=copy.deepcopy(rows)
        binary.extend(b'v')
        return idx
    def glb_encode(self,doc,binary):
        return pickle.dumps((doc,bytes(binary)),protocol=4)

class StubPrevious:
    class Blocked(RuntimeError):pass
    def parse_glb(self,source):
        return pickle.loads(source)
    def inspect_source(self,doc):
        assert len(doc['nodes'])==53 and len(doc['skins'][0]['joints'])==50
        assert len(doc['animations'])==6
        return {n['name']:i for i,n in enumerate(doc['nodes'])}
    def tracks(self,doc,binary,clip,base):
        out={}
        for key,obj in clip['_tracks'].items():
            sampler=obj['sampler']
            output=sampler['output']
            values=doc.get('_emitted',{}).get(output,obj['rows'])
            out[key]={'rows':values,'sampler':sampler}
        return out
    def hoof_witnesses(self,doc,binary,base,label):
        return (None,None,None,[0 if label=='LF' else 1])
    def angle(self,p,q):
        dot=min(1.,abs(sum(a*b for a,b in zip(p,q))))
        return math.degrees(2*math.acos(dot))

def make_source():
    nodes=[dict(name='Bone_%03d'%i,children=[]) for i in range(53)]
    nodes[0]['translation']=[0.,0.,0.]
    for chain in ([15,14,13,12],[21,20,19,18]):
        for a,b in zip(chain,chain[1:]):nodes[a]['children'].append(b)
    anim=[{'name':'other_'+str(i),'_tracks':{}} for i in range(3)]
    all_ids=[0,15,14,13,12,21,20,19,18,23,28]
    for stage in range(3):
        channels={}
        for node in all_ids:
            if node==0:
                key=(0,'translation')
                values=[(0.,0.,i*.01) for i in range(NFRAMES)]
            else:
                key=(node,'rotation')
                values=[IDENTITY]*NFRAMES
            channels[key]={'rows':values,'sampler':{'output':'source'}}
        anim.append({'name':'walk_'+str(stage),'_tracks':channels})
    doc={'asset':{'version':'2.0'},'nodes':nodes,'skins':[{'joints':list(range(50))}],
         'meshes':[{'primitives':[]}],'animations':anim}
    return pickle.dumps((doc,b'CANONICAL_BUFFER_PREFIX'),protocol=4)

def clearance_factory(model,passes):
    def underside(base,doc,binary,track,pose,root,frame,xyz,joints,weights,indices):
        mid='Bone_014' if indices[0]==0 else 'Bone_020'
        shoulder='Bone_015' if indices[0]==0 else 'Bone_021'
        names={v['name']:i for i,v in enumerate(doc['nodes'])}
        a=abs(rotation_x(pose[names[shoulder]]))
        b=abs(rotation_x(pose[names[mid]]))
        if a<.01 and b<.01:return 0.
        if not passes:return .001
        return .005 + .0022*b + .001*a
    return underside

def run_regressions(model):
    base=StubBase();old=StubPrevious();source=make_source()
    saved_sha=model.SOURCE_SHA; saved_underside=model.underside
    model.SOURCE_SHA=hashlib.sha256(source).hexdigest()
    try:
        model.underside=clearance_factory(model,True)
        result,report=model.make_candidate(source,base,old,(24,36))
        assert result and report['changed_channels']==12
        assert set(report['all_three_stages'])=={'1','2','3'}
        assert all(value=='PASS' for value in report['all_three_stages'].values())
        assert len(report['front_joint_angles'])>=12
        assert report['min_mid_clearance']>=model.MID_CLEARANCE
        assert report['min_early_clearance']>=model.EARLY_CLEARANCE
        assert report['preserved_rotations']>=3
        assert len(report['front_hoof_clearance'])==6
        model.underside=clearance_factory(model,False)
        try:
            model.verify(source,result,base,old,(24,36))
            raise AssertionError('CLEARANCE_FAIL_CANDIDATE_WAS_NOT_BLOCKED')
        except model.Blocked as exc:
            assert str(exc).startswith('CLEARANCE_MID_FRONT_HOOF_STILL_DRAGS:'),str(exc)
    finally:
        model.SOURCE_SHA=saved_sha
        model.underside=saved_underside
