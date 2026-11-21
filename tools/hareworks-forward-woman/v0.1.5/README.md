# Hareworks v0.1.5: blank viewer resource recovery

This is a **loading-path correction only** to the owner-rejected blank-screen v0.1.4 viewer. Its published `viewer.mjs` requests `./foot-profile.json` although that asset only exists in `../v0.1.3/foot-profile.json`. That missing HTTP JSON blocks the entire `Promise.all` initialization before the skinned characters are added to the scene.

## Preserved scope

- Unchanged original source GLB, all 9 animations, and the reference `Walking_Woman` clip.
- Unchanged v0.1.3 leg and foot solver, v0.1.2 pelvis equations, v0.1.4 upper-body Fourier reconstruction.
- The full v0.1.5 `viewer.mjs` is generated from the exact audited v0.1.4 viewer with only the broken asset URL and version labels replaced. Its physics/pose statements are byte-equivalent after that substitution. The `upper-kernel.mjs` and its tests are copied byte-for-byte.
- The HTML has updated model-description wording plus a browser error message hook. Source profile, foot profile, model, old versions, and the existing Git history are untouched.

## Gates

The Termux campaign pins the current remote Git main, rules Git blob, source GLB SHA256 and bytes. It checks every relative `import`, the actual two JSON profile dependencies, and model URI, including deliberate validation of the old broken dependency path as a negative fixture. It runs existing kernel tests, publishes new text files only in an isolated Termux checkout, confirms exact remote readback, and starts a fresh no-cache HTTP viewer that checks the same runtime resource manifest rather than an unrelated list of URLs. It prints the actual dynamically assigned localhost URL, port, PID, model hash, and persistent receipt. Browser execution and visible skinned model review remain separate from HTTP availability and Git publication.

**Owner acceptance pending.** This does not assert the upper-body motion is visually approved or that world-space locomotion is complete.
