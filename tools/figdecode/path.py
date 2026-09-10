import struct, json
import nodes as _n
def BLOBS_():
    return _n.BLOBS
ARITY={0:0,1:2,2:2,4:6}
NAME={0:'Z',1:'M',2:'L',4:'C'}
def parse(idx):
    b=BLOBS_()[idx]; i=0; out=[]
    while i < len(b):
        op=b[i]; i+=1
        n=ARITY[op]
        v=struct.unpack_from('<%df'%n, b, i) if n else ()
        i+=4*n
        out.append((NAME[op], v))
    return out
def to_d(cmds, dx=0.0, dy=0.0, r=3):
    p=[]
    for op,v in cmds:
        if op=='Z': p.append('Z')
        else:
            nums=[round(v[k]+(dx if k%2==0 else dy), r) for k in range(len(v))]
            p.append(op + ' '.join(str(n) for n in nums))
    return ''.join(p).replace('  ',' ').strip()
def bounds(cmds):
    xs=[];ys=[]
    for op,v in cmds:
        for k in range(0,len(v),2): xs.append(v[k]); ys.append(v[k+1])
    return (min(xs),min(ys),max(xs),max(ys)) if xs else None
