# Hareworks v0.1.19: Source-locked knee plane, no pelvis centerline crossing

Owner rejected v0.1.18 visual motion: knees remain wobbly and pass far across the centerline. Previous distal-style decoupling passed its own test but did NOT constrain the knee's actual world-space side position. This version corrects the proximal joint target rather than changing the already-liked foot direction.

* Source authority: original 60-frame Walking_Woman skinned hip, knee and ankle witnesses from published original model. For each real IK step, project the SOURCE hip-to-knee direction into the current hip-to-ankle 2-bone bending circle. This restores the original anatomical knee plane even when the world-planted ankle differs from the phase-fit ankle.
* Constrain each knee to remain at least .018 model units on its own side of the midpoint between the actual left/right hip roots; use the closest feasible point on the true two-bone knee circle, never fake a knee coordinate or move the planted foot. Report if geometry is physically infeasible rather than claiming completion.
* Limit knee-pole radial direction changes to 10 rad/s between physical IK frames, then enforce the centerline bound. Measure maximum knee displacement per 120Hz step, original-knee deviation, side clearance and correction count.
* Foot heading: `foot-heading.mjs` and the entire distal-styling block remain unchanged from published v0.1.18. Preserve original model, root path, dynamic speed, foot contact geometry and camera OrbitControls.
* Git authority: one versioned Termux script, checked existing Documents checkout, immutable source GLB SHA, new `v0.1.19` path only, remote commit and exact readback. Real browser audit and owner visual acceptance are NOT inferred from numerical tests or publication.

This is not a completed or approved gait until the actual skinned browser model passes and the owner reviews the movement.
