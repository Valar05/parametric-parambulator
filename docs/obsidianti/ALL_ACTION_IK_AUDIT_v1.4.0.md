# Lionheart 11-action native IK diagnostic | v1.4.0

## Purpose and scope

Archive the **evaluated original Lionheart** two-bone IK source rig for every native action (`Idle`, `Cast`, `Heavy1`, `Heavy2`, `Heavy3`, `Kick`, `Light1`, `Light2`, `Light3`, `SpringAttack`, `Stomp`) and calibrate source foot-controller and knee-pole positions against Obsidianti's accepted static `LionheartIdle_UNREVIEWED` stance. Include all deforming bone world matrices, all four original IK controller matrices and evaluated ankle relationships for each action at whole and half frames. No new animation, mesh, skin, rig or canonical GLB is written.

## Binary and repository authority

Git repo: `Valar05/parametric-parambulator`. Only Android Termux Git can commit or push this audit. The launcher ships one ZIP payload inside one SHA-checked shell script. The Termux runner clones the current main into a new isolated checkout, rereads actual `AGENTS.md`, verifies the original donor .blend's Git LFS SHA256 `81aa915416cd1a742feba5670aad67a6f131da74e0c1837d02d52b57b66998d4`, and verifies the current canonical Obsidianti GLB's Git LFS SHA256 `8036ea2545cd1f32096447649eea1119aeb59769c94af0118bf94c929c2f63b4` before evaluating the source. It refuses unexpected LFS changes, versioned destination collisions, incomplete action enumeration, or a mutated target. It never touches Repl.

The output is **new read-only evidence** in `diagnostics/obsidianti/lionheart-ik-all-v1.4.0/` with one JSON per native action, complete source rest and constraints (`source-rig.json`), target bind and accepted Idle (`target-reference.json`), derived offsets and frame-range index (`calibration.json`), and a SHA-256 manifest (`manifest.json`). Save a ZIP and separate receipt in phone Downloads regardless of whether the later remote Git push succeeds. A remote report is claimed only after a normal non-forced Git push and readback of the exact remote manifest; source/model/repl hashes must remain unchanged.

## Measurements and limitations

For each original frame and half-frame, Blender evaluates the **real** native `.blend` with NLA muted and native constraints active, returning each bone's complete evaluated world 4×4 matrix, position, quaternion, local hierarchy/rest matrix, lengths and constraints, plus foot-controller/ankle/pole offsets relative to the pelvis. Blender Z-up source world transforms are converted into glTF Y-up metres using its actual object transform. The target's approved combat Idle is read from the first frame of the exact `LionheartIdle_UNREVIEWED` clip, not Running frame 0. Its bind/rest is read independently from GLB node transforms. Per-leg scaling uses measured target leg-chain length divided by source rest length; provisional pelvis-relative source-to-target IK-controller offsets are included in the summary.

**This is a diagnostic, not successful retargeting.** The original controller may not coincide with the ankle or sole. The script does not measure deformed sole-floor contact, does not resolve character-facing orientation differences, and does not certify unreachable movements, motion continuity or viewer acceptance. The captured bone matrices and native controller evaluation are intended to support those later investigations. **Do not overwrite approved Heavy2, Ares, Idle, Walking/Running, Repl or any canonical model clips.**

If any action or verification fails, the receipt reports `BLOCKED_NO_CLAIM_OF_REMOTE_SAVE` and no push success is claimed. If a previous run already committed this exact version, inspect that durable report instead of overwriting it. Running a new version requires a new versioned campaign rather than mutating existing source filenames.
