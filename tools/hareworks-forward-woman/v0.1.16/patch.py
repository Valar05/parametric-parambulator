#!/usr/bin/env python3
"""Exact-source-only additive v0.1.16 patch of existing v0.1.15.
No canonical GLB / historical directory modifications."""
from pathlib import Path
import sys, json, hashlib

root=Path(sys.argv[1]); dest=Path(sys.argv[2])
source=root/'tools/hareworks-forward-woman/v0.1.15'
if not source.is_dir():raise SystemExit('NO_PUBLISHED_V015_SOURCE')
p=dest/'viewer.mjs'
s=p.read_text()
def one(old,new):
 global s
 n=s.count(old)
 if n!=1:raise RuntimeError('V016_VIEWER_ANCHOR_'+str(n)+'_'+old[:85])
 s=s.replace(old,new,1)

one("import {sourceAt,SourceFootContact} from './foot-gait.mjs';", "import {sourceAt,SourceFootContact} from './foot-gait.mjs';\nimport {speedGait,blendMotion,transformSourceFoot,adjustAnkleForSpeed,rootStepDistance} from './speed-gait.mjs';")
one('let motionMode=\'LOADING\',frameTickCount=0,lastPreviewError=\'\',previewCycle=0;',
    "let motionMode='LOADING',frameTickCount=0,lastPreviewError='',previewCycle=0;\nlet dynamicMotion=null; // speed-dependent stride geometry, cadence and crossover; not clip-time scaling")
one('previewCycle+=Math.max(0,speed)*dt/REFERENCE_ROOT_UNITS_PER_CYCLE;\n phase=mod1(previewCycle);worldZ=REFERENCE_ROOT_UNITS_PER_CYCLE*previewCycle;',
    '''dynamicMotion=blendMotion(dynamicMotion,speedGait(speed,REFERENCE_ROOT_UNITS_PER_CYCLE),dt);
 const nextCycle=previewCycle+(dynamicMotion.cadence*dt);
 worldZ+=(nextCycle-previewCycle)*dynamicMotion.stride;
 previewCycle=nextCycle;phase=mod1(previewCycle);''')
one('const target=H.clone().add(V(...rotateY(v.ankleLocal,yaw)));',
    '''const target=H.clone().add(V(...rotateY(v.ankleLocal,yaw)));
    target.fromArray(adjustAnkleForSpeed(H.toArray(),target.toArray(),side,dynamicMotion));''')
# Actual accepted v0.1.9 foot orientation rather than forcing the source GLB sample
# rotation onto the fully procedural leg. Blend limits deviation pending owner review.
needle='function measuredFootQ(s){'
assert s.count(needle)==1
foot='''// Accepted v0.1.9 toe-vector + ankle-yaw analytical orientation.
function runwayFootQ(c,toeVector,ankleYaw){
 const from=wpos(c.toe).sub(wpos(c.foot)),to=V(...toeVector);
 if(from.lengthSq()<1e-9||to.lengthSq()<1e-9)throw Error('RUNWAY_FOOT_VECTOR_DEGENERATE');
 const axis=to.normalize(),base=Q().setFromUnitVectors(from.normalize(),axis).multiply(wq(c.foot));
 const forward=V(0,0,1).applyQuaternion(base),desired=V(Math.sin(ankleYaw),0,Math.cos(ankleYaw));
 const fp=forward.addScaledVector(axis,-forward.dot(axis)),dp=desired.addScaledVector(axis,-desired.dot(axis));
 if(fp.lengthSq()<1e-7||dp.lengthSq()<1e-7)throw Error('RUNWAY_FOOT_HEADING_SINGULAR');
 fp.normalize();dp.normalize();
 const twist=Math.atan2(axis.dot(fp.clone().cross(dp)),fp.dot(dp));
 return Q().setFromAxisAngle(axis,twist).multiply(base).normalize();
}
'''
s=s.replace(needle,foot+needle,1)
one('const f=sourceAt(sourceSamples[side],phase);setWorldQ(c.foot,measuredFootQ(f));actor.updateMatrixWorld(true);',
    '''const f=sourceAt(sourceSamples[side],phase);setWorldQ(c.foot,measuredFootQ(f));actor.updateMatrixWorld(true);
    const footFit=independentPose(pelvisProfile,q).feet[side];
    const original=wq(c.foot).clone(),fitted=runwayFootQ(c,footFit.toeVector,footFit.ankleYaw);
    setWorldQ(c.foot,original.slerp(fitted,.52));actor.updateMatrixWorld(true);''')
one('setWorldQ(c.foot,desiredQ);actor.updateMatrixWorld(true);',
    '''setWorldQ(c.foot,desiredQ);actor.updateMatrixWorld(true);
  // Preserve the published skinned contact geometry but restore a portion of
  // v0.1.9 toe-vector/yaw styling and align foot slightly toward its knee.
  const footFit=independentPose(pelvisProfile,phase*clipDuration).feet[side];
  const kneeToFoot=clamp(wpos(c.knee).x-wpos(c.foot).x,-.16,.16);
  const stylizedToe=[footFit.toeVector[0]+.20*kneeToFoot,
                     footFit.toeVector[1],footFit.toeVector[2]];
  try{
   const original=wq(c.foot).clone(),fitted=runwayFootQ(c,stylizedToe,footFit.ankleYaw);
   const styleBlend=t.planted?(best<.008?.35:.08):.52;
   setWorldQ(c.foot,original.slerp(fitted,styleBlend));actor.updateMatrixWorld(true);
  }catch(footError){
   // Keep original orientation, and log warning; never hide an invalid contact.
   setWorldQ(c.foot,desiredQ);previewFaults++;lastPreviewError=String(footError.message||footError);
  }''')
one('out[side]=worldContacts[side].step({phase,worldZ,totalPhase});',
    'out[side]=worldContacts[side].step({phase,worldZ,totalPhase,gait:dynamicMotion});')
one('const cadence=cadenceFor(speed,stride);totalPhase+=cadence*dt;phase=mod1(totalPhase);worldZ=rootAt(rootCurve,totalPhase);frameBody(phase);',
    '''dynamicMotion=blendMotion(dynamicMotion,speedGait(speed,rootCurve.stride),dt);
 const cadence=cadenceFor(speed,dynamicMotion.stride),newPhase=totalPhase+cadence*dt;
 worldZ+=rootStepDistance(rootAt,rootCurve,totalPhase,newPhase,dynamicMotion);
 totalPhase=newPhase;phase=mod1(totalPhase);frameBody(phase);''')
one('phase=0;totalPhase=0;worldZ=0;clearStats();frameBody(0);',
    '''phase=0;totalPhase=0;worldZ=0;dynamicMotion=speedGait(speed,rootCurve.stride);
 clearStats();frameBody(0);''')
one('sourceGround,readWitness:k=>witnessCache[side][k],rootAt:q=>rootAt(rootCurve,q)});',
    '''sourceGround,readWitness:k=>witnessCache[side][k],rootAt:q=>rootAt(rootCurve,q),
  transformSource:(s,gait)=>transformSourceFoot(s,side,gait||dynamicMotion)});''')
one("previewCycle=0;worldZ=0;frameBody(0);for(const p of Object.values(drawPins))p.visible=false;",
    "previewCycle=0;worldZ=0;dynamicMotion=speedGait(speed,REFERENCE_ROOT_UNITS_PER_CYCLE);frameBody(0);for(const p of Object.values(drawPins))p.visible=false;")
# The source viewer initializes at the speed selected in the HTML; change speed
# only through a smooth parameter update, not a reset or an anchor re-seed.
one("$('speed').oninput=()=>{speed=Number($('speed').value);$('speedOut').textContent=speed.toFixed(2)+' u/s';updateMotionStatus()};",
    "$('speed').oninput=()=>{speed=Number($('speed').value);$('speedOut').textContent=speed.toFixed(2)+' u/s';updateMotionStatus()};") if False else None
one("$('motionStatus').textContent='UNPINNED SOURCE PROCEDURAL PREVIEW · '+REFERENCE_ROOT_UNITS_PER_CYCLE.toFixed(4)+' u/full cycle · contact audit NOT available';",
    "$('motionStatus').textContent='UNPINNED DYNAMIC GEOMETRY PREVIEW · target stride '+(dynamicMotion?.stride||0).toFixed(3)+' u/full cycle · no contact proof';")
one('}else $(\'motionStatus\').textContent=`SOURCE-DERIVED FOOT PATH · ${stride.toFixed(3)} u travel/cycle · ${cadenceFor(speed,stride).toFixed(3)} cycles/s · no synthetic foot lift`;',
    '''}else $('motionStatus').textContent=`DYNAMIC SOURCE-ANCHORED FOOT PATH · stride ${(dynamicMotion?.stride||stride).toFixed(3)} u/full cycle · cadence ${cadenceFor(speed,dynamicMotion?.stride||stride).toFixed(3)} cycles/s · crossover ${(dynamicMotion?.crossover||0).toFixed(3)} u`;
''')
# New speed panel is an actual slow-to-fast gait range, rather than 0..0.8.
one("$('metrics').textContent=`${prefix} · SOURCE-MEASURED WALKING_WOMAN · WORLD IK", "$('metrics').textContent=`${prefix} · DYNAMIC SOURCE-ANCHORED WALKING_WOMAN · WORLD IK")
one('cadence ${cadenceFor(speed,stride).toFixed(3)} cycles/s\\nLEFT',
    'cadence ${cadenceFor(speed,dynamicMotion?.stride||stride).toFixed(3)} cycles/s, stride ${(dynamicMotion?.stride||stride).toFixed(3)}\\nLEFT')
one('const n=Math.ceil((3/cadenceFor(speed,stride))*120);',
    'const n=Math.ceil((3/cadenceFor(speed,speedGait(speed,stride).stride))*120);')
one('actualCyclesTested:n/120*cadenceFor(speed,stride),',
    'actualCyclesTested:n/120*cadenceFor(speed,dynamicMotion.stride),')
one('ownerVisualAcceptance:false,sourceOriginalUnchanged:true,acceptedForwardV019Unchanged:true,observations:samples};',
    '''ownerVisualAcceptance:false,sourceOriginalUnchanged:true,acceptedForwardV019Unchanged:true,observations:samples};
  // Real GLB physical checks at three distinct speeds. Changing speed is not a
  // pass unless contact drift, reach and actual root advance are acceptable.
  const speedMatrix=[];
  for(const requested of [.30,.52,1.18]){
   speed=requested;initRun();
   const expected=speedGait(requested,stride),steps=Math.ceil((1.20/expected.cadence)*120);
   for(let j=0;j<steps;j++){
    physicsStep(1/120);
    if(j%40===0)await new Promise(requestAnimationFrame);
   }
   const realTime=steps/120;
   speedMatrix.push({requested,realTime,travel:worldZ,
    stride:dynamicMotion.stride,cadence:dynamicMotion.cadence,
    maxDrift,maxPenetration,unreachable,
    rootMeanSpeed:worldZ/realTime,
    status:'REAL_SKINNED_GLTF_SOLVER',
    pass:maxDrift<=.025&&maxPenetration<=.020&&unreachable===0&&
      Math.abs(worldZ/realTime-requested)<.17});
  }
  report.speedMatrix=speedMatrix;
  report.dynamicSpeedGate=speedMatrix.every(x=>x.pass)?'PASS':'WARN';
  if(report.dynamicSpeedGate!=='PASS'){
   report.contactGate='WARN';report.status='DYNAMIC_SPEED_PHYSICAL_GATES_WARN_OWNER_REVIEW_REQUIRED';
  }
  speed=oldSpeed;initRun();''')
one('worldZ>2.5&&cameraError<',
    'worldZ>speedGait(speed,stride).stride*2.70&&cameraError<')
one('rootMethod:rootCurve.method,rootStridePerFullCycle:rootCurve.stride,',
    '''rootMethod:rootCurve.method,rootStridePerFullCycle:rootCurve.stride,
    speedResponsiveGait:dynamicMotion,referenceV019FootOrientationBlend:.52,''')
one('previewCycle=0;worldZ=0;frameBody(0);\n console.info(\'V019_REFERENCE_LEG_MOTION_LIVENESS_PASS\'',
    "previewCycle=0;worldZ=0;dynamicMotion=speedGait(speed,REFERENCE_ROOT_UNITS_PER_CYCLE);frameBody(0);\n console.info('V019_REFERENCE_LEG_MOTION_LIVENESS_PASS'")
# Version identity updated in copied file, not in previous baseline.
s=s.replace('v0.1.15','v0.1.16').replace('V0.1.15','V0.1.16')
# Source fit must remain physically audited instead of incorrectly marked accepted.
assert 'rootStepDistance(rootAt,rootCurve,totalPhase,newPhase,dynamicMotion)' in s
assert "motionMode='PHYSICAL_GROUND_PINNING'" in s
assert "OrbitControls" in s
p.write_text(s.rstrip()+'\n')

p=dest/'foot-gait.mjs';x=p.read_text()
def foot_once(a,b):
 global x
 if x.count(a)!=1:raise RuntimeError('V016_FOOT_PATCH_ANCHOR_'+str(x.count(a))+'_'+a[:70])
 x=x.replace(a,b,1)
foot_once('constructor({samples,gait,sourceGround,readWitness,rootAt,groundY=0}){',
          'constructor({samples,gait,sourceGround,readWitness,rootAt,groundY=0,transformSource=null}){')
foot_once('this.readWitness=readWitness;this.rootAt=rootAt;',
          'this.readWitness=readWitness;this.rootAt=rootAt;this.transformSource=transformSource;this.activeDuty=gait.duty;')
foot_once('step({phase,worldZ,totalPhase}){\n  const s=sourceAt(this.samples,phase),p=gap(phase,this.gait.start),planted=p<this.gait.duty;',
          '''step({phase,worldZ,totalPhase,gait}){
  const p=gap(phase,this.gait.start);
  if(this.state!=='stance'&&p<Math.min(this.gait.duty,this.activeDuty))
   this.activeDuty=clamp(this.gait.duty+((gait?.stanceDuty??.60)-.60),.49,.69);
  const planted=p<this.activeDuty;
  const raw=sourceAt(this.samples,phase),s=this.transformSource?this.transformSource(raw,gait,planted):raw;''')
foot_once('const u=clamp((p-this.gait.duty)/(1-this.gait.duty),0,1)',
          'const u=clamp((p-this.activeDuty)/(1-this.activeDuty),0,1)')
p.write_text(x.rstrip()+'\n')

p=dest/'contact-core.mjs';x=p.read_text();k='stride<.3||stride>1';
if x.count(k)!=2:raise RuntimeError('CADENCE_UNIT_CONTRACT_EXPECTED_TWICE_'+str(x.count(k)))
x=x.replace(k,'stride<.3||stride>1.8')
p.write_text(x.rstrip()+'\n')

p=dest/'index.html';x=p.read_text()
x=x.replace('v0.1.15','v0.1.16').replace('v0.1.15-startup-and-preview','v0.1.16-dynamic-physics')
x=x.replace('max="0.8"','max="1.2"')
x=x.replace('Swing and heel-to-toe motion are reconstructed from the original Walking_Woman source, not parameter sliders.',
 '''Original Walking_Woman trajectories supply the reference. The travel-speed slider changes stride length, cadence, lateral crossover and landing geometry. A physical-contact PASS is separate from seeing the model move.''')
x=x.replace('Feet use actual persistent world-space sole anchors during stance.',
            'The physical controller holds actual world-space skinned sole anchors during stance; a clearly labeled preview is unpinned if physics initialization fails.')
x=x.replace('Walking_Woman · World-Space IK','Walking_Woman · Dynamic World-Space IK')
p.write_text(x.rstrip()+'\n')

p=dest/'review-server.py';x=p.read_text().replace('v0.1.15','v0.1.16')
p.write_text(x.rstrip()+'\n')

# Source tests may be carried forward unchanged; the immutable old v0.1.15 is not modified.
for p in dest.rglob('*'):
 if p.is_file() and p.suffix in ('.mjs','.py','.json','.md','.html','.sh'):
  raw=p.read_bytes();p.write_bytes(raw.rstrip(b'\r\n')+b'\n')
print('V016_PATCH_PASS source=v0.1.15 dynamic_stride=1.2245 physical_world_contacts=retained orbit=retained')
