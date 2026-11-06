# Obsidianti Mwni documented test v1.4.7

Source-only retarget experiment; canonical GLB and source Blender file are immutable.

Documented plugin rig scale/rest alignment and real limb articulation are tested BEFORE any GLB is promoted to review.
Prior v1.4.0 IK did not move legs correctly despite numeric claims. This version tests source and target hip-relative foot trajectories, joint angle motion and toe vertex heights.

Real Blender execution exit code: 0
Physically gated and independently GLB-reimported clips: NONE
Rejected clip details: {"Kick": "REIMPORT_PHYSICAL_GATE_FAIL_Kick REIMPORT_LOST_ANIMATION_['GLB_REIMPORT_SHOE_PENETRATION_Left', 'GLB_REIMPORT_FLOATING_SHOE_Left', 'GLB_EXPORT_SKIN_SOLE_MOTION_DIFFERENT_Left', 'GLB_REIMPORT_SHOE_PENETRATION_Right', 'GLB_REIMPORT_FLOATING_SHOE_Right', 'GLB_EXPORT_SKIN_SOLE_MOTION_DIFFERENT_Right', 'GLB_REIMPORT_SUPPORT_FOOT_MISSING', 'LeftUpLeg prior=88.978 reimport=0.0', 'LeftLeg prior=57.07 reimport=0.0', 'LeftFoot prior=63.19 reimport=0.0', 'RightUpLeg prior=311.357 reimport=0.0', 'RightLeg prior=62.161 reimport=0.0', 'RightFoot prior=71.938 reimport=0.0', 'LeftArm prior=40.435 reimport=0.0', 'Spine2 prior=11.841 reimport=0.0', 'REIMPORT_HIP_ONLY_KICK']", "Light1": "REIMPORT_PHYSICAL_GATE_FAIL_Light1 REIMPORT_LOST_ANIMATION_['GLB_REIMPORT_SHOE_PENETRATION_Left', 'GLB_REIMPORT_FLOATING_SHOE_Left', 'GLB_EXPORT_SKIN_SOLE_MOTION_DIFFERENT_Left', 'GLB_REIMPORT_SHOE_PENETRATION_Right', 'GLB_REIMPORT_FLOATING_SHOE_Right', 'GLB_EXPORT_SKIN_SOLE_MOTION_DIFFERENT_Right', 'GLB_REIMPORT_STANDING_FEET_NOT_GROUNDED', 'LeftUpLeg prior=55.608 reimport=0.0', 'LeftLeg prior=36.031 reimport=0.0', 'LeftFoot prior=31.386 reimport=0.0', 'RightUpLeg prior=304.691 reimport=0.0', 'RightLeg prior=42.823 reimport=0.0', 'RightFoot prior=30.678 reimport=0.0', 'LeftArm prior=18.158 reimport=0.0', 'RightArm prior=65.208 reimport=0.0', 'RightForeArm prior=89.835 reimport=0.0', 'Spine2 prior=20.611 reimport=0.0', 'REIMPORT_HIP_ONLY_LIGHT1']"}
REJECTED DIAGNOSTIC PREVIEW CLIPS (NOT VALIDATED): Light1

Any passing clip is still UNAPPROVED pending actual owner visual review.
