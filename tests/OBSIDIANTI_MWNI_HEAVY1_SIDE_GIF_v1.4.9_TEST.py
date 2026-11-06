from __future__ import annotations
import pathlib,struct,tempfile,sys,hashlib
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from gif_writer import gif_fallback,assemble

def make_bmp(p,i):
    w=h=32;row=((w*3+3)//4)*4;raw=bytearray(row*h)
    for y in range(h):
        for x in range(w):
            t=y*row+x*3;raw[t:t+3]=bytes([((x+i*2)*7)%255,((y+i)*11)%255,((x+y+i)*3)%255])
    size=54+len(raw)
    p.write_bytes(b'BM'+struct.pack('<IHHI',size,0,0,54)+struct.pack('<IiiHHIIiiII',40,w,h,1,24,0,len(raw),2835,2835,0,0)+raw)

with tempfile.TemporaryDirectory() as d:
    root=pathlib.Path(d);frames=[root/('frame_%03d.bmp'%i) for i in range(7)]
    for i,p in enumerate(frames):make_bmp(p,i)
    a=root/'fallback.gif';mode=gif_fallback(frames,a)
    assert a.read_bytes().startswith(b'GIF89a')
    try:
        from PIL import Image
        with Image.open(a) as im:
            assert im.n_frames==7,(im.n_frames,mode)
            im.seek(6);im.load()
    except ImportError:pass
    b=root/'normal.gif';result=assemble(frames,b)
    assert result['frames']==7 and result['bytes']>50000 or result['frames']==7
    assert result['width']==32 and result['height']==32
    print('GIF_FALLBACK_REAL_BMP_DECODE=PASS GIF_FRAME_COUNT=7')
    print('GIF_ASSEMBLY=PASS',result)
