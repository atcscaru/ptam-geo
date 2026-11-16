"""PTAM GEO: consultas indicativas ao OpenStreetMap com redundância e fontes rastreáveis."""
import math
import re
from urllib.parse import urlparse, unquote
import requests

HEADERS = {'User-Agent': 'PTAM-GEO/1.1 (geographic research; contact: repository administrator)'}
ENDPOINTS = (
    'https://overpass.private.coffee/api/interpreter',
    'https://overpass.kumi.systems/api/interpreter',
    'https://overpass-api.de/api/interpreter',
)
CATEGORIES = {
    'Educação pública': [('amenity','school'),('amenity','university'),('amenity','college'),('amenity','kindergarten')],
    'Saúde': [('amenity','hospital'),('amenity','clinic'),('amenity','doctors'),('amenity','pharmacy')],
    'Órgãos públicos': [('amenity','townhall'),('office','government'),('amenity','courthouse'),('amenity','police'),('amenity','post_office')],
    'Comércio e serviços': [('shop','supermarket'),('shop','mall'),('shop','department_store'),('amenity','bank'),('amenity','atm'),('shop','convenience'),('shop','chemist'),('amenity','fuel')],
    'Mobilidade': [('highway','bus_stop'),('public_transport','platform'),('amenity','bus_station')]
}

def parse_coordinates(value):
    value = value.strip()
    if not value:
        raise ValueError('Informe um link ou coordenadas.')
    decoded = unquote(value)
    patterns = [
        r'!3d(-?\d+(?:\.\d+)?)!4d(-?\d+(?:\.\d+)?)',
        r'@(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)',
        r'[?&](?:q|query|ll)=(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)',
        r'(-?\d{1,2}(?:\.\d+)?)\s*[,;]\s*(-?\d{1,3}(?:\.\d+)?)'
    ]
    for pattern in patterns:
        match = re.search(pattern, decoded)
        if match:
            lat, lon = float(match[1]), float(match[2])
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return lat, lon
            raise ValueError('Latitude ou longitude fora do intervalo permitido.')
    raise ValueError('Não foi possível extrair coordenadas. Informe latitude e longitude no formato -8.28, -35.97.')

def resolve_input(value):
    value = value.strip()
    if value.startswith(('https://', 'http://')):
        host = (urlparse(value).hostname or '').lower()
        if not (host == 'google.com' or host.endswith('.google.com') or host in ('maps.app.goo.gl', 'goo.gl')):
            raise ValueError('Somente links do Google Maps são aceitos neste campo.')
        try:
            return parse_coordinates(value)
        except ValueError:
            try:
                response = requests.get(value, headers=HEADERS, timeout=(4, 9), allow_redirects=True)
                response.raise_for_status()
                final_host = (urlparse(response.url).hostname or '').lower()
                if not (final_host == 'google.com' or final_host.endswith('.google.com') or final_host in ('maps.app.goo.gl', 'goo.gl')):
                    raise ValueError('O link redirecionou para um domínio não autorizado.')
                return parse_coordinates(response.url)
            except requests.RequestException as exc:
                raise ValueError('Não foi possível abrir o link. Cole as coordenadas do Google Maps.') from exc
    return parse_coordinates(value)

def haversine(a,b,c,d):
    r=6371008.8
    p1,p2=math.radians(a),math.radians(c)
    dp=math.radians(c-a); dl=math.radians(d-b)
    x=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return round(2*r*math.asin(min(1,math.sqrt(x))))

def _overpass(query, endpoint=None):
    """Tentativas sequenciais; falha explícita, nunca substituída por resultados fictícios."""
    endpoints = ([endpoint] if endpoint else []) + [e for e in ENDPOINTS if e != endpoint]
    errors = []
    for url in endpoints:
        try:
            response = requests.post(url, data={'data':query}, headers=HEADERS, timeout=(5, 17))
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict) or not isinstance(data.get('elements'), list):
                raise ValueError('Resposta geográfica inválida')
            return data
        except (requests.RequestException, ValueError) as exc:
            errors.append(f'{urlparse(url).hostname}: {type(exc).__name__}')
    raise RuntimeError('Servidores Overpass indisponíveis após tentativas alternativas (' + '; '.join(errors) + '). Tente novamente mais tarde. Nenhum resultado foi inventado.')

def query_osm(lat,lon,radius=1000,endpoint=None):
    if not (-90<=lat<=90 and -180<=lon<=180):
        raise ValueError('Coordenadas inválidas.')
    if not 50 <= radius <= 5000:
        raise ValueError('Raio deve estar entre 50 e 5.000 metros.')
    pairs = sorted(set(pair for items in CATEGORIES.values() for pair in items))
    clauses = [f'nwr["{k}"="{v}"](around:{int(radius)},{lat},{lon});' for k,v in pairs]
    query='[out:json][timeout:15];(' + ''.join(clauses) + ');out center tags;'
    data=_overpass(query,endpoint)
    result=[];seen=set()
    for el in data['elements']:
        tags=el.get('tags',{})
        name=tags.get('name')
        if not name: continue
        center=el.get('center',el)
        a,b=center.get('lat'),center.get('lon')
        if a is None or b is None: continue
        distance=haversine(lat,lon,a,b)
        if distance>radius: continue
        cat=next((category for category,p in CATEGORIES.items() if any(tags.get(k)==v for k,v in p)),'Outros')
        key=(el.get('type'),el.get('id'))
        if key in seen: continue
        seen.add(key)
        result.append({'incluir':False,'categoria':cat,'nome':name,'distância_reta_m':distance,'distância_vias_m':None,
            'latitude':a,'longitude':b,'fonte':f'https://www.openstreetmap.org/{el["type"]}/{el["id"]}',
            'confiança':'Cadastro OSM não verificado', 'observação':'Confirmar nome, atividade, natureza pública/privada e funcionamento',
            'texto_editado':''})
    return sorted(result,key=lambda x:x['distância_reta_m'])

def road_distance(lat,lon,lat2,lon2,timeout=8):
    """OSRM público de demonstração. Distância viária aproximada, sem garantia de disponibilidade."""
    url=f'https://router.project-osrm.org/route/v1/driving/{lon},{lat};{lon2},{lat2}'
    try:
        r=requests.get(url,params={'overview':'false'},timeout=timeout,headers=HEADERS)
        r.raise_for_status(); data=r.json()
        if data.get('code')=='Ok' and data.get('routes'):
            return round(data['routes'][0]['distance'])
    except (requests.RequestException,ValueError,KeyError,IndexError):
        pass
    return None

def street_context(lat,lon,radius=150,endpoint=None):
    """Cadastro indicativo de via/superfície. Não comprova pavimentação nem esquina."""
    query=f'[out:json][timeout:15];way["highway"](around:{int(radius)},{lat},{lon});out center tags;'
    data=_overpass(query,endpoint)
    roads=[]
    for el in data['elements']:
        tags=el.get('tags',{}); p=el.get('center',{})
        if 'lat' in p and 'lon' in p:
            roads.append((haversine(lat,lon,p['lat'],p['lon']),tags,el))
    if not roads:
        return {'logradouro':'Não identificado','pavimentação':'Não verificada','fonte':'','observação':'Confirmar por vistoria'}
    roads.sort(key=lambda x:x[0]); _,tags,el=roads[0]
    return {'logradouro':tags.get('name','Sem nome cadastrado'),
            'pavimentação':tags.get('surface','Não informada no OSM'),
            'fonte':f'https://www.openstreetmap.org/way/{el["id"]}',
            'observação':'Dado cadastral OSM. Confirmar em vistoria; centro geométrico da via não garante a via mais próxima.'}
