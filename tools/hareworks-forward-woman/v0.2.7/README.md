# Hareworks Left Walk, In Place, v0.2.7

The owner explicitly corrected the selected animation: **the walk to the left, NOT the slide**. Source clips are `Cautious_Crouch_Walk_Left` and `Cautious_Crouch_Walk_Left_inplace`. No `slide_right` clip is loaded, compared, or transferred.

The real GLB original extracted evidence shows a ~1.43-unit lateral pelvis trajectory in the traveling left walk and only ~0.13 unit cyclic sideways excursion in its authored in-place version. The latter is our exact parity target. Recreate it using source-calibrated mathematical per-joint rotation, translation and scale trajectories across all 74 bones (720 calibrated phases). The generated character does not run source animation tracks. The original authored source clip plays only on the visible reference rig, and the traveling variant is offered exclusively for source comparison.

Remove only the small noncyclic source-root X/Z trend from the in-place curve. Preserve legitimate cyclical lateral sway and vertical bounce; this is not freezing the pelvis. Reconstruct the final ~7% seam with continuous quaternion/position/scale splines to avoid the GLB terminal reset. Explicitly disclose source-parity exclusion in the modified seam window. The generated at time zero should match the original source at time zero across all 74 local joints, independent of the two scene placements.

The browser audits 30, 60 and 120 Hz with half frames, measures all joints in the same model space and reports contact-ankle, toe and joint parity. It exports JSON and posts a copy to Termux persistent campaign state. It never claims that low-foot proximity proves physical foot contact. Numerical parity does not mean owner visual acceptance.

**Immutable approved baselines:** accepted forward v0.1.9, backward in-place v0.2.2, approved pelvis-only style experiment v0.2.6, source GLB (SHA a0e0c7575c366a6967fbcaefb875b47ca956292f3b3975e7d1a7afb2b3d2aec6) and all prior files. This is an append-only prototype under `tools/hareworks-forward-woman/v0.2.7/`, deployed using the owner's Termux Git lane ONLY. No direct GitHub writes, no replacement architecture or visual approval claimed.

Fail clearly if Git HEAD changed, artifact paths collide, exact model identity fails, or a required test fails. A browser warning should remain viewable rather than hiding the animated model. Source comparison and generated gait remain explicitly separate.
