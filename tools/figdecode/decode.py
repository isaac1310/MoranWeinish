#!/usr/bin/env python3
"""Decode Portfolio.fig into a queryable node tree.

    python3 tools/figdecode/decode.py Portfolio.fig /tmp/figx

Writes <out>/nodes.json (every node), <out>/blobs.json (path geometry) and
<out>/images/ (the raster fills). Then:

    cd tools/figdecode && python3 -c "
    import nodes; nodes.load('/tmp/figx')
    print(nodes.frames())          # the page frames
    nodes.tree('46:121', maxd=3)   # walk one
    "

A .fig is a zip: canvas.fig holds a kiwi schema block (zlib) and the document
(zstd). Needs the zstd CLI — brew install zstd.
"""
import json, os, shutil, struct, subprocess, sys, zipfile, zlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kiwi import parse_schema, Schema, BB

def main(fig, out):
    os.makedirs(out, exist_ok=True)
    with zipfile.ZipFile(fig) as z:
        z.extractall(out)
    raw = open(os.path.join(out, 'canvas.fig'), 'rb').read()
    assert raw[:8] == b'fig-kiwi', 'not a .fig canvas'
    off = 12
    blocks = []
    while off < len(raw):
        n = struct.unpack_from('<I', raw, off)[0]; off += 4
        blocks.append(raw[off:off + n]); off += n
    schema_bytes = zlib.decompress(blocks[0], -15)

    comp = os.path.join(out, '_doc.zst'); open(comp, 'wb').write(blocks[1])
    plain = os.path.join(out, '_doc.bin')
    if not shutil.which('zstd'):
        sys.exit('zstd not found — brew install zstd')
    subprocess.run(['zstd', '-d', '-f', comp, '-o', plain], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    S = Schema(parse_schema(schema_bytes))
    msg = S.read(BB(open(plain, 'rb').read()), S.by_name['Message'])
    json.dump(msg.get('nodeChanges') or [], open(os.path.join(out, 'nodes.json'), 'w'))
    json.dump([bytes(b['bytes']).hex() for b in (msg.get('blobs') or [])],
              open(os.path.join(out, 'blobs.json'), 'w'))
    for f in ('_doc.zst', '_doc.bin', 'canvas.fig'):
        p = os.path.join(out, f)
        if os.path.exists(p): os.remove(p)
    print('%d nodes, %d blobs -> %s' % (len(msg.get('nodeChanges') or []),
                                        len(msg.get('blobs') or []), out))

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'Portfolio.fig',
         sys.argv[2] if len(sys.argv) > 2 else '/tmp/figx')
