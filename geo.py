"""Geographic lookup using public OpenStreetMap endpoints. No fabricated results."""
import math, re, requests
from urllib.parse import urlparse, parse_qs, unquote

HEADERS={'User-Agent':'PTAM-GEO/1.0 (research prototype; contact: local deployment administrator)'}
CATEGORIES={
 'Educação pública': [('amenity','school'),('amenity','university'),('amenity','college'),('amenity','kindergarten')],
 'Saúde': [('amenity','hospital'),('amenity','clinic'),('amenity','doctors'),('amenity','pharmacy')],
 'Órgãos públicos': [('amenity','townhall'),('office','government'),('amenity','courthouse'),('amenity','police'),('amenity','post_office')],
 'Comércio e serviços': [('shop','supermarket'),('shop','mall'),('shop','department_store'),('amenity','bank'),('amenity','atm'),('shop','convenience'),('shop','chemist'),('amenity','fuel')],
 'Mobilidade': [('highway','bus_stop'),('public_transport','platform'),('amenity','bus_station')]
}

def parse_coordinates(value):
    value=value.strip()
    if not value: raise ValueError('Informe um link ou coordenadas.')
    match=re.search(r'!3d(-?\d+\.\d+)!4d(-?\d+\.\d+)',value)
    if match: return float(match[1]),float(match[2])
    for pattern in [r'@(-?\d+\.\d+),(-?\d+\.\d+)',r'[?&](?:q|query|ll)=(-?\d+\.\d+)%?2[Cc](-?\d+\.\d+)',r'(-?\d{1,2}\.\d+)\s*[,;]\s*(-?\d{1,3}\.\d+)']:
        match=re.search(pattern,unquote(value))
        if match: return float(match[1]),float(match[2])
    raise ValueError('Não foi possível extrair coordenadas. Informe latitude e longitude no formato -8.28, -35.97.')

def resolve_input(value):
    if value.startswith('http'):
        host=urlparse(value).hostname or ''
        if not (host=='google.com' or host.endswith('.google.com') or host=='maps.app.goo.gl' or host=='goo.gl'):
            raise ValueError('Somente links do Google Maps são aceitos neste campo.')
        try:
            response=requests.get(value,headers=HEADERS,timeout=12,allow_redirects=True)
            response.raise_for_status()
            return parse_coordinates(response.url)
        except (requests.RequestException, ValueError):
            return parse_coordinates(value)
    return parse_coordinates(value)

def haversine(a,b,c,d):
    r=6371008.8
    p1,p2=math.radians(a),math.radians(c)
    dp=math.radians(c-a);dl=math.radians(d-b)
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return round(2*r*math.asin(min(1,math.sqrt(x))))

def query_osm(lat,lon,radius=1000,endpoint='https://overpass.kumi.systems/api/interpreter'):
    if not (-90<=lat<=90 and -180<=lon<=180): raise ValueError('Coordenadas inválidas.')
    clauses=[]
    for items in CATEGORIES.values():
        for k,v in items: clauses.append(f'nwr["{k}"="{v}"](around:{radius},{lat},{lon});')
    q='[out:json][timeout:35];(' + ''.join(clauses) + ');out center tags;'
    resp=requests.post(endpoint,data={'data':q},headers=HEADERS,timeout=55)
    resp.raise_for_status()
    result=[];seen=set()
    for el in resp.json().get('elements',[]):
        tags=el.get('tags',{})
        name=tags.get('name')
        if not name: continue
        center=el.get('center',el)
        a,b=center.get('lat'),center.get('lon')
        if a is None or b is None:continue
        distance=haversine(lat,lon,a,b)
        if distance>radius: continue
        cat=next((category for category, pairs in CATEGORIES.items() if any(tags.get(k)==v for k,v in pairs)),'Outros')
        key=(el.get('type'),el.get('id'))
        if key in seen:continue
        seen.add(key)
        result.append({'incluir':False,'categoria':cat,'nome':name,'distância_reta_m':distance,'distância_vias_m':None,
                       'latitude':a,'longitude':b,'fonte':f'https://www.openstreetmap.org/{el["type"]}/{el["id"]}',
                       'confiança':'Cadastro OSM não verificado','observação':'Confirmar nome, atividade e funcionamento',
                       'texto_editado':''})
    return sorted(result,key=lambda x:x['distância_reta_m'])

def road_distance(lat,lon,lat2,lon2,timeout=8):
    """Public OSRM demo service: best-effort only, not for bulk or guaranteed production."""
    url=f'https://router.project-osrm.org/route/v1/driving/{lon},{lat};{lon2},{lat2}'
    try:
        r=requests.get(url,params={'overview':'false'},timeout=timeout,headers=HEADERS)
        r.raise_for_status(); data=r.json()
        if data.get('code')=='Ok' and data.get('routes'):
            return round(data['routes'][0]['distance'])
    except (requests.RequestException,ValueError,KeyError): pass
    return None

def street_context(lat,lon,radius=150,endpoint='https://overpass.kumi.systems/api/interpreter'):
    """Surface and nearest road from OSM; intersection requires verified road topology, not guessed."""
    q=f'[out:json][timeout:25];way["highway"](around:{radius},{lat},{lon});out center tags;'
    r=requests.post(endpoint,data={'data':q},headers=HEADERS,timeout=40)
    r.raise_for_status(); roads=[]
    for el in r.json().get('elements',[]):
        tags=el.get('tags',{});p=el.get('center',{})
        if 'lat' in p and 'lon' in p:
            roads.append((haversine(lat,lon,p['lat'],p['lon']),tags,el))
    if not roads:return {'logradouro':'Não identificado','pavimentação':'Não verificada','fonte':'','observação':'Confirmar por vistoria'}
    roads.sort(key=lambda x:x[0]); _,tags,el=roads[0]
    surface=tags.get('surface','Não informada no OSM')
    return {'logradouro':tags.get('name','Sem nome cadastrado'), 'pavimentação':surface,
            'fonte':f'https://www.openstreetmap.org/way/{el["id"]}',
            'observação':'Dado cadastral OSM, exige confirmação por vistoria. Não comprova tipo de mistura asfáltica.'}
