# Hareworks v0.1.18: original knee IK / independent distal foot heading

Owner: Right foot is not pointed as far forward as left. Knees must revert to their earlier source-derived IK, not be altered by foot direction. Preserve existing good left-foot orientation, dynamic root cadence, real world foot pins, foot roll, and camera orbit.

### Corrected causal bug

v0.1.17 `solveLeg()` recomputed the thigh and shin repeatedly after applying an arbitrary blend of v0.1.9 toe/yaw styling. The resulting orientation-dependent skinned-patch displacement fed back into `desiredAnkle`, changing thigh/shin angles because the distal foot was rotated. Additionally, v0.1.17 `adjustAnkleForSpeed` applied artificial lateral shifts to the source ankle. Both violate the owner's stated independence between foot-heading style and knee IK.

### This change

* Preserve original v0.1.9 pelvis, full hip-relative ankle coordinates, and knee pole. No artificial ankle crossover. Restore the near-full knee extension by replacing the old 0.005 maximum-reach clamp with a 0.00025 numerical tolerance (still within real limb reach). The runway motion inherent in the source remains; don't create it by moving the knee.
* `kneeFromTarget` and contact IK first solve against the ORIGINAL source foot orientation, independent of styling. Every unstyled foot witness is cached before distal heading is applied, including future touchdown anchors. Then the foot is rotated ONCE, post-IK. Exact hip/knee/ankle positions and knee-bone rotation are asserted invariant under this foot-only style change at every physical step.
* Right foot heading bias comes from the real v0.1.2 fit's left and right mean yaw (about -8.72° on the right). The left foot heading remains untouched, and phase variation remains intact.
* This can change final skinned contact-patch positions slightly: measured contact drift is reported honestly, with existing contact audit thresholds unchanged. A hard world pin can be incompatible with a foot twist and an exactly unchanged knee: the script does not silently change the knee to hide that tradeoff.
* Keep previous real model GLB untouched; preserve OrbitControls and physically derived root travel/stance anchors. No source animation mixer on the running actor.

Three independent gates: distal yaw-to-knee invariance, contact quality at 120Hz with a hard numerical 6° source-knee-deviation audit limit, human silhouette acceptance. The code and numeric tests are not a human visual verdict.
