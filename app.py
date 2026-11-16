import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geo import resolve_input, query_google, road_distance, street_context, CATEGORIES
from exporter import build_docx

st.set_page_config(page_title='PTAM GEO v2.0', page_icon='📍', layout='wide')
st.title('PTAM GEO | Considerandos para avaliação mercadológica')
st.caption('Versão 2.0 • Google Places e Routes • Revisão humana obrigatória • Word editável')
st.warning('Os cadastros são indicativos. Não declare pavimentação, redes públicas, funcionamento de serviços, natureza pública de instituições ou esquina mais próxima sem confirmação.')
try:
    api_key = st.secrets.get('GOOGLE_MAPS_API_KEY', '')
except Exception:
    api_key = ''
if not api_key:
    st.error('Chave Google Maps não configurada. Adicione GOOGLE_MAPS_API_KEY aos Secrets do aplicativo no Streamlit Cloud. Não cole a chave no GitHub.')

with st.sidebar:
    st.header('Configurações')
    radius = st.number_input('Raio de pesquisa (metros)', min_value=100, max_value=5000, value=1000, step=100)
    categories = st.multiselect('Categorias', list(CATEGORIES), default=list(CATEGORIES))
    routing = st.checkbox('Permitir cálculo de distância viária (Google Routes)', value=True)
    st.caption('Cada categoria consulta Google Places. Cada rota selecionada gera uma requisição adicional faturável.')

link = st.text_input('Link Google Maps ou coordenadas (latitude, longitude)', placeholder='https://www.google.com/maps/... ou -8.28, -35.97')
address = st.text_input('Identificação do imóvel (opcional)', placeholder='Rua, número, bairro, cidade e UF')

if st.button('Pesquisar localização e estabelecimentos', type='primary', disabled=not bool(api_key)):
    try:
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
    cols=['incluir','categoria','nome','distância_reta_m','distância_vias_m','latitude','longitude','fonte','confiança','observação','texto_editado']
    df=pd.DataFrame(st.session_state.rows)
    if df.empty:
        df=pd.DataFrame(columns=cols)
        st.info('Nenhum registro encontrado. Isso não significa ausência de serviços na região.')
    st.subheader('Seleção e conferência')
    st.caption('Selecione os registros e revise os dados. A pesquisa limita a 20 resultados por categoria; não é levantamento exaustivo.')
    edited=st.data_editor(df[cols], num_rows='dynamic', use_container_width=True, hide_index=True,
        column_config={'latitude':None,'longitude':None,'fonte':st.column_config.LinkColumn('Fonte'),
            'incluir':st.column_config.CheckboxColumn('Incluir'),
            'distância_reta_m':st.column_config.NumberColumn('Linha reta (m)'),
            'distância_vias_m':st.column_config.NumberColumn('Via (m)'),
            'texto_editado':st.column_config.TextColumn('Considerando revisado',width='large')}, key='editor_v2')
    if st.button('Calcular distâncias viárias dos selecionados', disabled=not routing):
        updated=edited.to_dict('records')
        selected=[r for r in updated if r.get('incluir')]
        if len(selected)>15:
            st.warning('Selecione até 15 registros para controlar custos e evitar consultas excessivas.')
        elif not selected:
            st.warning('Selecione pelo menos um registro.')
        else:
            with st.spinner('Calculando percursos pelo Google Routes...'):
                failures=0
                for r in updated:
                    if r.get('incluir') and pd.notna(r.get('latitude')) and pd.notna(r.get('longitude')):
                        try:
                            r['distância_vias_m']=road_distance(lat,lon,float(r['latitude']),float(r['longitude']),api_key)
                        except Exception:
                            failures+=1
                            r['distância_vias_m']=None
            st.session_state.rows=updated
            if failures:st.warning(f'{failures} percurso(s) indisponível(is). Não foram inventadas distâncias.')
            st.rerun()
    st.subheader('Complementos e validação profissional')
    notes=st.text_area('Considerandos adicionais confirmados pelo avaliador', height=130,
                       placeholder='Descreva apenas características verificadas, com indicação da fonte ou vistoria.')
    verified=st.checkbox('Conferi os registros, as distâncias, as fontes e o texto. Autorizo a exportação após revisão humana.', value=False)
    if verified:
        selected=edited.to_dict('records')
        for r in selected:
            for k in ('distância_reta_m','distância_vias_m'):
                if pd.isna(r.get(k)):r[k]=None
            if pd.isna(r.get('texto_editado')):r['texto_editado']=''
        if not any(r.get('incluir') for r in selected) and not notes.strip():
            st.warning('Selecione registros ou informe considerandos confirmados.')
        else:
            content=build_docx(address or st.session_state.query_address,lat,lon,selected,road,notes,
                method='Linha reta geodésica e, quando disponível, percurso viário pelo Google Routes (modo automóvel)')
            st.download_button('Exportar considerandos em Word (.docx)',content,'PTAM_GEO_Considerandos.docx',
                mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document')

with st.expander('Integrações, privacidade e custos'):
    st.markdown('''**Google Places API (New):** requer chave de API, faturamento habilitado e cobra conforme requisições e campos solicitados. **Google Routes API:** requer chave e faturamento; cada percurso pode gerar cobrança. **Distância em linha reta:** calculada localmente, sem cobrança adicional. **Google Earth:** não integrado; não se afirma que a distância foi medida nele. **Pavimentação, esgoto, iluminação, esquina mais próxima e natureza pública dos serviços:** exigem vistoria ou cadastro oficial. **Exportação Word:** sem tarifa por documento nesta implementação. **Segurança:** a chave deve ficar nos Secrets do Streamlit, nunca no código ou no GitHub. A hospedagem pública não possui login próprio; não insira dados pessoais confidenciais. As coordenadas são transmitidas às APIs do Google. Consulte os termos e preços vigentes no Google Maps Platform.''')
