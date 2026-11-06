# Obsidianti Sparse FK review v1.10.5

Owner request: export the verified v1.10.4 sparse FK Blender project for visible Android browser review. Authority: Termux Git only, repository `Valar05/parametric-parambulator`.

Source is the exact SHA-256 `3ba6ab2356dd0034a76f710bcfef669ad9f998d942c73f8bfe9c5cf5a0fb7447` v1.10.4 editable Blender artifact in Android Downloads. Preserve original 23 FK actions, sparse FK action source, skin, armature and canonical GLB; only publish an unapproved derivative GLB and viewer evidence.

Export only the sparse authoring rig and its meshes and ten `SPARSE_FK_*` actions. Validate GLB 2.0, mesh and skin presence, ten uniquely identified clips with rotation tracks. The no-store viewer runtime verifies full GLB SHA-256 in the browser and identity against the URL manifest. The Termux launcher verifies HTTP responses, and prints `REVIEW_URL` regardless of opener availability; output persists in `~/.local/share/OBSIDIANTI_SPARSE_FK_REVIEW_v1.10.5/` and the exported GLB in Downloads.

Visual approval is withheld. `VIEWER_READY_UNAPPROVED` is an HTTP/export gate, not owner acceptance. No artistic fix to SpringAttack, Light3, or Heavy3 is included.
