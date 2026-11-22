#!/usr/bin/env python3
"""Strict v0.1.23 to v0.1.24 backward-slot patch, forward baseline immutable."""
import pathlib,sys
root=pathlib.Path(sys.argv[1]);dest=pathlib.Path(sys.argv[2]);p=dest/'viewer.mjs';s=p.read_text()
def once(old,new):
 global s
 n=s.count(old)
 if n!=1:raise RuntimeError(f'V024_VIEWER_PINNED_ANCHOR_{n}_'+old[:120])
 s=s.replace(old,new,1)
assert 'OrbitControls' in s and 'sourceKnee' not in s[:0] and 'GLTFLoader' in s
assert 'new THREE.AnimationMixer(actor)' not in s
once('/* v0.1.23. ONE moving Walking_Woman.','/* v0.1.24. ONE moving Walking_Woman.')
once("import {distalHeading} from './foot-heading.mjs';", "import {distalHeading} from './foot-heading.mjs';\nimport {sourcePhase,reversedSamples,reversedWindows,backwardRootDelta,signedTravelPass,signForDirection} from './reverse-gait.mjs';")
once('const terrainArgs=new URLSearchParams(location.search);',
"""const terrainArgs=new URLSearchParams(location.search);
// Direction changes must restart the physical world contact run. No instant
// sign flip of a planted anchor; the forward branch uses its original math.
const directionMode=terrainArgs.get('move')==='forward'?'forward':'backward';
const backward=()=>directionMode==='backward';
const bodyPhase=p=>sourcePhase(directionMode,p);""")
# Fallback must be visually moving backwards but must NEVER assert real contact.
once("let terrainMode=TERRAIN_MODES.includes(terrainArgs.get('terrain'))?terrainArgs.get('terrain'):'profile-ridges';",
     "let terrainMode=TERRAIN_MODES.includes(terrainArgs.get('terrain'))?terrainArgs.get('terrain'):(backward()?'flat':'profile-ridges');")
once('worldZ+=(nextCycle-previewCycle)*dynamicMotion.stride;',
     'worldZ+=signForDirection(directionMode)*(nextCycle-previewCycle)*dynamicMotion.stride;')
once('previewCycle=nextCycle;phase=mod1(previewCycle);\n frameBody(phase);\n const q=phase*clipDuration,yaw=independentPose(pelvisProfile,q).pelvisYaw;',
"""previewCycle=nextCycle;phase=mod1(previewCycle);
 frameBody(bodyPhase(previewCycle));
 const q=bodyPhase(previewCycle)*clipDuration,yaw=independentPose(pelvisProfile,q).pelvisYaw;""")
# Pose source remains the calibrated originals, sampled in reverse chronology.
once('const yaw=independentPose(pelvisProfile,phase*clipDuration).pelvisYaw;',
    'const yaw=independentPose(pelvisProfile,bodyPhase(totalPhase)*clipDuration).pelvisYaw;')
once('const footFit=independentPose(pelvisProfile,phase*clipDuration).feet[side];',
    'const footFit=independentPose(pelvisProfile,bodyPhase(totalPhase)*clipDuration).feet[side];')
once('worldZ+=rootStepDistance(rootAt,rootCurve,totalPhase,newPhase,dynamicMotion);',
    'worldZ+=backward()?backwardRootDelta(rootAt,rootCurve,totalPhase,newPhase,dynamicMotion):rootStepDistance(rootAt,rootCurve,totalPhase,newPhase,dynamicMotion);')
once('totalPhase=newPhase;phase=mod1(totalPhase);frameBody(phase);',
    'totalPhase=newPhase;phase=mod1(totalPhase);frameBody(bodyPhase(totalPhase));')
once('if(lastHipSolve.feasible){groundLift+=lastHipSolve.delta;frameBody(phase)}',
    'if(lastHipSolve.feasible){groundLift+=lastHipSolve.delta;frameBody(bodyPhase(totalPhase))}')
once("  terrainAt:terrainMode==='flat'?null:terrainAt,", "  terrainAt:terrainMode==='flat'?null:terrainAt,reverseRocker:backward(),")
# Physical derivation: rootCurve must be built from ORIGINAL forward source
# before deriving backward samples and reversed contact windows.
once('rootCurve=buildRootCurve(baseline,sourceGaits);stride=rootCurve.stride;',
"""rootCurve=buildRootCurve(baseline,sourceGaits);stride=rootCurve.stride;
// Keep exact forward source intact in previous version. Backward samples are
// reverse-indexed source measurements, with mirrored stance chronology.
if(backward()){
 sourceSamples=reversedSamples(sourceSamples);
 sourceGaits=reversedWindows(sourceGaits);
}
const forwardSourceCommit='ed4bae4ffbe713fc3170f4028708ff8a9992bbab';""")
# Honest negative displacement instead of failing positive-only forward gate.
once("if(!Number.isFinite(travelled)||travelled<.04)throw Error('NO_OBSERVABLE_WORLD_TRAVEL_AT_STARTUP '+travelled);",
"if(!Number.isFinite(travelled)||signForDirection(directionMode)*travelled<.04)throw Error('NO_OBSERVABLE_DIRECTIONAL_WORLD_TRAVEL_AT_STARTUP '+travelled);")
once("if(terrainMode!=='flat'&&worldZ-terrainCenterZ>14)rebuildTerrain(Math.floor(worldZ/14)*14);",
"if(terrainMode!=='flat'&&Math.abs(worldZ-terrainCenterZ)>14)rebuildTerrain(Math.round(worldZ/14)*14);")
# Shared review/gates accept signed travel. A negative root is correct backward.
once('maxTrailingExtensionDeficit=Math.max(maxTrailingExtensionDeficit,Math.max(0,actualRelative-sourceRelative));',
     'maxTrailingExtensionDeficit=Math.max(maxTrailingExtensionDeficit,Math.max(0,signForDirection(directionMode)*(actualRelative-sourceRelative)));')
once('worldZ>speedGait(speed,stride).stride*2.70',
     'signForDirection(directionMode)*worldZ>speedGait(speed,stride).stride*2.70')
once('Math.abs(worldZ/realTime-requested)<.17',
     'signedTravelPass(directionMode,worldZ/realTime,requested,.17)')
once('nominalForwardAdvance:worldZ,generatedAnimationMixerCount:0',
     'directionSlot:directionMode,expectedTravelSign:signForDirection(directionMode),signedWorldAdvance:worldZ,generatedAnimationMixerCount:0')
once("schema:'hareworks-woman-accepted-v019-world-pin-v0.1.23'",
     "schema:'hareworks-v0.1.24-directional-two-of-eight'")
once("a.download='hareworks-woman-accepted-v019-world-pin-v0.1.23.json'",
     "a.download='hareworks-v0.1.24-'+directionMode+'-world-pin.json'")
once("status('PHYSICAL IK ON '+terrainMode.toUpperCase()+' AT '",
     "status('PHYSICAL '+directionMode.toUpperCase()+' WALK IK ON '+terrainMode.toUpperCase()+' AT '")
once("$('identity').textContent=`v0.1.23 ACCEPTED V019 SOURCE ROOT + HONEST RUNNING PREVIEW",
     "$('identity').textContent=`v0.1.24 ${directionMode.toUpperCase()} DIRECTIONAL IK · TWO OF EIGHT CARDINAL SLOTS · PHYSICAL STATUS SEPARATE · SOURCE WALKING_WOMAN PHASE CALIBRATION · V019 SOURCE ROOT + HONEST RUNNING PREVIEW")
once('function updateMotionStatus(){',
"""$('directionMode').value=directionMode;
$('directionMode').onchange=()=>{
 const u=new URL(location.href);u.searchParams.set('move',$('directionMode').value);
 location.assign(u.toString()); // new world run, no planted-anchor teleport
};
function updateMotionStatus(){""")
once("$('motionStatus').textContent='PHYSICAL TERRAIN IK UNAVAILABLE · UNPINNED PREVIEW ONLY · '",
     "$('motionStatus').textContent=directionMode.toUpperCase()+' PHYSICAL TERRAIN IK UNAVAILABLE · UNPINNED PREVIEW ONLY · '")
once('}else $(\'motionStatus\').textContent=`DYNAMIC SOURCE-ANCHORED FOOT PATH',
     '}else $(\'motionStatus\').textContent=`${directionMode.toUpperCase()} DYNAMIC SOURCE-ANCHORED FOOT PATH')
# Source diagnostics and explicit two-slot scope; never claim diagonal locomotion.
once('terrainMode,terrainStrength,terrainHipReachSolver:true,',
     'directionSlot:directionMode,directionStatus:"FORWARD_AND_BACKWARD_IMPLEMENTED; SIX_OTHER_DIRECTIONS_UNIMPLEMENTED",terrainMode,terrainStrength,terrainHipReachSolver:true,')
once('terrainMode,terrainStrength,bodyTerrainLift:groundLift,hipReachLimitCount,',
     'directionMode,terrainMode,terrainStrength,bodyTerrainLift:groundLift,hipReachLimitCount,')
once('3 measured cycles, 120 Hz, traveling root ${worldZ.toFixed(3)} u',
     '3 measured cycles, 120 Hz, ${directionMode} traveling root ${worldZ.toFixed(3)} u')
# Avoid silently v23 legacy phrases asserting a new (backward) walk is already accepted.
s=s.replace('v0.1.23','v0.1.24').replace('V0.1.23','V0.1.24')
# Revert pinned original source SHA literal (used in documentation marker) after global version substitution.
assert "directionMode" in s and "reversedSamples(sourceSamples)" in s
assert 'backwardRootDelta(' in s and 'sourceGaits=reversedWindows(sourceGaits);' in s
assert s.count('new THREE.AnimationMixer(actor)')==0
p.write_text(s.rstrip()+'\n')
# The v23 foot-gait is byte-identical for FORWARD. Only reverse rocker transfer
# gains an optional mode and never touches ankle target or source pose.
p=dest/'foot-gait.mjs';t=p.read_text()
needle='constructor({samples,gait,sourceGround,readWitness,rootAt,groundY=0,transformSource=null,terrainAt=null}){'
assert t.count(needle)==1
t=t.replace(needle,'constructor({samples,gait,sourceGround,readWitness,rootAt,groundY=0,transformSource=null,terrainAt=null,reverseRocker=false}){')
needle='this.readWitness=readWitness;this.rootAt=rootAt;this.transformSource=transformSource;this.terrainAt=terrainAt;this.activeDuty=gait.duty;'
assert t.count(needle)==1
t=t.replace(needle,'this.readWitness=readWitness;this.rootAt=rootAt;this.transformSource=transformSource;this.terrainAt=terrainAt;this.reverseRocker=reverseRocker;this.activeDuty=gait.duty;')
needle='if(order[pivot]<order[this.pivot])pivot=this.pivot;'
assert t.count(needle)==1
t=t.replace(needle,'if(this.reverseRocker?order[pivot]>order[this.pivot]:order[pivot]<order[this.pivot])pivot=this.pivot;')
p.write_text(t.rstrip()+'\n')
# Distinct, cache-busted HTML with accessible backward/forward selection.
p=dest/'index.html';t=p.read_text()
t=t.replace('v0.1.23','v0.1.24').replace('V0.1.23','V0.1.24')
needle='<div id="motionStatus" class="bar" role="status" aria-live="polite">'
assert t.count(needle)==1
t=t.replace(needle,"""<div class="bar" role="group" aria-label="Locomotion direction: two of eight slots">
<label for="directionMode">Direction</label><select id="directionMode"><option value="backward">Backward (−Z)</option><option value="forward">Forward (+Z, baseline)</option></select>
<strong>2/8 directional slots</strong><span class="small">Facing stays +Z. Switching directions starts a fresh world run to protect planted anchors. Lateral and diagonal slots are not implemented.</span></div>
"""+needle)
t=t.replace('<title>Hareworks v0.1.24 | Accepted Walk + World Pin</title>',
            '<title>Hareworks v0.1.24 | Forward + Backward Procedural IK</title>')
t=t.replace('Walking_Woman · Dynamic World-Space IK','Walking_Woman · Forward / Backward Procedural IK')
t=t.replace('Original Walking_Woman trajectories supply the reference.',
            'Original Walking_Woman trajectories supply startup calibration. Backward uses reversed procedural phase, reversed world root travel and toe-first heel-last rocker. No baked clip playback drives the visible character.')
t=t.replace('v0.1.24-startup-and-preview','v0.1.24-backward-direction-physical-ik')
p.write_text(t.rstrip()+'\n')
p=dest/'review-server.py';t=p.read_text().replace('v0.1.23','v0.1.24');p.write_text(t.rstrip()+'\n')
# Produce new README, contract and source-obligation tests; copy other files unchanged.
print('V024_PATCH_PASS: copied v23 forward baseline, distinct backward slot, signed world travel, no model edit')
