import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from geo import resolve_input, query_google, road_distance, street_context, CATEGORIES, places_request_count
from exporter import build_docx
from infrastructure import FIELDS, build_infrastructure_considerando
from geo import haversine

st.set_page_config(page_title='PTAM GEO v2.8', page_icon='📍', layout='wide')

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
st.caption('Versão 2.8 • Acesso Google restrito • Pesquisa automática ou manual • Percurso a pé por logradouros • Word editável')
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
    routing = st.checkbox('Permitir cálculo de percurso a pé (Google Routes)', value=True)
    st.caption('Cada categoria gera consulta Places; Saúde e centros de compras também fazem buscas complementares por nome. Cada rota gera outra requisição faturável.')
    st.metric('Places nesta sessão', f"{st.session_state.api_usage['places']}/{SESSION_PLACES_CAP}")
    st.metric('Routes nesta sessão', f"{st.session_state.api_usage['routes']}/{SESSION_ROUTES_CAP}")
    st.warning('Limites acima valem apenas para esta sessão. Reiniciar o aplicativo ou abrir outra sessão zera os contadores. Para limite efetivo, configure cotas no Google Cloud.')

mode = st.radio('Modo de levantamento', ['Pesquisa automática pelo Google Maps', 'Cadastro manual sem localização eletrônica'], horizontal=True)
manual_mode = mode.startswith('Cadastro manual')
if st.session_state.get('last_mode') != mode:
    st.session_state.last_mode = mode
    for k in ('rows','road','lat','lon','query_radius','query_address','manual_initialized'):
        st.session_state.pop(k,None)
    st.session_state.editor_revision=st.session_state.get('editor_revision',0)+1
link = st.text_input('Link Google Maps ou coordenadas (latitude, longitude)', placeholder='https://www.google.com/maps/... ou -8.28, -35.97')
address = st.text_input('Identificação do imóvel (opcional)', placeholder='Rua, número, bairro, cidade e UF')

if not manual_mode and st.button('Pesquisar localização e estabelecimentos', type='primary', disabled=not bool(api_key)):
    try:
        expected = places_request_count(categories)
        if expected == 0:
            raise ValueError('Selecione ao menos uma categoria.')
        if st.session_state.api_usage['places'] + expected > SESSION_PLACES_CAP:
            raise ValueError('Limite preventivo de consultas Places nesta sessão atingido. Verifique as cotas do Google Cloud antes de continuar.')
        # Reserva antecipada: falhas e resultados vazios também podem ser faturáveis.
        st.session_state.api_usage['places'] += expected
        lat, lon = resolve_input(link)
        with st.spinner('Consultando Google Places...'):
            rows = query_google(lat, lon, api_key, radius, categories)
        st.session_state.update(rows=rows, road=street_context(lat, lon), lat=lat, lon=lon, query_radius=radius, query_address=address, editor_revision=st.session_state.get('editor_revision',0)+1)
        st.success(f'Pesquisa concluída: {len(rows)} registros. Confira as informações antes de utilizar no PTAM.')
    except Exception as exc:
        st.error(f'Pesquisa não concluída: {exc}. Nenhum resultado foi inventado.')

if manual_mode and ('rows' not in st.session_state or not st.session_state.get('manual_initialized')):
    st.session_state.update(rows=[], road={'logradouro':'Não verificado automaticamente','pavimentação':'Não verificada','fonte':'','observação':'Levantamento manual: informações e distâncias dependem de verificação profissional.'}, lat=None, lon=None, query_radius=radius, query_address=address, manual_initialized=True, editor_revision=st.session_state.get('editor_revision',0)+1)
if not manual_mode:
    st.session_state.manual_initialized=False

if 'rows' in st.session_state:
    lat, lon = st.session_state.lat, st.session_state.lon
    road = st.session_state.road
    st.subheader('Resultados e conferência')
    if manual_mode:
        st.info('Modo manual: cadastre os pontos relevantes e suas distâncias aproximadas por percurso a pé em logradouros públicos. Nenhuma consulta ao Google Maps é feita neste modo.')
    else:
        st.write(f'Coordenadas: **{lat:.7f}, {lon:.7f}** | **{len(st.session_state.rows)}** registros')
        st.info(road['observação'])
        m = folium.Map(location=[lat, lon], zoom_start=15)
        folium.Marker([lat,lon], tooltip='Imóvel avaliando', icon=folium.Icon(color='red')).add_to(m)
        folium.Circle([lat,lon], radius=st.session_state.query_radius, fill=False).add_to(m)
        for r in st.session_state.rows:
            if pd.notna(r.get('latitude')) and pd.notna(r.get('longitude')):
                folium.CircleMarker([r['latitude'],r['longitude']], radius=3, tooltip=r['nome']).add_to(m)
        st_folium(m, height=360, returned_objects=[])
        with st.expander('Ajustar localização (somente em casos excepcionais)', expanded=False):
            st.caption('Use apenas quando o Google posicionar incorretamente o imóvel ou a entrada do estabelecimento. Alterar coordenadas exige novo cálculo da rota correspondente.')
            origin_lat = st.number_input('Latitude do acesso ao imóvel', min_value=-90.0, max_value=90.0, value=float(lat), format='%.7f', key='origin_lat')
            origin_lon = st.number_input('Longitude do acesso ao imóvel', min_value=-180.0, max_value=180.0, value=float(lon), format='%.7f', key='origin_lon')
            st.caption('As coordenadas dos estabelecimentos podem ser corrigidas na tabela quando necessário.')
    st.subheader('Seleção e conferência dos estabelecimentos')
    if st.session_state.pop('table_saved_notice',False):
        st.success('Alterações salvas nesta sessão. Distâncias corrigidas foram protegidas contra novos cálculos.')
    st.info('Fluxo: selecione os locais, calcule os percursos a pé em lote, confira os resultados, corrija apenas as distâncias necessárias e clique em Salvar e proteger correções.')
    st.warning('Critério PTAM GEO: menor percurso a pé exclusivamente por ruas, avenidas, travessas e outros logradouros públicos regulares indicados no mapa. Exclua becos, vielas, atalhos por terrenos e travessias não oficiais de cursos d’água. O Google Routes NÃO garante esse filtro. Confira cada trajeto e marque a coluna de validação somente após verificar; se necessário, corrija manualmente a distância e indique a fonte.')
    st.caption('É possível acrescentar estabelecimentos manualmente, inclusive os não cadastrados no Google. Informe a fonte e a natureza da medição.')
    if st.button('Adicionar estabelecimento manualmente'):
        st.session_state.rows.append({'incluir':True,'categoria':'Outros','nome':'','natureza_cemiterio':'Não verificada',
            'distância_reta_m':None,'distância_vias_m':None,'latitude':None,'longitude':None,
            'fonte':'','confiança':'Informação manual; sujeita a conferência', 'observação':'', 'texto_editado':'',
            'origem_distancia':'Medição manual do avaliador','distancia_confirmada':False,'trajeto_validado':False})
        st.session_state.editor_revision=st.session_state.get('editor_revision',0)+1
        st.rerun()
    cols=['incluir','categoria','nome','natureza_cemiterio','distância_vias_m','origem_distancia','distancia_confirmada','trajeto_validado','latitude','longitude','fonte','observação','texto_editado']
    df=pd.DataFrame(st.session_state.rows)
    for c in cols:
        if c not in df.columns:
            df[c]=False if c in ('incluir','distancia_confirmada','trajeto_validado') else None
    with st.expander('Tabela de estabelecimentos e distâncias', expanded=True):
        edited=st.data_editor(df[cols],num_rows='fixed',use_container_width=True,hide_index=True,
        column_config={
            'incluir':st.column_config.CheckboxColumn('Incluir'),
            'categoria':st.column_config.TextColumn('Categoria'),
            'nome':st.column_config.TextColumn('Estabelecimento / ponto relevante',required=True),
            'natureza_cemiterio':st.column_config.SelectboxColumn('Natureza do cemitério',options=['Não verificada','Público','Privado']),
            'distância_vias_m':st.column_config.NumberColumn('Percurso a pé conferido (m)',min_value=0.0,step=1.0),
            'origem_distancia':st.column_config.SelectboxColumn('Fonte da distância',options=['Google Routes','Google Earth','Medição manual do avaliador','Outra fonte verificada','Não verificada']),
            'distancia_confirmada':st.column_config.CheckboxColumn('Preservar distância conferida'),
            'trajeto_validado':st.column_config.CheckboxColumn('Trajeto por logradouros conferido'),
            'latitude':st.column_config.NumberColumn('Latitude destino',format='%.7f'),
            'longitude':st.column_config.NumberColumn('Longitude destino',format='%.7f'),
            'fonte':st.column_config.TextColumn('Fonte / referência documental'),
            'observação':st.column_config.TextColumn('Observação / acesso'),
            'texto_editado':st.column_config.TextColumn('Considerando personalizado (opcional)',width='large'),
        },key=f"editor_{st.session_state.get('editor_revision',0)}")
    # Marcar como manual somente distâncias efetivamente alteradas pelo avaliador.
    def protect_manual_changes(records, baseline):
        for i, row in enumerate(records):
            old = baseline[i] if i < len(baseline) else {}
            new_distance = row.get('distância_vias_m')
            old_distance = old.get('distância_vias_m')
            new_num = None if pd.isna(new_distance) else float(new_distance)
            old_num = None if pd.isna(old_distance) else float(old_distance)
            if new_num != old_num and new_num is not None:
                if row.get('origem_distancia') in (None, '', 'Google Routes', 'Não verificada'):
                    row['origem_distancia'] = 'Medição manual do avaliador'
                row['distancia_confirmada'] = True
            # Corrigir coordenadas invalida rota automática anterior, mas não a distância manual protegida.
            if old and any((None if pd.isna(row.get(k)) else row.get(k)) != (None if pd.isna(old.get(k)) else old.get(k)) for k in ('latitude','longitude')):
                if not row.get('distancia_confirmada'):
                    row['distância_vias_m'] = None
                    row['trajeto_validado'] = False
        return records

    if not manual_mode:
        st.subheader('Cálculo automático em lote')
        if (origin_lat,origin_lon)!=(lat,lon):
            st.warning('O acesso do imóvel foi ajustado. Clique em Atualizar origem (excepcional) antes de calcular percursos.')
        with st.expander('Atualizar origem ou coordenadas corrigidas (excepcional)', expanded=False):
            if st.button('Atualizar origem e coordenadas corrigidas'):
                updated=protect_manual_changes(edited.to_dict('records'),st.session_state.rows)
                changed=(origin_lat,origin_lon)!=(lat,lon)
                for r in updated:
                    if changed and not r.get('distancia_confirmada'):
                        r['distância_vias_m']=None
                        r['trajeto_validado']=False
                    if pd.notna(r.get('latitude')) and pd.notna(r.get('longitude')):
                        a,b=float(r['latitude']),float(r['longitude'])
                        if not (-90<=a<=90 and -180<=b<=180):
                            st.error('Coordenadas de destino inválidas.');st.stop()
                        r['distância_reta_m']=haversine(origin_lat,origin_lon,a,b)
                st.session_state.rows=updated
                st.session_state.lat,st.session_state.lon=origin_lat,origin_lon
                st.session_state.editor_revision=st.session_state.get('editor_revision',0)+1
                st.rerun()
        if st.button('Calcular percursos a pé dos selecionados',type='primary',disabled=not routing or not bool(api_key)):
            updated=protect_manual_changes(edited.to_dict('records'),st.session_state.rows)
            if (origin_lat,origin_lon)!=(lat,lon):
                st.error('Atualize primeiro a origem corrigida na seção excepcional.');st.stop()
            selected=[r for r in updated if r.get('incluir') and not r.get('distancia_confirmada')]
            eligible=[r for r in selected if pd.notna(r.get('latitude')) and pd.notna(r.get('longitude'))]
            if len(eligible)>10:
                st.warning('Selecione até 10 percursos não protegidos por lote.')
            elif st.session_state.api_usage['routes']+len(eligible)>SESSION_ROUTES_CAP:
                st.warning('Limite preventivo de rotas nesta sessão atingido.')
            elif not eligible:
                st.warning('Nenhum estabelecimento selecionado com coordenadas válidas e distância não protegida.')
            else:
                st.session_state.api_usage['routes']+=len(eligible)
                failures=0
                with st.spinner('Calculando percursos a pé pelo Google Routes...'):
                    for r in eligible:
                        try:
                            r['distância_vias_m']=road_distance(lat,lon,float(r['latitude']),float(r['longitude']),api_key)
                            r['origem_distancia']='Google Routes'
                            r['trajeto_validado']=False
                        except Exception:
                            failures+=1
                            r['distância_vias_m']=None
                            r['trajeto_validado']=False
                st.session_state.rows=updated
                st.session_state.editor_revision=st.session_state.get('editor_revision',0)+1
                if failures:st.warning(f'{failures} percurso(s) indisponível(is).')
                st.rerun()
    else:
        st.caption('No cadastro manual, preencha nome, categoria, distância, fonte e confirme o trajeto. Não são exigidas coordenadas.')
    if st.button('Salvar e proteger correções da tabela'):
        updated=protect_manual_changes(edited.to_dict('records'),st.session_state.rows)
        st.session_state.table_saved_notice=True
        st.session_state.rows=updated
        st.session_state.editor_revision=st.session_state.get('editor_revision',0)+1
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
        if not manual_mode and (origin_lat,origin_lon)!=(lat,lon):
            st.error('Confirme as coordenadas da origem antes de exportar.');st.stop()
        if any(v!='Não verificado' for section in infra.values() for v in section.values()) and not infra_source.strip():
            st.error('Informe a fonte das condições de infraestrutura antes de exportar.');st.stop()
        selected=protect_manual_changes(edited.to_dict('records'),st.session_state.rows)
        for r in selected:
            for k in ('distância_vias_m','distância_reta_m'):
                if pd.isna(r.get(k)):r[k]=None
            for k in ('texto_editado','nome','fonte','observação'):
                if pd.isna(r.get(k)):r[k]=''
        if any(r.get('incluir') and (not str(r.get('nome','')).strip() or r.get('distância_vias_m') is None or not str(r.get('fonte','')).strip()) for r in selected):
            st.error('Cada registro incluído deve ter nome, distância viária e fonte/referência.');st.stop()
        if any(r.get('incluir') and not r.get('trajeto_validado',False) for r in selected):
            st.error('Há registros selecionados sem conferência do percurso por logradouros públicos. Marque “Trajeto por logradouros conferido” somente após verificar o caminho no mapa e corrigir a distância, se necessário.');st.stop()
        if any(r.get('incluir') and str(r.get('texto_editado') or '').strip() for r in selected):
            st.info('Há considerandos personalizados. Confira se as distâncias escritas nesses textos correspondem às distâncias finais da tabela.')
        if not any(r.get('incluir') for r in selected) and not notes.strip() and not infra_text:
            st.warning('Selecione registros ou informe considerandos confirmados.')
        else:
            content=build_docx(address or st.session_state.query_address,lat,lon,selected,road,notes,infra_text=infra_text,
                method='Menor percurso a pé verificado pelo avaliador, exclusivamente por logradouros públicos regulares indicados no mapa; sem becos, vielas, atalhos por terrenos particulares ou travessias não oficiais de cursos d’água; fonte individual indicada por registro')
            st.download_button('Exportar considerandos em Word (.docx)',content,'PTAM_GEO_Considerandos.docx',
                mime='application/vnd.openxmlformats-officedocument.wordprocessingml.document')

with st.expander('Integrações, privacidade e custos'):
    st.markdown('''**Controle de custos:** até 20 consultas Places e 30 Routes por sessão. Esses limites não são globais, não persistem e não impedem cobranças de outras sessões. Use cotas e monitoramento no Google Cloud. **Google Places API (New):** requer chave de API, faturamento habilitado e cobra conforme requisições e campos solicitados. **Google Routes API (modo WALK):** requer chave e faturamento; cada percurso pode gerar cobrança. O modo WALK pode sugerir atalhos, becos e passagens que não atendem ao critério adotado; o avaliador deve conferir e corrigir antes da exportação. **Distância em linha reta:** calculada localmente, sem cobrança adicional. **Google Earth:** não integrado; não se afirma que a distância foi medida nele. **Pavimentação, esgoto, iluminação, esquina mais próxima e natureza pública dos serviços:** exigem vistoria ou cadastro oficial. **Exportação Word:** sem tarifa por documento nesta implementação. **Segurança:** a chave deve ficar nos Secrets do Streamlit, nunca no código ou no GitHub. O acesso é protegido por login Google autorizado; evite dados pessoais desnecessários. As coordenadas são transmitidas às APIs do Google. Consulte os termos e preços vigentes no Google Maps Platform.''')
