# -*- coding: utf-8 -*-
import struct, zlib

src = 'C:/Users/huaxi/WorkBuddy/Claw/desktop_now.png'
out = 'C:/Users/huaxi/WorkBuddy/Claw/wb_crop.png'

with open(src, 'rb') as f:
    d = f.read()

idat = b''; i = 8; w = h = 0
while i < len(d):
    ln = struct.unpack('>I', d[i:i+4])[0]; typ = d[i+4:i+8]
    if typ == b'IHDR':
        w, h = struct.unpack('>II', d[i+8:i+16])
    if typ == b'IDAT':
        idat += d[i+8:i+8+ln]
    if typ == b'IEND':
        break
    i += 12 + ln

raw = zlib.decompress(idat); stride = w * 3
# WorkBuddy rect (-11,2,1013,730) -> 虚拟桌面内可见 x0=max(0,-11)=0, x1=min(1024,1013)=1013, y0=2, y1=730
x0, y0, x1, y1 = 0, 2, min(w, 1013), 730
cw, ch = x1 - x0, y1 - y0

sig = b'\x89PNG\r\n\x1a\n'
def chunk(typ, data):
    c = typ + data
    return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)

ihdr = struct.pack('>IIBBBBB', cw, ch, 8, 2, 0, 0, 0)
nr = bytearray()
mv = memoryview(raw)
for y in range(y0, y1):
    base = y * (stride + 1) + 1 + x0 * 3
    nr += b'\x00'
    nr += mv[base:base + cw * 3]

idat2 = zlib.compress(bytes(nr), 9)
with open(out, 'wb') as f:
    f.write(sig + chunk(b'IHDR', ihdr) + chunk(b'IDAT', idat2) + chunk(b'IEND', b''))
print('CROPPED %dx%d' % (cw, ch))
