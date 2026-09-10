import struct

class BB:
    def __init__(self, d): self.d=d; self.i=0
    def byte(self):
        b=self.d[self.i]; self.i+=1; return b
    def varuint(self):
        v=0; s=0
        while True:
            b=self.byte(); v |= (b&0x7f)<<s; s+=7
            if not (b&0x80): break
        return v & 0xFFFFFFFF
    def varint(self):
        v=self.varuint()
        return ~(v>>1) if (v&1) else (v>>1)
    def varfloat(self):
        first=self.d[self.i]
        if first==0: self.i+=1; return 0.0
        b=self.d[self.i:self.i+4]; self.i+=4
        # kiwi float: bytes rotated
        n=b[0]|(b[1]<<8)|(b[2]<<16)|(b[3]<<24)
        n=((n<<23)|(n>>9)) & 0xFFFFFFFF
        return struct.unpack('<f', struct.pack('<I', n))[0]
    def string(self):
        s=self.i
        while self.d[self.i]!=0: self.i+=1
        out=self.d[s:self.i].decode('utf-8','replace'); self.i+=1
        return out
    def bytes_(self):
        n=self.varuint(); b=self.d[self.i:self.i+n]; self.i+=n; return b
    def bool(self): return bool(self.byte())
    def uint(self): return self.varuint()
    def int(self): return self.varint()

TYPES={0:'bool',1:'byte',2:'int',3:'uint',4:'float',5:'string',6:'int64',7:'uint64'}

def parse_schema(data):
    bb=BB(data)
    n=bb.varuint()
    defs=[]
    for _ in range(n):
        name=bb.string(); kind=bb.byte(); fc=bb.varuint()
        fields=[]
        for _ in range(fc):
            fn=bb.string(); ft=bb.varint(); arr=bb.bool(); val=bb.varuint()
            fields.append(dict(name=fn,type=ft,array=arr,value=val))
        defs.append(dict(name=name,kind=kind,fields=fields))
    return defs

class Schema:
    def __init__(self, defs):
        self.defs=defs
        self.by_name={d['name']:i for i,d in enumerate(defs)}
    def read(self, bb, idx):
        d=self.defs[idx]
        if d['kind']==0:  # ENUM
            v=bb.varuint()
            for f in d['fields']:
                if f['value']==v: return f['name']
            return v
        if d['kind']==1:  # STRUCT
            return {f['name']: self.read_field(bb,f) for f in d['fields']}
        # MESSAGE
        out={}
        while True:
            t=bb.varuint()
            if t==0: return out
            f=next((x for x in d['fields'] if x['value']==t), None)
            if f is None: raise ValueError(f"unknown field {t} in {d['name']}")
            out[f['name']]=self.read_field(bb,f)
    def read_field(self, bb, f):
        if f['array']:
            n=bb.varuint()
            return [self.read_value(bb,f['type']) for _ in range(n)]
        return self.read_value(bb,f['type'])
    def read_value(self, bb, t):
        if t<0:
            k=TYPES[-t-1]
            return dict(bool=bb.bool,byte=bb.byte,int=bb.int,uint=bb.uint,
                        float=bb.varfloat,string=bb.string,
                        int64=bb.int,uint64=bb.uint)[k]()
        return self.read(bb,t)
