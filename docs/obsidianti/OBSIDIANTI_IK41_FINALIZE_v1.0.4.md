# Obsidianti IK41 final native reopen and publication v1.0.4

Authority: Termux Git only. No new IK generation, no animation rewrites.

Reuses exact v1.0.3 repaired candidate SHA256 30ad2518a820e6b1770dcced6a46f1f2f91db28af799c60dfa21ab3488cda75e, verified with original source SHA256 30b00b71333f3d17aa923884381cbed381ac255af6366c83cc5005166e1c4a27. v1.0.3 reopened all 82 preserved original FK actions with 252,130 points and zero differences; all 41 IK actions were present, 121 sampled poses within limits (knee 0.003745m, ankle 0.000008924m). It failed ONLY because the verifier incorrectly required >=123 independent samples for 41 clips, two of which have fewer unique sample times. This patch preserves all substantive checks but computes and compares the expected unique sample count from actual action keyframes, and gates exact pinned 121 count. Neither the original .blend nor the generated IK candidate is modified.

Independent native Blender reopen must reproduce original FK curve metadata, handles, times, values, all 41 active IK chains, and pose tolerances. Then copy to Android Downloads, Git-LFS publish the existing versioned v1.0.3 output with remote HEAD and LFS pointer readback. Owner visual acceptance remains pending. No Sword1/two-handed integration.
