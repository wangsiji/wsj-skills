#!/usr/bin/env python3
"""Generate tabbar PNG icons for UniApp miniprogram."""
import struct, zlib, os, sys

def make_png(w, h, r, g, b):
    def chunk(tag, data):
        c = zlib.crc32(bytes(tag) + data) & 0xffffffff
        return struct.pack('>I', len(data)) + bytes(tag) + data + struct.pack('>I', c)
    raw = b''
    for y in range(h):
        raw += b'\x00' + bytes([r, g, b]) * w
    png = b'\x89PNG\r\n\x1a\n'
    png += chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 2, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(raw))
    png += chunk(b'IEND', b'')
    return png

def main():
    if len(sys.argv) < 2:
        base = '/home/wangsiji/projects/time-box/miniprogram'
    else:
        base = sys.argv[1]

    icons = [
        ('static/tabbar/timebox.png',       81, 81, 81),
        ('static/tabbar/timebox-active.png', 99, 102, 241),
        ('static/tabbar/tools.png',          81, 81, 81),
        ('static/tabbar/tools-active.png',   99, 102, 241),
        ('static/tabbar/mine.png',           81, 81, 81),
        ('static/tabbar/mine-active.png',    99, 102, 241),
    ]
    for rel, r, g, b in icons:
        path = f'{base}/{rel}'
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            f.write(make_png(81, 81, r, g, b))
        print(f'Created {rel}')

if __name__ == '__main__':
    main()
