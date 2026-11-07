#!/usr/bin/env python3
"""Build fresh versioned A/B viewer using previously published, SHA-pinned 2.0.26 viewer."""
from __future__ import annotations

def one(s,old,new):
 n=s.count(old)
 if n!=1:raise RuntimeError('VIEWER_TEMPLATE_DRIFT '+repr(old[:90])+' occurrences='+str(n))
 return s.replace(old,new,1)

def build(source):
 s=one(source,'Mudman | HitHeadLeft torso-frame repair 2.0.26','Mudman | HitHeadLeft exact 90° hips rotation 2.0.27')
 s=one(s,'<option value="candidate">Corrected HitHeadLeft · review</option><option value="original">Before repair · same animations</option>',
 '''<option value="candidate">Hips −90° X | exact quarter-turn</option><option value="axis">Hips −90° measured axis | comparison</option><option value="original">Original v2.0.23 | no correction</option>''')
 s=one(s,"key=mode==='candidate'?'candidate':'canonical'","key=mode")
 s=one(s,'Original comparison unavailable: canonical GLB not staged. Select purchased ARP retarget.',
         'Comparison GLB unavailable; check run receipt and identity.')
 s=one(s,'Review the real HitHeadLeft measured world-frame correction against the original GLB. Only HitHeadLeft rotation data may differ; all other 22 clips, UVs, textures, mesh, and ground origin are preserved.',
       'HitHeadLeft source is unmodified v2.0.23. Candidate options are EXACT 90-degree rotations of the Hips keyframes, NOT the rejected 62.38-degree pose fit. A/B against source. All other 22 clips, UVs, textures, mesh, ground origin, and key times are identical. OWNER REVIEW PENDING.')
 needle="for(const name of ordered){const option=document.createElement('option');option.value=name;option.textContent=name;el('move').appendChild(option)}"
 s=one(s,needle,needle+"\nel('move').value='HitHeadLeft';")
 s=one(s,"const span=Math.max(size.x,size.y,size.z,.5);","const span=Math.max(size.x,size.y,size.z,.5)*1.65; // extra camera room for sideways and upright hit reactions")
 s=one(s," | ARP preview | MUDMAN ARES ACTION TRANSFER | UNAPPROVED"," | EXACT 90° HIPS A/B REVIEW | OWNER VERDICT PENDING")
 # Do not accumulate TEXTURED counters when switching comparison models.
 if "identity.textContent=identity.textContent.replace" not in s:raise RuntimeError('TEXTURE_COUNTER_REGRESSION')
 if "EXACT_ANIMATION_SELECTION_FAILED_" not in s:raise RuntimeError('STANDUP_EXACT_SELECTION_REGRESSION')
 if "floor.position.y=Number(el('ground').value)" not in s:raise RuntimeError('GROUNDED_FLOOR_REGRESSION')
 return s
