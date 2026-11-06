# Obsidianti FK-authoritative Blender baseline + gated IK authoring v1.10.1

**Authorized run:** Termux Git only, same canonical repository. Original Ares-scaled FK candidate SHA `955e424172da09cbff1182f260c7053389d2fa623657a62a4d03dd78f5fa1b32`. Neither canonical GLB nor the original source model is changed.

- Fix: LFS smudge is disabled for every Git checkout process, so an unavailable unrelated `assets/repl/Repl.glb` cannot prevent a checkout. The only explicitly fetched LFS file is the published Obsidianti evidence archive, verified by both archive and GLB SHA.
- Deliverable 1: native Blender FK baseline from the exact source GLB, without any IK modifications. Preserve all actions, geometry, armature, skin and left-leg choreography.
- Deliverable 2: separate FK->IK authoring test, evaluated at original keys and midpoints, hard-gated on exact joint and foot orientation parity. Never label a parity-failed IK rig as approved.
- Publish FK baseline .blend and receipts to versioned Git LFS evidence via Termux Git, remote readback, and to Android shared Downloads with atomic copy and SHA readback.
- If IK does not pass, deliver the clean FK baseline and report failed parity. Do not disguise it as an IK-ready project.
- The owner decides visual acceptance. No animation or canonical model mutation.
