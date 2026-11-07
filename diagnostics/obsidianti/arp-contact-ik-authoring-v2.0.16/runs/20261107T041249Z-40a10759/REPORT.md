# Obsidianti ARP moving-hips + first-frame mesh contact + editable foot IK (v2.0.16)

Status: ALL_21_SOURCE_ACTIONS_PRESENT; no canonical GLB mutation.

## Configuration

Purchased Auto-Rig Pro 3.79.17; Auto-Scale ON; Hips Set As Root ON; Hips Location ON. Source runner derived from v2.0.12; source-action slot fixed; NO animation auto-cleanup. Each retarget is vertically shifted at the first frame by actual weighted shoe geometry, no intra-clip motion modification. AxeKick is exact earlier GLB data without IK or new retarget.

## Evidence

Keys: KEYS.json. True sampled source and target hip and foot joint paths: TRAJECTORIES.json.

Review GLB: OBSIDIANTI_ARP_CONTACT_IK_AUTHORING_v2.0.16_20261107T041249Z-40a10759_REVIEW_LIBRARY.glb (SHA-256 e7f60fea731fd9537380868adbb52fee63df34fdf1b6d7694bc39925b440fa1d).

Viewer: http://127.0.0.1:9202/index.html?run=20261107T041249Z-40a10759&build=c6b77676aef6c6d3c176e989

Original Heavy1 remains under Heavy1_old_ARP; new Heavy1 has moving hips and grounded foot mesh.

Editable Blender authoring rig: CREATED with always-on foot IK constraints. Pose parity: True.

## Results

- Lionheart_Idle: EXPORTED
- Lionheart_Cast: EXPORTED
- Lionheart_Heavy1: EXPORTED
- Lionheart_Heavy2: EXPORTED
- Lionheart_Heavy3: EXPORTED
- Lionheart_Kick: EXPORTED
- Lionheart_Light1: EXPORTED
- Lionheart_Light2: EXPORTED
- Lionheart_Light3: EXPORTED
- Lionheart_SpringAttack: EXPORTED
- Lionheart_Stomp: EXPORTED
- Ares_Idle: EXPORTED
- Ares_Cross: EXPORTED
- Ares_StepForward: EXPORTED
- Ares_StepBack: EXPORTED
- Ares_StepLeft: EXPORTED
- Ares_StepRight: EXPORTED
- Ares_StepForwardLeft: EXPORTED
- Ares_StepForwardRight: EXPORTED
- Ares_StepBackLeft: EXPORTED
- Ares_StepBackRight: EXPORTED

AxeKick: accepted exact control, not re-retargeted.
No acceptance claim for any newly retargeted animation.
Previous action fallbacks (not fixed, only preserved): {}
