import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geo import resolve_input, query_google, road_distance, street_context, CATEGORIES
from exporter import build_docx
from infrastructure import FIELDS, build_infrastructure_considerando
from geo import haversine

st.set_page_config(page_title='PTAM GEO v2.4', page_icon='📍', layout='wide')

# Autenticação obrigatória antes de qualquer consulta, dado do imóvel ou mapa.
# Configure [auth] e ALLOWED_GOOGLE_EMAIL em Streamlit Cloud > Settings > Secrets.
try:
    allowed_email = str(st.secrets.get('ALLOWED_GOOGLE_EMAIL', '')).strip().casefold()
except Exception:
    allowed_email = ''

if not allowed_email:
    st.error('Acesso bloqueado: configure ALLOWED_GOOGLE_EMAIL nos Secrets do Streamlit.')
    st.stop()

if not st.user.is_logged_in:
    st.title('PTAM GEO | Acesso restrito')
    st.write('Entre com a conta Google autorizada para utilizar o aplicativo.')
    if st.button('Entrar com Google', type='primary'):
        st.login('google')
    st.stop()

current_email = str(st.user.get('email', '')).strip().casefold()
email_verified = st.user.get('email_verified', False)
if current_email != allowed_email or email_verified is not True:
    st.error('Esta conta Google não está autorizada a utilizar o PTAM GEO.')
    if st.button('Sair da conta Google'):
        st.logout()
    st.stop()

with st.sidebar:
    st.caption('Acesso autorizado')
    if st.button('Sair', key='logout'):
        st.logout()

st.title('PTAM GEO | Considerandos para avaliação mercadológica')
st.caption('Versão 2.4 • Acesso Google restrito • Google Places e Routes • Revisão humana obrigatória • Word editável')
st.warning('Os cadastros são indicativos. Não declare pavimentação, redes públicas, funcionamento de serviços, natureza pública de instituições ou esquina mais próxima sem confirmação.')
try:
    api_key = st.secrets.get('GOOGLE_MAPS_API_KEY', '')
except Exception:
    api_key = ''
if not api_key:
    st.error('Chave Google Maps não configurada. Adicione GOOGLE_MAPS_API_KEY aos Secrets do aplicativo no Streamlit Cloud. Não cole a chave no GitHub.')

# Contador preventivo por sessão: NÃO é limite mensal global nem bloqueio de cobrança.
if 'api_usage' not in st.session_state:
    st.session_state.api_usage = {'places': 0, 'routes': 0}
SESSION_PLACES_CAP = 20
SESSION_ROUTES_CAP = 30

with st.sidebar:
    st.header('Configurações')
    radius = st.number_input('Raio de pesquisa (metros)', min_value=100, max_value=5000, value=1000, step=100)
    categories = st.multiselect('Categorias', list(CATEGORIES), default=list(CATEGORIES))
    routing = st.checkbox('Permitir cálculo de distância viária (Google Routes)', value=True)
    st.caption('Cada categoria consulta Google Places. Cada rota selecionada gera uma requisição adicional faturável.')
    st.metric('Places nesta sessão', f"{st.session_state.api_usage['places']}/{SESSION_PLACES_CAP}")
    st.metric('Routes nesta sessão', f"{st.session_state.api_usage['routes']}/{SESSION_ROUTES_CAP}")
    st.warning('Limites acima valem apenas para esta sessão. Reiniciar o aplicativo ou abrir outra sessão zera os contadores. Para limite efetivo, configure cotas no Google Cloud.')

link = st.text_input('Link Google Maps ou coordenadas (latitude, longitude)', placeholder='https://www.google.com/maps/... ou -8.28, -35.97')
address = st.text_input('Identificação do imóvel (opcional)', placeholder='Rua, número, bairro, cidade e UF')

if st.button('Pesquisar localização e estabelecimentos', type='primary', disabled=not bool(api_key)):
    try:
        expected = len([c for c in categories if c in CATEGORIES])
        if expected == 0:
            raise ValueError('Selecione ao menos uma categoria.')
        if st.session_state.api_usage['places'] + expected > SESSION_PLACES_CAP:
            raise ValueError('Limite preventivo de consultas Places nesta sessão atingido. Verifique as cotas do Google Cloud antes de continuar.')
        # Reserva antecipada: falhas e resultados vazios também podem ser faturáveis.
        st.session_state.api_usage['places'] += expected
        lat, lon = resolve_input(link)
        with st.spinner('Consultando Google Places...'):
            rows = query_google(lat, lon, api_key, radius, categories)
        st.session_state.update(rows=rows, road=street_context(lat, lon), lat=lat, lon=lon, query_radius=radius, query_address=address)
        st.success(f'Pesquisa concluída: {len(rows)} registros. Confira as informações antes de utilizar no PTAM.')
    except Exception as exc:
        st.error(f'Pesquisa não concluída: {exc}. Nenhum resultado foi inventado.')

if 'rows' in st.session_state:
    lat, lon = st.session_state.lat, st.session_state.lon
    road = st.session_state.road
    st.subheader('Resultados e mapa')
    st.write(f'Coordenadas: **{lat:.7f}, {lon:.7f}** | **{len(st.session_state.rows)}** registros')
    st.info(road['observação'])
    m = folium.Map(location=[lat, lon], zoom_start=15)
    folium.Marker([lat,lon], tooltip='Imóvel avaliando', icon=folium.Icon(color='red')).add_to(m)
    folium.Circle([lat,lon], radius=st.session_state.query_radius, fill=False).add_to(m)
    for r in st.session_state.rows:
        folium.CircleMarker([r['latitude'],r['longitude']], radius=3, tooltip=r['nome']).add_to(m)
    st_folium(m, height=360, returned_objects=[])
    cols=['incluir','categoria','nome','natureza_cemiterio','distância_reta_m','distância_vias_m','latitude','longitude','fonte','confiança','observação','texto_editado']
    df=pd.DataFrame(st.session_state.rows)
    if df.empty:
        df=pd.DataFrame(columns=cols)
        st.info('Nenhum registro encontrado. Isso não significa ausência de serviços na região.')
    st.subheader('Conferência do ponto do imóvel')
    st.caption('Confirme o ponto exato do imóvel. Um link do Google Maps pode conter o centro do mapa, e não a posição do imóvel.')
    origin_lat = st.number_input('Latitude confirmada do imóvel', min_value=-90.0, max_value=90.0, value=float(lat), format='%.7f', key='origin_lat')
    origin_lon = st.number_input('Longitude confirmada do imóvel', min_value=-180.0, max_value=180.0, value=float(lon), format='%.7f', key='origin_lon')
    st.info('As coordenadas de cada estabelecimento estão disponíveis para edição na tabela. Ajuste-as para o ponto verificado, preferencialmente a entrada principal. O Google Places pode indicar apenas o centro do estabelecimento.')
    st.subheader('Seleção e conferência')
    st.caption('Selecione os registros e revise os dados. A pesquisa limita a 20 resultados por categoria; não é levantamento exaustivo. Cemitérios são pesquisados dentro do raio configurado; a natureza pública ou privada deve ser confirmada por fonte independente.')
    edited=st.data_editor(df[cols], num_rows='dynamic', use_container_width=True, hide_index=True,
        column_config={'latitude':st.column_config.NumberColumn('Latitude do destino',format='%.7f'), 'longitude':st.column_config.NumberColumn('Longitude do destino',format='%.7f'),'fonte':st.column_config.LinkColumn('Fonte'),
            'incluir':st.column_config.CheckboxColumn('Incluir'),
            'natureza_cemiterio':st.column_config.SelectboxColumn('Natureza do cemitério (confirmada)',options=['Não verificada','Público','Privado']),
            'distância_reta_m':st.column_config.NumberColumn('Linha reta (m)'),
            'distância_vias_m':st.column_config.NumberColumn('Via (m)'),
            'texto_editado':st.column_config.TextColumn('Considerando revisado',width='large')}, key='editor_v2')
    if st.button('Recalcular linhas retas com coordenadas conferidas'):
        updated=edited.to_dict('records')
        for r in updated:
            if pd.notna(r.get('latitude')) and pd.notna(r.get('longitude')):
                a,b=float(r['latitude']),float(r['longitude'])
                if not (-90<=a<=90 and -180<=b<=180):
                    st.error('Coordenadas de destino inválidas.');st.stop()
                r['distância_reta_m']=haversine(origin_lat,origin_lon,a,b)
                r['distância_vias_m']=None  # não conservar rota de pontos antigos
        st.session_state.rows=updated
        st.session_state.lat,st.session_state.lon=origin_lat,origin_lon
        st.rerun()
    if (origin_lat,origin_lon)!=(lat,lon):
        st.warning('O ponto do imóvel foi alterado. Recalcule as linhas retas antes de calcular rotas ou exportar.')
    if st.button('Calcular distâncias viárias dos selecionados', disabled=not routing):
        updated=edited.to_dict('records')
        if (origin_lat,origin_lon)!=(lat,lon):
            st.error('Recalcule as linhas retas com a nova origem antes das rotas.');st.stop()
        selected=[r for r in updated if r.get('incluir')]
        for r in selected:
            if pd.notna(r.get('latitude')) and pd.notna(r.get('longitude')):
                expected=haversine(lat,lon,float(r['latitude']),float(r['longitude']))
                if pd.isna(r.get('distância_reta_m')) or abs(float(r['distância_reta_m'])-expected)>1:
                    st.error('Coordenadas alteradas: recalcule primeiro as distâncias em linha reta.');st.stop()
        if len(selected)>10:
            st.warning('Selecione até 10 registros por lote para controlar custos.')
        elif st.session_state.api_usage['routes'] + len(selected) > SESSION_ROUTES_CAP:
            st.warning('Limite preventivo de rotas nesta sessão atingido. Consulte o painel de faturamento do Google Cloud.')
        elif not selected:
            st.warning('Selecione pelo menos um registro.')
        else:
            st.session_state.api_usage['routes'] += len(selected)
            with st.spinner('Calculando percursos pelo Google Routes...'):
                failures=0
                for r in updated:
                    if r.get('incluir') and pd.notna(r.get('latitude')) and pd.notna(r.get('longitude')):
                        try:
                            r['distância_vias_m']=road_distance(origin_lat,origin_lon,float(r['latitude']),float(r['longitude']),api_key)
                        except Exception:
                            failures+=1
                            r['distância_vias_m']=None
            st.session_state.rows=updated
            if failures:st.warning(f'{failures} percurso(s) indisponível(is). Não foram inventadas distâncias.')
            st.rerun()
    st.subheader('Infraestrutura verificada: imóvel e logradouro')
    st.caption('Preenchimento manual. Não verificado não será declarado no considerando. Separe a existência da rede no logradouro da ligação efetiva no imóvel.')
    infra={'logradouro':{},'imovel':{}}
    with st.expander('Informar condições de infraestrutura', expanded=True):
        for field, choices in FIELDS.items():
            a,b=st.columns(2)
            with a:
                infra['logradouro'][field]=st.selectbox(f'{field} | Logradouro',choices,index=len(choices)-1,key='infra_rua_'+field)
            with b:
                infra['imovel'][field]=st.selectbox(f'{field} | Imóvel',choices,index=len(choices)-1,key='infra_imovel_'+field)
        infra_source=st.text_input('Fonte da informação (obrigatória se houver características declaradas)',placeholder='Ex.: vistoria realizada em DD/MM/AAAA; informação fornecida pela concessionária...',key='infra_source')
        try:
            infra_text=build_infrastructure_considerando(infra,infra_source) if infra_source.strip() else ''
        except ValueError:
            infra_text=''
        if infra_text: st.text_area('Considerando único gerado',value=infra_text,height=160,disabled=True)
    st.subheader('Complementos e validação profissional')
    notes=st.text_area('Considerandos adicionais confirmados pelo avaliador', height=130,
                       placeholder='Descreva apenas características verificadas, com indicação da fonte ou vistoria.')
    verified=st.checkbox('Conferi os registros, as distâncias, as fontes e o texto. Autorizo a exportação após revisão humana.', value=False)
    if verified:
        if (origin_lat,origin_lon)!=(lat,lon):
            st.error('Recalcule as distâncias com as coordenadas confirmadas antes de exportar.');st.stop()
        if any(v!='Não verificado' for section in infra.values() for v in section.values()) and not infra_source.strip():
            st.error('Informe a fonte das condições de infraestrutura antes de exportar.');st.stop()
        selected=edited.to_dict('records')
        for row in selected:
            if pd.notna(row.get('latitude')) and pd.notna(row.get('longitude')):
                expected=haversine(lat,lon,float(row['latitude']),float(row['longitude']))
                if row.get('distância_reta_m') is not None and pd.notna(row.get('distância_reta_m')) and abs(float(row['distância_reta_m'])-expected)>1:
                    st.error('A distância em linha reta não corresponde às coordenadas editadas. Clique em Recalcular linhas retas.');st.stop()
        for r in selected:
            for k in ('distância_reta_m','distância_vias_m'):
                if pd.isna(r.get(k)):r[k]=None
            if pd.isna(r.get('texto_editado')):r['texto_editado']=''
        if not any(r.get('incluir') for r in selected) and not notes.strip() and not infra_text:
            st.warning('Selecione registros ou informe considerandos confirmados.')
        else:
            content=build_docx(address or st.session_state.query_address,lat,lon,selected,road,notes,infra_text=infra_text,
                method='Linha reta geodésica e, quando disponível, percurso viário pelo Google Routes (modo automóvel)')
            st.download_button('Exportar considerandos em Word (.docx)',content,'PTAM_GEO_Considerandos.docx',
                mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document')

with st.expander('Integrações, privacidade e custos'):
    st.markdown('''**Controle de custos:** até 20 consultas Places e 30 Routes por sessão. Esses limites não são globais, não persistem e não impedem cobranças de outras sessões. Use cotas e monitoramento no Google Cloud. **Google Places API (New):** requer chave de API, faturamento habilitado e cobra conforme requisições e campos solicitados. **Google Routes API:** requer chave e faturamento; cada percurso pode gerar cobrança. **Distância em linha reta:** calculada localmente, sem cobrança adicional. **Google Earth:** não integrado; não se afirma que a distância foi medida nele. **Pavimentação, esgoto, iluminação, esquina mais próxima e natureza pública dos serviços:** exigem vistoria ou cadastro oficial. **Exportação Word:** sem tarifa por documento nesta implementação. **Segurança:** a chave deve ficar nos Secrets do Streamlit, nunca no código ou no GitHub. A hospedagem pública não possui login próprio; não insira dados pessoais confidenciais. As coordenadas são transmitidas às APIs do Google. Consulte os termos e preços vigentes no Google Maps Platform.''')
