#!/usr/bin/env python3
"""Assemble real Blender images into compact deterministic GIF and inspectable 4x4 sheet."""
from __future__ import annotations
import hashlib,pathlib
from PIL import Image,ImageOps,ImageDraw

def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()

def assemble(frame_dir,out_dir,clip):
 files=sorted(pathlib.Path(frame_dir).glob('frame_*.png'))
 if len(files)!=16:raise RuntimeError('BLENDER_RENDER_FRAME_COUNT_INVALID_'+str(len(files)))
 imgs=[]
 for f in files:
  with Image.open(f) as im:
   if im.size!=(512,512):raise RuntimeError('FRAME_DIMENSIONS_INVALID')
   imgs.append(im.convert('RGB'))
 # Static frames are still valuable rejected diagnostics; never label them motion proof.
 out_dir=pathlib.Path(out_dir)
 gif=out_dir/('ARP_'+clip+'_SIDE_UNAPPROVED.gif')
 # global palette reduces frame-to-frame color chatter
 palette=Image.new('RGB',(16*512,512))
 for i,im in enumerate(imgs):palette.paste(im,(i*512,0))
 pal=palette.quantize(colors=192,method=Image.Quantize.MEDIANCUT)
 encoded=[im.quantize(palette=pal,dither=Image.Dither.NONE) for im in imgs]
 encoded[0].save(gif,save_all=True,append_images=encoded[1:],duration=130,loop=0,optimize=True,disposal=2)
 sheet=Image.new('RGB',(1280,1280),(27,34,45))
 draw=ImageDraw.Draw(sheet)
 for i,im in enumerate(imgs):
  x=(i%4)*320;y=(i//4)*320
  sheet.paste(im.resize((320,320),Image.Resampling.LANCZOS),(x,y))
  draw.rectangle((x+2,y+2,x+47,y+22),fill=(18,27,36))
  draw.text((x+7,y+5),str(i),fill=(255,255,255))
 sheetpath=out_dir/('ARP_'+clip+'_SIDE_CONTACT.png');sheet.save(sheetpath,optimize=True)
 return {'gif':str(gif),'gifSHA256':sha(gif),'gifBytes':gif.stat().st_size,'contact':str(sheetpath),
  'contactSHA256':sha(sheetpath),'frames':len(files),'distinctFrames':len({sha(f) for f in files})}
