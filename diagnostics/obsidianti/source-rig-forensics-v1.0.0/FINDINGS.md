# Ares vs Lionheart source rig forensics

This is source evidence, not proof of the original Obsidianti import divergence. No animation or rig was modified.

Ares original SHA: `63b6e7a7250cfb03e49cf0d335101d808126ae926894d74c1b2a6a49936b8b2a`
Lionheart original SHA: `81aa915416cd1a742feba5670aad67a6f131da74e0c1837d02d52b57b66998d4`

## Ares
- Rig `Armature`: 42 bones, constraints {}
- Action `AxeKick` active IK constraints 0; max constraint-on/off foot differences {'L': 0.0, 'R': 0.0}
- Action `AxleKick` active IK constraints 0; max constraint-on/off foot differences {'L': 0.0, 'R': 0.0}
- Action `CurbStomp` active IK constraints 0; max constraint-on/off foot differences {'L': 0.0, 'R': 0.0}
- Action `FrontKick` active IK constraints 0; max constraint-on/off foot differences {'L': 0.0, 'R': 0.0}
- Action `LowBackKick` active IK constraints 0; max constraint-on/off foot differences {'L': 0.0, 'R': 0.0}
- Action `SpinningHighKick` active IK constraints 0; max constraint-on/off foot differences {'L': 0.0, 'R': 0.0}
## Lionheart
- Rig `Armature`: 32 bones, constraints {'COPY_ROTATION': 2, 'IK': 2}
- Action `Cast` active IK constraints 2; max constraint-on/off foot differences {'L': 0.1890807, 'R': 0.2040645}
- Action `Heavy1` active IK constraints 2; max constraint-on/off foot differences {'L': 0.7513371, 'R': 0.7519826}
- Action `Heavy2` active IK constraints 2; max constraint-on/off foot differences {'L': 0.6576149, 'R': 0.7291766}
- Action `Heavy3` active IK constraints 2; max constraint-on/off foot differences {'L': 0.750041, 'R': 0.816658}
- Action `Kick` active IK constraints 2; max constraint-on/off foot differences {'L': 1.0268366, 'R': 1.1666034}
- Action `Light1` active IK constraints 2; max constraint-on/off foot differences {'L': 0.2574336, 'R': 0.4867813}
- Action `Light2` active IK constraints 2; max constraint-on/off foot differences {'L': 0.3467065, 'R': 0.5933336}
- Action `Light3` active IK constraints 2; max constraint-on/off foot differences {'L': 0.5983723, 'R': 0.6224798}
- Action `SpringAttack` active IK constraints 2; max constraint-on/off foot differences {'L': 0.4531382, 'R': 0.9234397}
- Action `Stomp` active IK constraints 2; max constraint-on/off foot differences {'L': 0.4327941, 'R': 0.4096848}

## Interpretation gate
If turning off IK changes evaluated foot transforms in source, an FK-only import must bake *evaluated* source motion rather than copying raw deform keys. If source on/off match, investigate rest matrices, pelvis scale and retarget interpolation. The original import stage still requires a separate source/target trajectory comparison.
