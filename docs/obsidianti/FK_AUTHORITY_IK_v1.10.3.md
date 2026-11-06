# Obsidianti dense FK-to-IK v1.10.3

Authority: Termux Git only. Input: exact Ares-scaled FK GLB SHA256 `955e424172da09cbff1182f260c7053389d2fa623657a62a4d03dd78f5fa1b32`. Immutable Blender FK baseline SHA256 `96e13a407a3d1746636509ddf26dbc6d15aec78458beb333cbc99dfecf320034`.

Goal: duplicate FK motions to editable Blender IK, sampling at original FK action keys and at most 0.2 Blender frames apart, keeping knee-pole controllers parented to their ankle IK controllers (unconnected). Controllers store dense keys in parent-local coordinates; foot orientation quaternions are explicitly hemisphere-unwrapped. Preserve original FK actions, source GLB, canonical GLB, left/right geometry and all nonleg animation. No visual corrections are introduced.

Acceptance: all ten attack clips, both sides, hips <=1mm, knees <=4mm, ankles <=4mm, foot orientation <=0.75 degrees, checked at sample times and at independent interval midpoints. No false green based only on exact keyed pose matches. A failed test publishes reports only, not a candidate authoring `.blend`. The unchanged baseline stays in Android Downloads. Reports record dense sample counts, maximum drift, worst frames, pole-phase outliers and SHA/provenance.

Delivery: one SHA-checked Termux launcher containing source, build and policy; driver creates unique versioned source files in the requested repo, runs Blender in phone's existing Debian proot (or native Blender), Git-LFS publishes evidence via Termux Git with exact remote readback, and copies the successful editable Blender file to Downloads by readback SHA. No direct connector writes or canonical mutation. Native Blender runtime and physical phone success are unverified until actual operator receipt.
