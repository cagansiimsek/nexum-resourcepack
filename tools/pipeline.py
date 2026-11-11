from pathlib import Path

from io import BytesIO

import base64

import hashlib

import json

import math

import random

import uuid

import zipfile

import numpy as np

from PIL import Image, ImageDraw, ImageFont

CREDIT = "SkyGrind combined pack 2026-11-12; procedural cuboid/pixel art"
UUID_NS = "skygrind/combined-2026-11-12/"

FACES = {
    'north': [(1,1,0),(0,1,0),(0,0,0),(1,0,0)],
    'south': [(0,1,1),(1,1,1),(1,0,1),(0,0,1)],
    'east': [(1,1,1),(1,1,0),(1,0,0),(1,0,1)],
    'west': [(0,1,0),(0,1,1),(0,0,1),(0,0,0)],
    'up': [(0,1,0),(1,1,0),(1,1,1),(0,1,1)],
    'down': [(0,0,1),(1,0,1),(1,0,0),(0,0,0)],
}

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def strict(raw):
    def pairs(xs):
        result = {}
        for key, value in xs:
            assert key not in result, f'Duplicate JSON key: {key}'
            result[key] = value
        return result
    def invalid(value):
        raise ValueError(value)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

def rotation(pitch, yaw, roll=0):
    a,b,c = map(math.radians, (pitch,yaw,roll))
    X=np.array([[1,0,0],[0,math.cos(a),-math.sin(a)],[0,math.sin(a),math.cos(a)]])
    Y=np.array([[math.cos(b),0,math.sin(b)],[0,1,0],[-math.sin(b),0,math.cos(b)]])
    Z=np.array([[math.cos(c),-math.sin(c),0],[math.sin(c),math.cos(c),0],[0,0,1]])
    return Z @ X @ Y

class Relic:
    def __init__(self,key):
        self.key=key
        self.parts=[]
    def box(self,name,a,b,mat,top=None,rot=None,origin=None):
        assert all(x<y for x,y in zip(a,b)),name
        self.parts.append({'name':name,'from':list(a),'to':list(b),'mat':mat,'top':top,
                           'rot':rot,'origin':list(origin or [8,8,8])})
    def ring(self,name,x1,x2,z1,z2,y1,y2,width,mat):
        B=self.box
        B(name+' front',(x1,y1,z1),(x2,y2,z1+width),mat)
        B(name+' rear',(x1,y1,z2-width),(x2,y2,z2),mat)
        B(name+' left',(x1,y1,z1+width),(x1+width,y2,z2-width),mat)
        B(name+' right',(x2-width,y1,z1+width),(x2,y2,z2-width),mat)
        return self

def local_vertices(element):
    a,b=np.array(element['from']),np.array(element['to'])
    points=np.array([a+(b-a)*np.array(v) for v in [(x,y,z) for x in (0,1) for y in (0,1) for z in (0,1)]])
    if 'rotation' in element:
        r=element['rotation']; angles=[0,0,0]; angles['xyz'.index(r['axis'])]=r['angle']
        pivot=np.array(r['origin']); points=(points-pivot)@rotation(*angles).T+pivot
    return points

def export(m):
    sheet=Image.new('RGBA',(SIZE,SIZE),(0,0,0,0))
    x=y=2; row=0; elements=[]; cubes=[]; tiles=[]
    for i,p in enumerate(m.parts):
        dx,dy,dz=np.array(p['to'])-p['from']; faces={}; bbfaces={}
        for j,(face,w,h) in enumerate([('north',dx,dy),('south',dx,dy),('east',dz,dy),
                                     ('west',dz,dy),('up',dx,dz),('down',dx,dz)]):
            w,h=max(1,math.ceil(w*2)),max(1,math.ceil(h*2))
            if x+w+2>SIZE: x=2; y+=row+4; row=0
            assert y+h+2<=SIZE, f'{m.key}: atlas full'
            material=p['top'] if face in ('up','down') and p['top'] else p['mat']
            tile=pixel_tile(material,w,h,i*31+j,face)
            # Extruded two-pixel edge gutters protect against texture bleeding.
            sheet.paste(tile,(x,y))
            for n in (1,2):
                sheet.paste(tile.crop((0,0,w,1)),(x,y-n))
                sheet.paste(tile.crop((0,h-1,w,h)),(x,y+h-1+n))
                sheet.paste(tile.crop((0,0,1,h)),(x-n,y))
                sheet.paste(tile.crop((w-1,0,w,h)),(x+w-1+n,y))
            for xx,yy,px,py in [(x-2,y-2,0,0),(x+w,y-2,w-1,0),
                                (x-2,y+h,0,h-1),(x+w,y+h,w-1,h-1)]:
                sheet.paste(Image.new('RGBA',(2,2),tile.getpixel((px,py))),(xx,yy))
            uv=[x,y,x+w,y+h]
            faces[face]={'uv':[v*16/SIZE for v in uv],'texture':'#0'}
            bbfaces[face]={'uv':uv,'texture':0,'rotation':0}
            tiles.append({'cube':p['name'],'face':face,'material':material,'pixels':uv})
            x+=w+4; row=max(row,h)
        element={'name':p['name'],'from':p['from'],'to':p['to'],'faces':faces}
        angles=[0,0,0]
        if p['rot']:
            axis,angle=p['rot']; angles['xyz'.index(axis)]=angle
            element['rotation']={'axis':axis,'angle':angle,'origin':p['origin'],'rescale':False}
        elements.append(element)
        cubes.append({'name':p['name'],'type':'cube',
            'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,UUID_NS+m.key+'/'+str(i))),
            'from':p['from'],'to':p['to'],'origin':p['origin'],'rotation':angles,
            'box_uv':False,'uv_offset':[0,0],'faces':bbfaces,'rescale':False,
            'shade':True,'visibility':True,'export':True})
    path=ROOT/'textures'/f'{m.key}.png'; path.parent.mkdir(exist_ok=True); sheet.save(path)
    texture=f'grindcore:item/workstations/{m.key}'
    model={'credit':CREDIT,
           'ambientocclusion':False,'gui_light':'front','texture_size':[SIZE,SIZE],
           'textures':{'0':texture,'particle':texture},'elements':elements,'display':displays(m.parts)}
    write(PACK/'assets/grindcore/models/item'/f'{m.key}.json',model)
    write(PACK/'assets/grindcore/items'/f'{m.key}.json',
          {'model':{'type':'minecraft:model','model':f'grindcore:item/{m.key}'}})
    packed=PACK/'assets/grindcore/textures/item/workstations'/path.name
    packed.parent.mkdir(parents=True,exist_ok=True); packed.write_bytes(path.read_bytes())
    project={'meta':{'format_version':'4.10','model_format':'java_block','box_uv':False},
        'name':m.key,'model_identifier':m.key,'visible_box':[1,1,0],
        'resolution':{'width':SIZE,'height':SIZE},'elements':cubes,
        'outliner':[c['uuid'] for c in cubes],
        'textures':[{'name':path.name,'folder':'item/workstations','namespace':'grindcore','id':'0',
            'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,m.key+'/texture')),
            'width':SIZE,'height':SIZE,'uv_width':SIZE,'uv_height':SIZE,
            'mode':'bitmap','source':'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode()}],
        'display':model['display'],'front_gui_light':True,'ambientocclusion':False}
    write(ROOT/'source'/f'{m.key}.bbmodel',project)
    write(ROOT/'uv-layout'/f'{m.key}.json',{'sheet':[SIZE,SIZE],'texels_per_block':32,
                                          'edge_gutter_pixels':2,'faces':tiles})
    return model,sheet

def render(model,sheet,size=480,pitch=25,yaw=210,gui=False):
    """Depth-buffered orthographic renderer adapted from the workstation renderer.
    Reads exported elements/UVs; uses actual GUI rotation/scale/translation.
    All large views share size/21 pixels per model unit (no per-model zoom).
    """
    disp=model['display']['gui'] if gui else None
    R=rotation(*disp['rotation']) if gui else rotation(pitch,yaw)
    out=np.zeros((size,size,4),dtype=np.uint8)
    depth=np.full((size,size),-1e9)
    tex=np.array(sheet)
    shade={'up':1,'down':.6,'north':.91,'south':.82,'west':.72,'east':.86}
    pixel_scale=size/16 if gui else size/21
    for element in model['elements']:
        a,b=np.array(element['from']),np.array(element['to'])
        for face,f in element['faces'].items():
            vertices=np.array([a+(b-a)*np.array(v) for v in FACES[face]])
            if 'rotation' in element:
                r=element['rotation']; angles=[0,0,0]; angles['xyz'.index(r['axis'])]=r['angle']
                pivot=np.array(r['origin']); vertices=(vertices-pivot)@rotation(*angles).T+pivot
            v=(vertices-8)@R.T
            if gui:
                v=v*np.array(disp['scale'])+np.array(disp['translation'])
            screen=np.column_stack((v[:,0]*pixel_scale+size/2,
                                     -v[:,1]*pixel_scale+size/2,v[:,2]))
            uv=np.array(f['uv'])*sheet.width/16
            coords=np.array([[uv[0],uv[1]],[uv[2],uv[1]],[uv[2],uv[3]],[uv[0],uv[3]]])
            for indices in ((0,1,2),(0,2,3)):
                p,q=screen[list(indices)],coords[list(indices)]
                lo=np.maximum(np.floor(p[:,:2].min(axis=0)).astype(int),0)
                hi=np.minimum(np.ceil(p[:,:2].max(axis=0)).astype(int),size-1)
                if np.any(hi<lo): continue
                xx,yy=np.meshgrid(np.arange(lo[0],hi[0]+1)+.5,np.arange(lo[1],hi[1]+1)+.5)
                den=(p[1,1]-p[2,1])*(p[0,0]-p[2,0])+(p[2,0]-p[1,0])*(p[0,1]-p[2,1])
                if abs(den)<1e-8: continue
                w0=((p[1,1]-p[2,1])*(xx-p[2,0])+(p[2,0]-p[1,0])*(yy-p[2,1]))/den
                w1=((p[2,1]-p[0,1])*(xx-p[2,0])+(p[0,0]-p[2,0])*(yy-p[2,1]))/den
                w2=1-w0-w1
                z=w0*p[0,2]+w1*p[1,2]+w2*p[2,2]
                ys,xs=slice(lo[1],hi[1]+1),slice(lo[0],hi[0]+1)
                mask=(w0>=-1e-7)&(w1>=-1e-7)&(w2>=-1e-7)&(z>depth[ys,xs])
                u=np.clip((w0*q[0,0]+w1*q[1,0]+w2*q[2,0]).astype(int),int(uv[0]),int(uv[2])-1)
                t=np.clip((w0*q[0,1]+w1*q[1,1]+w2*q[2,1]).astype(int),int(uv[1]),int(uv[3])-1)
                color=tex[t,u].copy()
                color[:,:,:3]=np.rint(color[:,:,:3]*shade[face]).astype(np.uint8)
                mask &= color[:,:,3]>0
                out[ys,xs][mask]=color[mask]
                depth[ys,xs][mask]=z[mask]
    return Image.fromarray(out)

def font(size):
    return ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',size)

def geometry_checks(model):
    elements=model['elements']
    assert 0<len(elements)<=55
    boxes=[(local_vertices(e).min(axis=0),local_vertices(e).max(axis=0)) for e in elements]
    assert all(np.all(b>a) and np.all(a>=0) and np.all(b<=16) for a,b in boxes)
    connected={0}
    while True:
        additions={j for j,(a,b) in enumerate(boxes) if j not in connected and
                   any(np.all(a<=boxes[i][1]+1e-6) and np.all(b>=boxes[i][0]-1e-6) for i in connected)}
        if not additions: break
        connected.update(additions)
    assert len(connected)==len(elements), 'Disconnected cuboids: '+str([elements[i]['name'] for i in range(len(elements)) if i not in connected])
    # Detect visible, overlapping, same-facing coplanar surfaces. Internal union
    # faces are excluded by probing just outside the candidate surface.
    issues=[]
    for i,(a,b) in enumerate(boxes):
        for j,(c,d) in enumerate(boxes[i+1:],i+1):
            if 'rotation' in elements[i] or 'rotation' in elements[j]: continue
            for axis in range(3):
                others=[n for n in range(3) if n!=axis]
                lo=np.maximum(a[others],c[others]); hi=np.minimum(b[others],d[others])
                if not np.all(hi-lo>1e-6): continue
                for side in (0,1):
                    plane=(a,b)[side][axis]
                    if abs(plane-(c,d)[side][axis])>1e-6: continue
                    probe=np.zeros(3); probe[others]=(lo+hi)/2
                    probe[axis]=plane+(1 if side else -1)*1e-4
                    hidden=any(np.all(probe>aa+1e-7) and np.all(probe<bb-1e-7) for aa,bb in boxes)
                    if not hidden: issues.append([elements[i]['name'],elements[j]['name'],axis,side])
    assert not issues, 'Exposed coplanar overlap: '+str(issues)
    return {'connected_cuboids':len(connected),'visible_coplanar_overlaps':len(issues),
            'contact_check':'transformed AABB adjacency (not an exact rotated-solid intersection test)',
            'coplanar_check':'exposed axis-aligned faces; additional transformed polygon check recorded separately'}

def validate():
    stats={}
    for key in IDS:
        model=strict((PACK/'assets/grindcore/models/item'/f'{key}.json').read_bytes())
        source=strict((ROOT/'source'/f'{key}.bbmodel').read_bytes())
        raw=(ROOT/'textures'/f'{key}.png').read_bytes()
        assert source['meta']['model_format']=='java_block'
        assert source['resolution']=={'width':SIZE,'height':SIZE}
        assert len(model['elements'])==len(source['elements'])
        assert not any(field in source['textures'][0] for field in ('path','relative_path'))
        assert base64.b64decode(source['textures'][0]['source'].split(',',1)[1])==raw
        assert (PACK/'assets/grindcore/textures/item/workstations'/f'{key}.png').read_bytes()==raw
        tex=Image.open(BytesIO(raw)); tex.load(); assert tex.mode=='RGBA' and tex.size==(SIZE,SIZE)
        definition=strict((PACK/'assets/grindcore/items'/f'{key}.json').read_bytes())
        assert definition=={'model':{'type':'minecraft:model','model':f'grindcore:item/{key}'}}
        expected=f'grindcore:item/workstations/{key}'
        assert model['textures']=={'0':expected,'particle':expected}
        for element,cube in zip(model['elements'],source['elements']):
            assert element['from']==cube['from'] and element['to']==cube['to']
            if 'rotation' in element:
                r=element['rotation']; angles=[0,0,0]; angles['xyz'.index(r['axis'])]=r['angle']
                assert r['angle'] in (-45,-22.5,0,22.5,45) and not r['rescale']
                assert cube['origin']==r['origin'] and cube['rotation']==angles
            else: assert cube['origin']==[8,8,8] and cube['rotation']==[0,0,0]
            for face,f in element['faces'].items():
                assert face in FACES and f['texture']=='#0'
                assert len(f['uv'])==4 and all(math.isfinite(v) and 0<=v<=16 for v in f['uv'])
                assert cube['faces'][face]['uv']==[v*16 for v in f['uv']]
                l,t,r,b=map(int,cube['faces'][face]['uv'])
                assert r>l and b>t and tex.crop((l,t,r,b)).getchannel('A').getextrema()==(255,255)
                for n in (1,2):
                    assert tex.crop((l,t-n,r,t-n+1)).tobytes()==tex.crop((l,t,r,t+1)).tobytes()
                    assert tex.crop((l,b+n-1,r,b+n)).tobytes()==tex.crop((l,b-1,r,b)).tobytes()
                    assert tex.crop((l-n,t,l-n+1,b)).tobytes()==tex.crop((l,t,l+1,b)).tobytes()
                    assert tex.crop((r+n-1,t,r+n,b)).tobytes()==tex.crop((r-1,t,r,b)).tobytes()
        assert source['display']==model['display']
        assert set(model['display'])=={'gui','ground','fixed','head','firstperson_righthand','firstperson_lefthand','thirdperson_righthand','thirdperson_lefthand'}
        for context,values in model['display'].items():
            for channel in ('rotation','translation','scale'):
                assert len(values[channel])==3 and all(math.isfinite(x) for x in values[channel])
            assert all(0<s<=4 for s in values['scale'])
        icons={}
        for n in (16,32):
            p=ROOT/'previews'/f'{key}-inventory-{n}x{n}.png'
            im=Image.open(p); assert im.size==(n,n)
            bounds=im.getbbox(); assert bounds and min(bounds[:2])>=1 and max(bounds[2:])<=n-1,(key,n,bounds)
            icons[str(n)]=list(bounds)
        stats[key]={'geometry':geometry_checks(model),'inventory_bounds':icons,
                    'cuboids':len(model['elements']),'texture_sha256':sha(raw)}
    # Reuse retained official-client atlas/model evidence; never infer support
    # from compatibility metadata alone.
    evidence=strict((IMAGES/'resource-pack/compatibility/evidence.json').read_bytes())
    refs=[]
    for minor in range(4,12):
        version=f'1.21.{minor}'; data=evidence['clients'][version]
        assert data['jar_checked']
        vanilla=data['reference_assets']
        assert vanilla['assets/minecraft/items/bread.json']['model']['type']=='minecraft:model'
        atlas='items' if minor==11 else 'blocks'
        assert any(s.get('source')=='item' and s.get('prefix')=='item/' and
                   s.get('type') in ('directory','minecraft:directory')
                   for s in vanilla[f'assets/minecraft/atlases/{atlas}.json']['sources'])
        refs.append({'client':version,'atlas':atlas,'status':'PASS (reference/static)'})
    return {'models':stats,'client_reference_checks':refs}

def preservation_snapshot():
    target=ROOT/'validation/preservation-before.json'
    if target.exists(): return strict(target.read_bytes())
    protected=[p for p in IMAGES.rglob('*') if p.is_file() and ROOT not in p.parents]
    for base in ('plugin-configs/GrindCore','plugins/grindcore/src/main/resources'):
        protected.extend(REPO/base/file for file in ('items.yml','workbenches.yml'))
    result={str(p):sha(p.read_bytes()) for p in protected}
    write(target,result)
    return result

def zip_paths(path,payload):
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as archive:
        for relative,raw in sorted(payload.items()):
            assert not relative.startswith('/') and '..' not in Path(relative).parts
            info=zipfile.ZipInfo(relative,date_time=(2026,10,30,0,0,0)); info.compress_type=zipfile.ZIP_DEFLATED
            archive.writestr(info,raw)
    with zipfile.ZipFile(path) as archive:
        assert archive.testzip() is None and len(archive.namelist())==len(set(archive.namelist()))
        assert set(archive.namelist())==set(payload)
        assert all(archive.read(p)==raw for p,raw in payload.items())

def collision_check():
    keys={f'grindcore:{key}' for key in IDS}
    assert len(keys)==3
    scanned=[]; collisions=[]
    for p in IMAGES.rglob('*'):
        if not p.is_file() or ROOT in p.parents: continue
        if p.suffix=='.zip':
            with zipfile.ZipFile(p) as archive:
                for name in archive.namelist():
                    if name.startswith('assets/grindcore/items/') and name.endswith('.json'):
                        model='grindcore:'+Path(name).stem
                        if model in keys: collisions.append([str(p),name])
            scanned.append(str(p))
        elif p.suffix=='.json' and '/assets/grindcore/items/' in p.as_posix():
            if 'grindcore:'+p.stem in keys: collisions.append(str(p))
            scanned.append(str(p))
    assert not collisions, collisions
    write(ROOT/'validation/key-collision-check.json',{'status':'PASS','allocated_in_candidate':sorted(keys),
         'existing_pack_sources_and_archives_scanned':scanned,'collisions':collisions,
         'registry_scan':'task-start rg across existing asset/source/config/vault text found no proposed key occurrences',
         'registry_modified':False})

def polygon_overlap(subject,clip):
    def cross(a,b): return float(a[0]*b[1]-a[1]*b[0])
    # Positive/negative clipping orientation is determined from signed area.
    sign=1 if sum(cross(clip[i],clip[(i+1)%len(clip)]) for i in range(len(clip)))>0 else -1
    result=[np.array(p) for p in subject]
    for i in range(len(clip)):
        a,b=np.array(clip[i]),np.array(clip[(i+1)%len(clip)])
        incoming=result;result=[]
        if not incoming: break
        for j,end in enumerate(incoming):
            start=incoming[j-1]
            ds=sign*cross(b-a,start-a); de=sign*cross(b-a,end-a)
            if (ds>=-1e-9)!=(de>=-1e-9):
                result.append(start+(end-start)*(ds/(ds-de)))
            if de>=-1e-9: result.append(end)
    if len(result)<3: return []
    if abs(sum(cross(result[i],result[(i+1)%len(result)]) for i in range(len(result))))<1e-7: return []
    return result

def rotated_surface_check(model):
    normals={'north':[0,0,-1],'south':[0,0,1],'east':[1,0,0],'west':[-1,0,0],'up':[0,1,0],'down':[0,-1,0]}
    groups={}; local=[]
    for i,e in enumerate(model['elements']):
        a,b=np.array(e['from']),np.array(e['to']); R=np.eye(3); origin=np.array([8,8,8])
        if 'rotation' in e:
            r=e['rotation']; angles=[0,0,0]; angles['xyz'.index(r['axis'])]=r['angle']
            R=rotation(*angles);origin=np.array(r['origin'])
        local.append((a,b,R,origin))
        for face in e['faces']:
            vertices=np.array([a+(b-a)*np.array(p) for p in FACES[face]])
            vertices=(vertices-origin)@R.T+origin
            n=R@np.array(normals[face]);distance=float(vertices[0]@n)
            groups.setdefault(tuple(np.round(n,7))+(round(distance,7),),[]).append((i,face,vertices,n,distance))
    issues=[]
    for faces in groups.values():
        for index,(i,face,vertices,n,distance) in enumerate(faces):
            dropped=int(np.argmax(np.abs(n))); axes=[k for k in range(3) if k!=dropped]
            p=vertices[:,axes]
            for j,other_face,other,_,_ in faces[index+1:]:
                if i==j: continue
                q=other[:,axes]
                if np.any(np.minimum(p.max(axis=0),q.max(axis=0))-np.maximum(p.min(axis=0),q.min(axis=0))<1e-7): continue
                overlap=polygon_overlap(p,q)
                if not overlap: continue
                centre=np.mean(overlap,axis=0); point=np.zeros(3);point[axes]=centre
                point[dropped]=(distance-float(n[axes]@centre))/n[dropped]
                point+=n*.0001
                covered=False
                for a,b,R,origin in local:
                    probe=(point-origin)@R+origin
                    if np.all(probe>a+1e-7) and np.all(probe<b-1e-7): covered=True;break
                if not covered: issues.append([model['elements'][i]['name'],model['elements'][j]['name'],face,other_face])
    return issues
