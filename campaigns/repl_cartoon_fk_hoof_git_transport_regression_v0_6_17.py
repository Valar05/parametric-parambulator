#!/usr/bin/env python3
"""No internet needed: test actual Git cache, clone isolation and timeouts."""
from pathlib import Path
import hashlib,importlib.util,os,subprocess,sys,tempfile
sys.dont_write_bytecode=True

def call(*args,cwd=None):
 p=subprocess.run(args,cwd=cwd,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=20)
 return p.stdout.strip()

def run_tests(driver_file):
 spec=importlib.util.spec_from_file_location('repl_git_transport_under_test',driver_file)
 d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
 # Timeout must become a classified recoverable blocked failure, not a raw traceback.
 original=d.subprocess.run
 def fake_timeout(*args,**kwargs):
  raise subprocess.TimeoutExpired(args[0],kwargs.get('timeout',1))
 try:
  d.subprocess.run=fake_timeout
  try:d.run(['git','clone','example'],timeout=1)
  except d.Blocked as ex:assert 'COMMAND_TIMEOUT:git:1s' in str(ex)
  else:raise AssertionError('TIMEOUT_WAS_NOT_CAUGHT')
 finally:d.subprocess.run=original
 with tempfile.TemporaryDirectory(prefix='repl0615-git-test-') as raw:
  root=Path(raw);prior=root/'cartoon-fk-hoof-v0.6.13'/'repo';prior.parent.mkdir(parents=True)
  call('git','init','-q','-b','main',str(prior))
  call('git','remote','add','origin',d.REMOTE,cwd=prior)
  path=prior/d.CANON;path.parent.mkdir(parents=True)
  path.write_bytes(b'HOISTED_VALID_REFERENCE')
  call('git','add','.',cwd=prior)
  call('git','-c','user.name=Regression','-c','user.email=regression@example.invalid','commit','-q','-m','reference',cwd=prior)
  ref=call('git','rev-parse','HEAD',cwd=prior)
  ref_blob=call('git','rev-parse','HEAD:'+d.CANON,cwd=prior)
  path.write_bytes(b'PINNED_CANONICAL_SOURCE')
  call('git','add','.',cwd=prior)
  call('git','-c','user.name=Regression','-c','user.email=regression@example.invalid','commit','-q','-m','source',cwd=prior)
  head=call('git','rev-parse','HEAD',cwd=prior)
  blob=call('git','rev-parse','HEAD:'+d.CANON,cwd=prior)
  d.KNOWN_PARENT_HEAD=head;d.SOURCE_BLOB=blob
  d.SOURCE_SHA=hashlib.sha256(path.read_bytes()).hexdigest()
  d.REFERENCE_COMMIT=ref;d.REFERENCE_GLB_BLOB=ref_blob
  # Local checkout deliberately has uncommitted source changes: we must not
  # mutate or transport them, only Git HEAD content.
  (prior/'dirty-private.txt').write_text('DO_NOT_TOUCH')
  need=root/'cartoon-fk-hoof-v0.6.17';need.mkdir()
  assert d._seed_is_pinned(prior)
  repo=d.checkout(need)
  assert repo==need/'repo'
  assert call('git','rev-parse','HEAD',cwd=repo)==head
  assert call('git','remote','get-url','origin',cwd=repo)==d.REMOTE
  assert (repo/d.CANON).read_bytes()==b'PINNED_CANONICAL_SOURCE'
  assert not (repo/'dirty-private.txt').exists()
  assert (prior/'dirty-private.txt').read_text()=='DO_NOT_TOUCH'
  assert d.checkout(need)==repo  # idempotent, no GitHub fetch
  assert not list(need.glob('.repl0615-local-*'))
  assert not d._seed_is_pinned(root)
  # A local bare remote exercises the SHALLOW NETWORK FETCH implementation.
  # Force the first attempt to fail, then verify bounded compatible fallback.
  bare=root/'simulation-remote.git'
  call('git','init','--bare','-q',str(bare))
  call('git','push','-q',str(bare),'main:refs/heads/main',cwd=prior)
  d.REMOTE=str(bare)
  stagework=root/'cartoon-fk-hoof-v0.6.17-simulation';stagework.mkdir()
  realrun=d.run
  calls=[0]
  def fail_first(cmd,*a,**kw):
   if len(cmd)>3 and cmd[0]=='git' and 'fetch' in cmd and '--filter=blob:none' in cmd and calls[0]==0:
    calls[0]+=1
    return subprocess.CompletedProcess(cmd,1,'','SIMULATED_TRANSIENT_FETCH_FAILURE')
   return realrun(cmd,*a,**kw)
  try:
   d.run=fail_first
   stage=d._network_bootstrap(stagework)
  finally:d.run=realrun
  assert calls[0]==1
  assert call('git','rev-parse','HEAD',cwd=stage)==head
  assert call('git','remote','get-url','origin',cwd=stage)==str(bare)
  assert (stage/d.CANON).read_bytes()==b'PINNED_CANONICAL_SOURCE'
  assert d._network_bootstrap(stagework)==stage  # retry must not refetch
  return {'timeout_classification':'PASS','verified_cache_reuse':'PASS','dirty_source_protection':'PASS','resume':'PASS','shallow_fetch_retry':'PASS','verified_fetch_cache_reuse':'PASS'}

if __name__=='__main__':
 print(run_tests(Path(__file__).with_name('driver.py')))
