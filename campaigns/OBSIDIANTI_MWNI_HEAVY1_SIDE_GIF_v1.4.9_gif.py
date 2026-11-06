#!/usr/bin/env python3
"""Convert the REAL Blender-rendered BMP sequence into a looping GIF.
Pillow preferred, ffmpeg second, portable pure-stdlib 3-3-2 GIF fallback.
"""
from __future__ import annotations
import pathlib,struct,subprocess,shutil,hashlib

def bmp_pixels(path):
    b=pathlib.Path(path).read_bytes()
    if len(b)<54 or b[:2]!=b'BM':raise RuntimeError('NOT_BMP '+str(path))
    offset=struct.unpack_from('<I',b,10)[0]
    dibsize=struct.unpack_from('<I',b,14)[0]
    if dibsize<40:raise RuntimeError('UNSUPPORTED_BMP_HEADER')
    w,h=struct.unpack_from('<ii',b,18)
    planes,depth=struct.unpack_from('<HH',b,26)
    compression=struct.unpack_from('<I',b,30)[0]
    if not(0<w<=1024 and 0<abs(h)<=1024 and planes==1 and depth in (24,32) and compression==0):
        raise RuntimeError('UNSUPPORTED_RENDER_BMP '+repr((w,h,planes,depth,compression)))
    stride=((w*(depth//8)+3)//4)*4
    if offset+stride*abs(h)>len(b):raise RuntimeError('TRUNCATED_FRAME_BMP')
    rgb=bytearray(w*abs(h))
    for y in range(abs(h)):
        row=(abs(h)-1-y) if h>0 else y
        start=offset+row*stride
        for x in range(w):
            n=start+x*(depth//8);blue,green,red=b[n],b[n+1],b[n+2]
            rgb[y*w+x]=(red&0xe0)|((green>>3)&0x1c)|(blue>>6)
    return w,abs(h),bytes(rgb)

def gif_fallback(frames,out,delay_cs=7):
    w,h,pixels=bmp_pixels(frames[0]);palette=bytes(sum(([(i>>5)*36,((i>>2)&7)*36,(i&3)*85] for i in range(256)),[]))
    with open(out,'wb') as f:
        f.write(b'GIF89a'+struct.pack('<HHBBB',w,h,0xf7,0,0)+palette)
        f.write(b'\x21\xff\x0bNETSCAPE2.0\x03\x01\x00\x00\x00')
        for frame in frames:
            fw,fh,idx=bmp_pixels(frame)
            if fw!=w or fh!=h:raise RuntimeError('GIF_FRAME_SIZE_DRIFT')
            f.write(b'\x21\xf9\x04'+bytes([0x08])+struct.pack('<H',delay_cs)+b'\x00\x00')
            f.write(b'\x2c'+struct.pack('<HHHHB',0,0,w,h,0)+b'\x08')
            # GIF LZW: frequent clear codes keep the stream at a guaranteed 9-bit code width.
            codes=[256]
            for i,p in enumerate(idx):
                codes.append(p)
                if (i+1)%180==0:codes.append(256)
            codes.append(257)
            bitbuf=0;bitcount=0;packed=bytearray()
            for code in codes:
                bitbuf |= code<<bitcount;bitcount+=9
                while bitcount>=8:
                    packed.append(bitbuf&255);bitbuf>>=8;bitcount-=8
            if bitcount:packed.append(bitbuf&255)
            for k in range(0,len(packed),255):chunk=packed[k:k+255];f.write(bytes([len(chunk)]));f.write(chunk)
            f.write(b'\x00')
        f.write(b'\x3b')
    return 'PORTABLE_PYTHON_GIF332'

def assemble(frames,out):
    frames=[pathlib.Path(x) for x in frames];out=pathlib.Path(out)
    if len(frames)<5 or not all(f.is_file() for f in frames):raise RuntimeError('RENDERED_FRAME_SEQUENCE_INCOMPLETE')
    mechanism=None
    try:
        from PIL import Image
        images=[]
        for frame in frames:
            with Image.open(frame) as im:images.append(im.convert('RGB'))
        # Force a consistent global palette from the first frame to avoid distracting flicker.
        p=images[0].quantize(colors=240,method=Image.Quantize.FASTOCTREE)
        frames_p=[im.quantize(palette=p) for im in images]
        frames_p[0].save(out,save_all=True,append_images=frames_p[1:],loop=0,duration=70,optimize=False,disposal=2)
        mechanism='PIL_GLOBAL_PALETTE'
    except (ImportError,AttributeError):pass
    if mechanism is None and shutil.which('ffmpeg'):
        pattern=str(frames[0].parent/'frame_%03d.bmp')
        z=subprocess.run(['ffmpeg','-y','-v','error','-framerate','14','-i',pattern,'-filter_complex',
             '[0:v]split[a][b];[a]palettegen=max_colors=240[p];[b][p]paletteuse=dither=bayer',
             '-loop','0',str(out)],capture_output=True,text=True,timeout=150)
        if z.returncode==0 and out.is_file():mechanism='FFMPEG_PALETTEGEN';
    if mechanism is None:mechanism=gif_fallback(frames,out)
    data=out.read_bytes()
    if data[:6]!=b'GIF89a' or data[-1:]!=b'\x3b' or len(data)<850:
        raise RuntimeError('GIF_STRUCTURE_OR_SIZE_INVALID')
    try:
        from PIL import Image
        with Image.open(out) as image:
            if image.n_frames!=len(frames):raise RuntimeError('GIF_FRAME_COUNT_INVALID '+str(image.n_frames))
            for i in [0,len(frames)//2,len(frames)-1]:image.seek(i);image.load()
    except ImportError:pass
    return {'encoder':mechanism,'frames':len(frames),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),
            'width':struct.unpack_from('<H',data,6)[0],'height':struct.unpack_from('<H',data,8)[0]}
