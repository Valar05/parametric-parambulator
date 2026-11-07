#!/usr/bin/env python3
"""Verification on actual owner GLBs, with injected hash/collision failures."""
import argparse,copy,json,pathlib,tempfile
import compose as c

def check_error(fn,term):
 try:fn()
 except Exception as e:
  assert term in str(e),(term,str(e))
 else:raise AssertionError('FAILURE_INJECTION_DID_NOT_BLOCK_'+term)

def main():
 p=argparse.ArgumentParser()
 for key in ('base','donor','canonical','candidate','proof','prior-source'):p.add_argument('--'+key,required=True)
 a=p.parse_args()
 core=c.load_prior(a.prior_source)
 actual,actual_bin=core.read_glb(a.candidate)
 b,base_bin=core.read_glb(a.base)
 d,donor_bin=core.read_glb(a.donor)
 original,orig_bin=core.read_glb(a.canonical)
 j=json.loads(pathlib.Path(a.proof).read_text())
 names=[x['name'] for x in actual['animations']]
 assert names==list(c.PRESERVED)+list(c.LIONHEART),(len(names),names)
 assert actual['animations'][:30]==b['animations']
 assert actual_bin.startswith(base_bin)
 assert j['outSHA256']==c.digest(a.candidate) and j['count']==41
 for key in ('nodes','meshes','skins','materials','textures','images','scenes'):
  assert actual.get(key)==original.get(key),key
 donor_clips={x['name']:x for x in d['animations']}
 for name in c.LIONHEART:
  assert name in donor_clips
  dest=next(x for x in actual['animations'] if x['name']==name)
  source=donor_clips[name]
  assert len(dest['channels'])==len(source['channels'])
  for sa,da in zip(source['samplers'],dest['samplers']):
   for key in ('input','output'):
    assert core.raw_accessor(d,donor_bin,sa[key])==core.raw_accessor(actual,actual_bin,da[key]),(name,key)
 with tempfile.TemporaryDirectory(prefix='obs32-errors-') as dtmp:
  t=pathlib.Path(dtmp)
  check_error(lambda:c.compose(a.base,a.donor,a.canonical,t/'bad.glb',t/'bad.json',a.prior_source,expected_base='0'*64), 'V231_30_CLIP_SHA256_MISMATCH')
  check_error(lambda:c.compose(a.base,a.donor,a.canonical,pathlib.Path(a.candidate),t/'dupe.json',a.prior_source,expected_base=j['inputThirtySHA256'],expected_donor=j['v216LionheartSHA256'],expected_canon=j['originalCanonicalSHA256']), 'OUTPUT_DESTINATION_ALREADY_EXISTS')
 print('V232_REAL_41_CLIP_PASS original30=UNCHANGED lionheart11=EXACT_SAMPLE_COPY vanguard19=PRESERVED shield=CANONICAL originalAnimatedIdle=UNCHANGED sourceMismatch=BLOCKED collisions=BLOCKED')
if __name__=='__main__':main()
