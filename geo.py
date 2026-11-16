"""PTAM GEO v2: Google Places (New) and Routes APIs. No OSM dependency."""
import math
import re
from urllib.parse import unquote, urlparse
import requests

HEADERS = {'User-Agent': 'PTAM-GEO/2.0 (professional research application)'}
CATEGORIES = {
    'Educação': ['school', 'university', 'preschool', 'primary_school', 'secondary_school'],
    'Saúde': ['hospital', 'medical_clinic', 'doctor', 'pharmacy'],
    'Órgãos públicos': ['city_hall', 'courthouse', 'police', 'post_office'],
    'Comércio e serviços': ['supermarket', 'shopping_mall', 'bank', 'atm', 'gas_station'],
    'Mobilidade': ['bus_station', 'transit_station'],
}

def parse_coordinates(value):
    value = unquote(value.strip())
    if not value:
        raise ValueError('Informe coordenadas ou um link do Google Maps.')
    patterns = [r'!3d(-?\d+(?:\.\d+)?)!4d(-?\d+(?:\.\d+)?)',
                r'@(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)',
                r'(?:[?&](?:q|query|ll)=)(-?\d+(?:\.\d+)?),(-?\d+(?:\.\d+)?)',
                r'^\s*(-?\d+(?:\.\d+)?)\s*[,;]\s*(-?\d+(?:\.\d+)?)\s*$']
    for pattern in patterns:
        m = re.search(pattern, value)
        if m:
            lat, lon = map(float, m.groups())
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return lat, lon
            raise ValueError('Coordenadas fora dos limites geográficos.')
    raise ValueError('Não foram encontradas coordenadas. Use latitude, longitude (ex.: -8.28, -35.97).')

def resolve_input(value):
    if value.strip().startswith('http'):
        host = (urlparse(value).hostname or '').lower()
        if host not in {'google.com', 'maps.app.goo.gl', 'goo.gl'} and not host.endswith('.google.com'):
            raise ValueError('Somente URLs do Google Maps ou coordenadas são aceitas.')
        try:
            return parse_coordinates(value)
        except ValueError:
            try:
                r = requests.get(value, headers=HEADERS, timeout=10, allow_redirects=True)
                r.raise_for_status()
                host_final = (urlparse(r.url).hostname or '').lower()
                if host_final != 'google.com' and not host_final.endswith('.google.com'):
                    raise ValueError('Redirecionamento não reconhecido.')
                return parse_coordinates(r.url)
            except requests.RequestException as exc:
                raise ValueError('Não foi possível resolver o link curto. Cole as coordenadas do Google Maps.') from exc
    return parse_coordinates(value)

def haversine(a,b,c,d):
    r = 6371008.8
    p1, p2 = math.radians(a), math.radians(c)
    dp, dl = math.radians(c-a), math.radians(d-b)
    x = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return round(2*r*math.asin(min(1,math.sqrt(x))))

def _post(url, payload, key, fieldmask, timeout=25):
    headers = {'X-Goog-Api-Key': key, 'X-Goog-FieldMask': fieldmask, 'Content-Type': 'application/json'}
    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=timeout)
        if not resp.ok:
            try:
                info = resp.json().get('error', {})
                msg = info.get('message') or f'HTTP {resp.status_code}'
            except ValueError:
                msg = f'HTTP {resp.status_code}'
            raise RuntimeError(f'Google Maps API: {msg}')
        return resp.json()
    except requests.Timeout as exc:
        raise RuntimeError('Tempo esgotado na consulta ao Google Maps.') from exc
    except requests.RequestException as exc:
        raise RuntimeError('Falha de conexão com Google Maps API.') from exc

def query_google(lat, lon, key, radius=1000, categories=None):
    if not key:
        raise ValueError('Configure GOOGLE_MAPS_API_KEY nos Secrets do Streamlit.')
    if not 100 <= radius <= 5000:
        raise ValueError('Raio deve estar entre 100 e 5.000 metros.')
    categories = categories or list(CATEGORIES)
    output, seen = [], set()
    for cat in categories:
        if cat not in CATEGORIES:
            continue
        payload = {'includedTypes': CATEGORIES[cat], 'maxResultCount': 20,
                   'locationRestriction': {'circle': {'center': {'latitude': lat, 'longitude': lon}, 'radius': float(radius)}},
                   'rankPreference': 'DISTANCE', 'languageCode': 'pt-BR'}
        data = _post('https://places.googleapis.com/v1/places:searchNearby', payload, key,
                     'places.id,places.displayName,places.location,places.formattedAddress,places.googleMapsUri,places.primaryType')
        for p in data.get('places', []):
            pid = p.get('id')
            loc = p.get('location', {})
            a, b = loc.get('latitude'), loc.get('longitude')
            if not pid or a is None or b is None or pid in seen:
                continue
            d = haversine(lat, lon, a, b)
            if d > radius:
                continue
            seen.add(pid)
            output.append({'incluir': False, 'categoria': cat, 'nome': p.get('displayName', {}).get('text', 'Sem nome'),
                'distância_reta_m': d, 'distância_vias_m': None, 'latitude': a, 'longitude': b,
                'fonte': p.get('googleMapsUri') or f'https://www.google.com/maps/place/?q=place_id:{pid}',
                'confiança': 'Cadastro Google Places; não comprova funcionamento ou natureza pública',
                'observação': f"{p.get('formattedAddress','')} | Tipo: {p.get('primaryType','não informado')}. Confirmar funcionamento, titularidade e acesso.",
                'texto_editado': ''})
    return sorted(output, key=lambda x: x['distância_reta_m'])

def road_distance(lat, lon, lat2, lon2, key, timeout=20):
    payload = {'origin': {'location': {'latLng': {'latitude': lat, 'longitude': lon}}},
               'destination': {'location': {'latLng': {'latitude': lat2, 'longitude': lon2}}},
               'travelMode': 'DRIVE', 'routingPreference': 'TRAFFIC_UNAWARE', 'languageCode': 'pt-BR'}
    data = _post('https://routes.googleapis.com/directions/v2:computeRoutes', payload, key,
                 'routes.distanceMeters', timeout=timeout)
    routes = data.get('routes', [])
    return round(routes[0]['distanceMeters']) if routes else None

def street_context(lat, lon):
    return {'logradouro': 'Não verificado automaticamente', 'pavimentação': 'Não verificada',
            'fonte': '', 'observação': 'Google Places não comprova pavimentação, drenagem, esgoto ou esquina mais próxima. Confirmar em vistoria ou cadastro oficial.'}
