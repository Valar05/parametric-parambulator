# Obsidianti FK Feet: direct GLB viewer export v1.0.0

This is a *view-only* export of the existing 52,375,227-byte, SHA-256 `30b00b71333f3d17aa923884381cbed381ac255af6366c83cc5005166e1c4a27` native Blender FK Feet authoring file. No modifications to the source `.blend`, animations, controls or canonical assets are authorized. The pre-Sword1 library has 41 clips; this campaign exports only the `OBSIDIANTI_FK_FEET_EDITABLE` rig and its independently copied meshes into a uniquely named unapproved GLB, tests its structure and provides a local Three.js playback viewer.

Repository publication and binary readback must occur in the isolated Termux Git lane; the viewer must report the exact exported model digest, 41 clips, its own unique run identity and no-cache routes. On export failure no binary is published. A structural GLB export and playable clip viewer do **not** establish frame-by-frame pose parity. Owner visual verdict decides whether any deformation occurred. An untouched source reference is kept in Git history.

The launcher is self-contained, uses a SHA-checked embedded packet, and publishes these versioned source files into `campaigns/` and this doc into `docs/obsidianti/`. Actual export runs with the already installed Blender runtime in native Termux or the established `obs-arp-blender50` / `debian` proot. No new rig rebuild or ARP solver run.
