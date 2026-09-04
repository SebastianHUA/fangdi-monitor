# -*- coding: utf-8 -*-
import sys, ctypes, struct, zlib, time

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

HWND = int(sys.argv[1])
out = sys.argv[2]

SW_RESTORE = 9
SW_SHOW = 5
PW_RENDERFULLCONTENT = 0x2
SRCCOPY = 0x00CC0020

# 先把窗口恢复到正常状态并置前，避免抓到最小化/遮挡的空帧
user32.ShowWindow(HWND, SW_RESTORE)
time.sleep(0.3)
user32.SetForegroundWindow(HWND)
time.sleep(0.3)

class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]
rc = RECT()
if not user32.GetWindowRect(HWND, ctypes.byref(rc)):
    print("ERROR: GetWindowRect failed")
    sys.exit(1)
l, t, r, b = rc.left, rc.top, rc.right, rc.bottom
w, h = r - l, b - t
if w <= 0 or h <= 0:
    print("ERROR: invalid size", w, h)
    sys.exit(1)

hwndDC = user32.GetWindowDC(HWND)
memDC = gdi32.CreateCompatibleDC(hwndDC)
bmp = gdi32.CreateCompatibleBitmap(hwndDC, w, h)
gdi32.SelectObject(memDC, bmp)

# PrintWindow 让系统把窗口内容真正渲染到 memDC（解决黑白/斜/空帧）
if not user32.PrintWindow(HWND, memDC, PW_RENDERFULLCONTENT):
    # 回退到 BitBlt
    gdi32.BitBlt(memDC, 0, 0, w, h, hwndDC, 0, 0, SRCCOPY)

class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", ctypes.c_uint32),
        ("biWidth", ctypes.c_int32),
        ("biHeight", ctypes.c_int32),
        ("biPlanes", ctypes.c_uint16),
        ("biBitCount", ctypes.c_uint16),
        ("biCompression", ctypes.c_uint32),
        ("biSizeImage", ctypes.c_uint32),
        ("biXPelsPerMeter", ctypes.c_int32),
        ("biYPelsPerMeter", ctypes.c_int32),
        ("biClrUsed", ctypes.c_uint32),
        ("biClrImportant", ctypes.c_uint32),
    ]

bih = BITMAPINFOHEADER()
bih.biSize = ctypes.sizeof(BITMAPINFOHEADER)
bih.biWidth = w
bih.biHeight = -h
bih.biPlanes = 1
bih.biBitCount = 24
bih.biCompression = 0

buf = ctypes.create_string_buffer(w * h * 3)
gdi32.GetDIBits(memDC, bmp, 0, h, buf, ctypes.byref(bih), 0)

gdi32.DeleteObject(bmp)
gdi32.DeleteDC(memDC)
user32.ReleaseDC(HWND, hwndDC)

def png(out_path, pixels, width, height):
    sig = b'\x89PNG\r\n\x1a\n'
    def chunk(typ, data):
        c = typ + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
    ihdr = struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0)
    raw = b''
    stride = width * 3
    for y in range(height):
        raw += b'\x00' + pixels[y*stride:(y+1)*stride]
    idat = zlib.compress(raw, 9)
    with open(out_path, 'wb') as f:
        f.write(sig + chunk(b'IHDR', ihdr) + chunk(b'IDAT', idat) + chunk(b'IEND', b''))

png(out, bytes(buf), w, h)
print("SAVED %s (%dx%d)" % (out, w, h))
