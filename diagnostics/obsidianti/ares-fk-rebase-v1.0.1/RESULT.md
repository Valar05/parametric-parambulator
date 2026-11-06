# Obsidianti pre-contact FK + Ares-style pelvis scale

Status: **UNAPPROVED candidate; canonical model unchanged.**

Source historical commit: `998d31fd7cf3bbeb8bd85123fdd29d9ee5a045ff`

Source LFS SHA: `5fa8773736cf4fd28eae13e13368246642642a1802d76e47ed7e14faf70d04c0`

Candidate SHA: `955e424172da09cbff1182f260c7053389d2fa623657a62a4d03dd78f5fa1b32`

Scale = mean(left,right) anatomical leg ratios = 0.8700185743929264

All ten Lionheart action pelvis translation tracks scaled around preserved idle. All rotations, weapon tracks, Ares clips, Walking/Running, geometry and skin unchanged.

This does NOT solve physical foot contact; it reverts the contact-IK code path and tests the old FK architecture with Ares scaling. Inspect visual playback and skinned sole floor before considering canonical publication.
