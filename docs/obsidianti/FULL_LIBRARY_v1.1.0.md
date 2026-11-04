# Obsidianti full animated-action library v1.1.0

## Authority

The real repository is `Valar05/parametric-parambulator`, and the one permanent model is `assets/obsidianti/Obsidianti.glb`. Never store the next version under another GLB name. Repl's `assets/repl/Repl.glb` and all Repl work remain outside scope. This document and scripts are installed through the single Termux Git campaign, not a direct connector write.

## User-visible goal

User approved the transferred Lionheart pose visually in the previous review. Preserve those full-body angles and independent weapon rigs. Floor hover is slightly visible: apply a conservative **candidate** -0.012m Y hip offset to new clips, keep viewer ground line adjustable, and require user visual check for penetration. Do not change existing Walking and Running animations.

The source Blender `Idle` is exactly one keyframed pose. The new `ObsidiantiIdle` is an explicitly authored 3-second, smoothly repeating breathing and weight-shift animation **around** that protected pose; do not mislabel it as recovered Lionheart source frames. The original `LionheartIdle_UNREVIEWED` stays byte-identical.

Bake all ten other native Lionheart Actions: `Cast`, `Heavy1`–`Heavy3`, `Kick`, `Light1`–`Light3`, `SpringAttack`, `Stomp`. The donor .blend's native foot IK constraints must be evaluated by actual Blender per-frame; raw curve transfer omits essential physical motion. Both independent weapon control bones must remain separately animated.

From the real Ares Mixamo source: transfer eight `Step*` clips **lower body only**, preserving Lionheart upper-body idle and separate weapon sockets; transfer `AxeKick` **full body** with source counterbalance. Do not confuse `AxeKick` and `AxleKick`. The Ares source can be taken from an existing phone checkout or fetched read-only from the Gravity Fist Git repository via Git LFS; no Pose Lab workspace is created.

## Runner

The direct-download packet contains the versioned campaign and the two native Blender files, plus an exact copy of the accepted static Idle target for provenance and LFS recovery. One Termux command invokes the launcher. It:

1. Verifies every packaged source byte by SHA-256, Git and Git LFS availability.
2. Creates a separate clean clone of `parametric-parambulator` and rereads current AGENTS. Guards the sole Obsidianti canonical input SHA and protected Repl tree object.
3. Obtains the exact real Ares GLB and evaluates the **real** Lionel and Ares Action poses in Blender (including native constraints) via existing Termux/proot Debian Blender.
4. Rebases source action quaternions onto the exact previously approved static Lionheart/Meshy Idle. Creates original `ObsidiantiIdle` and 19 sampled full-action clips. Maintains original Walking, Running and static Idle bytes and the full skin/geometry BIN prefix.
5. Validates 23 clips, no new GLB name, preserved original material/rig/skin and stable source SHA.
6. Commits **new versioned campaign scripts and docs first**, then replaces the same canonical model path and commits it using Git LFS. Pushes only from the authorized Termux Git checkout, checks remote HEAD, LFS pointer hash and verifies Repl unchanged.
7. Leaves all new animation clips quarantined pending the owner's actual rigged model visible verdict in the local review page.

The internal script never uses an arbitrary user worktree, silently overwrites a changed canonical model, force-pushes, creates a new version-named GLB, or claims host screenshot acceptance. On missing required Ares donor or working Blender, no model success is reported and the previous canonical model is untouched remotely.

## Known verification boundary

Off-device GLB patcher tests used the exact prior target and a **synthetic Ares proxy**, not real Ares source evaluation. They prove serialization/buffer invariance, not Ares choreography or correct hosted playback. Actual Blender and Ares sampling is performed in the authorized Termux run, and user visual review is mandatory. A source Action can use different source rest conventions or source constraints; any sampled mismatch is evidence requiring reauthoring, not permission to flatten keyframes or change the approved Idle pose.
