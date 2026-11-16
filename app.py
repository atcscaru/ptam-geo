import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geo import resolve_input,query_osm,road_distance,street_context
from exporter import build_docx

st.set_page_config(page_title='PTAM GEO',page_icon='📍',layout='wide')
st.title('PTAM GEO | Considerandos para avaliação mercadológica')
st.caption('Versão 1.0 • Pesquisa OSM rastreável • Revisão humana obrigatória • Word editável')
st.warning('Dados cartográficos são indicativos. Não declare pavimentação, redes públicas, funcionamento de serviços ou esquina mais próxima como fatos sem confirmação.')

with st.sidebar:
    st.header('Configurações')
    radius=st.number_input('Raio de pesquisa (metros)',min_value=100,max_value=5000,value=1000,step=100)
    categories=st.multiselect('Categorias', ['Educação pública','Saúde','Órgãos públicos','Comércio e serviços','Mobilidade'],default=['Educação pública','Saúde','Órgãos públicos','Comércio e serviços','Mobilidade'])
    routing=st.checkbox('Calcular também distância viária (OSRM)',value=True)
    st.caption('Roteamento em lote usa serviço público de demonstração e pode ser limitado. Se indisponível, a distância viária fica sem valor.')

link=st.text_input('Link Google Maps ou coordenadas (latitude, longitude)',placeholder='https://www.google.com/maps/... ou -8.2856200, -35.9738400')
address=st.text_input('Identificação do imóvel (opcional)',placeholder='Rua, número, bairro, cidade e UF')

if st.button('Pesquisar localização e estabelecimentos',type='primary'):
    try:
        with st.spinner('Consultando bases geográficas...'):
            lat,lon=resolve_input(link)
            rows=query_osm(lat,lon,radius)
            rows=[x for x in rows if x['categoria'] in categories]
            try: road=street_context(lat,lon)
            except Exception:road={'logradouro':'Não identificado','pavimentação':'Não verificada','fonte':'','observação':'Consulta de via indisponível'}
            st.session_state.update(rows=rows,road=road,lat=lat,lon=lon,reviewed=False)
    except Exception as exc:st.error(f'Pesquisa não concluída: {exc}. Verifique o link, conexão e disponibilidade da fonte. Nenhum resultado foi inventado.')

if 'rows' in st.session_state:
    lat=st.session_state.lat;lon=st.session_state.lon;road=st.session_state.road
    st.subheader('Resultado da pesquisa')
    st.write(f'Coordenadas: **{lat:.7f}, {lon:.7f}** | {len(st.session_state.rows)} registros localizados')
    st.info(f'Via cartográfica próxima: {road.get("logradouro","Não identificada")} | Pavimentação cadastrada: {road.get("pavimentação","Não informada")}. {road.get("observação","")}')
    m=folium.Map(location=[lat,lon],zoom_start=15)
    folium.Marker([lat,lon],tooltip='Imóvel avaliando',icon=folium.Icon(color='red')).add_to(m)
    folium.Circle([lat,lon],radius=radius,fill=False,color='blue').add_to(m)
    for r in st.session_state.rows[:150]:folium.CircleMarker([r['latitude'],r['longitude']],radius=3,tooltip=r['nome'],color='green').add_to(m)
    st_folium(m,width=None,height=380,returned_objects=[])
    st.subheader('Seleção e revisão dos registros')
    st.caption('Marque “incluir” para cada local. Edite o texto final, se necessário. Links na coluna fonte permitem auditoria. Não existe confirmação automática de funcionamento.')
    cols=['incluir','categoria','nome','distância_reta_m','distância_vias_m','latitude','longitude','fonte','confiança','observação','texto_editado']
    if not st.session_state.rows:
        st.info('Nenhum registro encontrado. É possível adicionar registros manualmente com fonte verificável.')
    df=pd.DataFrame(st.session_state.rows)
    if df.empty:df=pd.DataFrame(columns=cols)
    edited=st.data_editor(df[cols],num_rows='dynamic',use_container_width=True,hide_index=True,
        column_config={'latitude':None,'longitude':None,'incluir':st.column_config.CheckboxColumn('Incluir'), 'fonte':st.column_config.LinkColumn('Fonte'),
        'distância_reta_m':st.column_config.NumberColumn('Linha reta (m)',format='%d'),
        'distância_vias_m':st.column_config.NumberColumn('Via (m)',format='%d'),
        'texto_editado':st.column_config.TextColumn('Considerando revisado',width='large')},key='editor')
    st.caption('Para adicionar um registro manual, preencha nome, categoria, distância, fonte e observação. Verifique a procedência.')
    if st.button('Calcular rotas dos registros selecionados'):
        if not routing:st.warning('Ative o roteamento na barra lateral.')
        else:
            updated=edited.to_dict('records'); selected=[r for r in updated if r.get('incluir')]
            if len(selected)>15:st.warning('Selecione até 15 registros por consulta para não sobrecarregar o serviço público de demonstração.')
            else:
                with st.spinner('Calculando percursos...'):
                    for r in updated:
                        if r.get('incluir') and pd.notna(r.get('latitude')) and pd.notna(r.get('longitude')):
                            r['distância_vias_m']=road_distance(lat,lon,float(r['latitude']),float(r['longitude']))
                st.session_state.rows=updated;st.rerun()
    st.subheader('Vistoria e informações adicionais')
    notes=st.text_area('Considerandos adicionais confirmados pelo avaliador',height=120,placeholder='Considerando que... (informe apenas fatos comprovados)')
    verified=st.checkbox('Revisei os registros selecionados, conferi as fontes e assumo a responsabilidade técnica pelo conteúdo.',value=False)
    st.caption('A exportação permanece bloqueada até a confirmação explícita.')
    if verified:
        selected=edited.to_dict('records')
        for r in selected:
            for k in ('distância_reta_m','distância_vias_m'):
                if pd.isna(r.get(k)):r[k]=None
        if not any(r.get('incluir') for r in selected) and not notes.strip():st.warning('Selecione pelo menos um registro ou acrescente considerandos verificados.')
        else:
            content=build_docx(address,lat,lon,selected,road,notes)
            st.download_button('Exportar considerandos em Word (.docx)',data=content,file_name='PTAM_GEO_Considerandos.docx',mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document')

with st.expander('Integrações, fontes e custos'):
    st.markdown('''**OpenStreetMap / Overpass:** sem chave nesta versão; dados colaborativos. Servidores públicos possuem limites, não garantem disponibilidade e não são indicados para produção intensiva. **OSRM público:** sem chave, serviço de demonstração, limitado; produção requer servidor próprio ou provedor pago. **Google Maps Places/Routes/Geocoding:** não integrados nesta versão; exigem projeto Google Cloud, chave de API, faturamento habilitado e cobrança por uso conforme a tabela vigente. **Google Earth:** sem integração automática de medição nesta versão; não se afirma que as distâncias foram medidas nele. **Exportação Word:** local, sem chave e sem cobrança por documento. **Hospedagem:** pode ter custo conforme provedor. **Cadastros oficiais:** integração futura condicionada à disponibilidade de APIs/dados municipais, estaduais e federais.\n\nOs dados enviados aos serviços de mapas incluem coordenadas geográficas; evite inserir dados pessoais sensíveis.''')
