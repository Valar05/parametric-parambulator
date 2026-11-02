# Repl v0.6.19 — Stance Extension and Breakover, constrained recovery

**Owner boundary:** Repl 0.6.17 is best yet, almost acceptable, NOT approved. Protect its low swing, rear motion, body settling, meshes, skinning, root travel and hoof/toe/distal channels. Only Bone_015/014/021/020 animation rotations may change without separate approval.

This one-entrypoint Termux Git campaign first pins the live canonical binary and reads repository AGENTS.md. It then authors its own immutable versioned source and appends measured stance/breakover laws to AGENTS.md, commits them through Termux and verifies the remote readback. It evaluates a bounded family of full-cycle two-joint candidate gaits against actual skinned geometry. It publishes a new canonical GLB ONLY when the complete existing 1164-frame plus 576-midframe ground/hoof/kick/stance verifier AND the additional stance-straightening/trailing-reach metrics pass. Otherwise it leaves the canonical GLB unchanged and records the physical limitation, preserving the now-Git-owned recovery source and policy.

Do not misinterpret `SCRIPT_AND_POLICY_COMMITTED` as `WALK_CORRECTED`. If the two protected joints cannot meet the owner objective, stop and request a separate explicit authorization for additional degrees of freedom.

Proof levels are distinct: packet prepared → device packet verified → source Git read back → policy committed → actual model modified → user visual acceptance. No shortcut from synthetic tests to approval.

## v0.6.19 recovery note

This packet fixes a deterministic Python `UnboundLocalError` in v0.6.18, adds per-turn doctrine on this regression, and exercises driver code paths with test fixtures. The four existing two-joint gait candidates and physical gate remain unchanged. The reference replay had rejected all four, so no visual improvement is guaranteed; on actual infeasibility the model remains v0.6.17, while the source/AGENTS addendum may be committed separately through Termux Git.
