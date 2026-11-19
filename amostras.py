"""Módulo independente de pesquisa assistida de amostras do PTAM GEO."""
import csv
import io
import math
import re
from datetime import date
from urllib.parse import quote_plus, urlparse

import pandas as pd
import streamlit as st
from docx import Document
from docx.shared import Cm, Pt
from geo import resolve_input, haversine

FIELDS = ['incluir','tipo','titulo','preco','area_m2','endereco','latitude','longitude','url','fonte','data_consulta','situacao','quartos','observacoes']
TYPES = ['Terreno','Casa','Apartamento','Comercial','Rural','Outro']
SITUATIONS = ['Anunciado à venda','Negociado (comprovação)','Não confirmado']


def blank():
    return {'incluir':True,'tipo':'Casa','titulo':'','preco':None,'area_m2':None,'endereco':'','latitude':None,'longitude':None,'url':'','fonte':'','data_consulta':date.today().isoformat(),'situacao':'Anunciado à venda','quartos':None,'observacoes':''}


def number(value):
    if value is None or pd.isna(value) or str(value).strip()=='':
        return None
    try:
        v=float(value)
        return v if math.isfinite(v) and v>0 else None
    except (TypeError,ValueError):
        return None


def validated_url(value):
    value=str(value or '').strip()
    if not value:
        return ''
    parsed=urlparse(value)
    if parsed.scheme not in ('http','https') or not parsed.hostname:
        return ''
    return value


def enrich(records, origin, radius_m):
    result=[]
    for r in records:
        d=dict(r)
        lat=number_coordinate(d.get('latitude'),90)
        lon=number_coordinate(d.get('longitude'),180)
        if origin and lat is not None and lon is not None:
            dist=haversine(origin[0],origin[1],lat,lon)
            d['distancia_reta_m']=dist
            d['dentro_raio']='Sim' if dist<=radius_m else 'Não'
        else:
            d['distancia_reta_m']=None
            d['dentro_raio']='Não verificado'
        p=number(d.get('preco'))
        a=number(d.get('area_m2'))
        d['preco_m2']=round(p/a,2) if p and a else None
        result.append(d)
    return result


def number_coordinate(value,limit):
    if value is None or pd.isna(value) or str(value).strip()=='':
        return None
    try:
        n=float(value)
        return n if math.isfinite(n) and -limit<=n<=limit else None
    except (TypeError,ValueError):
        return None


def export_docx(rows,origin_text,radius_m,property_type):
    doc=Document()
    sec=doc.sections[0]
    sec.top_margin=Cm(3);sec.bottom_margin=Cm(2);sec.left_margin=Cm(3);sec.right_margin=Cm(2)
    normal=doc.styles['Normal'];normal.font.name='Arial';normal.font.size=Pt(11)
    doc.add_heading('PTAM GEO | Pesquisa assistida de amostras mercadológicas',0)
    doc.add_paragraph(f'Imóvel avaliando (referência): {origin_text or "Não informado"}')
    doc.add_paragraph(f'Tipo de imóvel: {property_type}. Raio de triagem: {radius_m/1000:g} km (linha reta, quando há coordenadas verificadas).')
    doc.add_paragraph('Pesquisa assistida. Os dados foram cadastrados ou importados e dependem de conferência profissional. A presença em resultados de buscadores não comprova localização dentro do raio, vigência do anúncio ou preço de transação. Preços anunciados não equivalem a preços negociados.')
    for i,r in enumerate(rows,1):
        doc.add_heading(f'Amostra {i}: {r.get("titulo") or "Sem título"}',level=2)
        for label,key in [('Tipo','tipo'),('Situação','situacao'),('Endereço','endereco'),('Fonte','fonte'),('Data da consulta','data_consulta'),('Link','url'),('Observações','observacoes')]:
            doc.add_paragraph(f'{label}: {r.get(key) or "Não informado"}')
        p=number(r.get('preco'));a=number(r.get('area_m2'))
        doc.add_paragraph('Preço informado: '+(f'R$ {p:,.2f}'.replace(',','X').replace('.',',').replace('X','.') if p else 'Não informado'))
        doc.add_paragraph('Área informada: '+(f'{a:.2f} m²' if a else 'Não informada'))
        doc.add_paragraph('Preço unitário: '+(f'R$ {p/a:,.2f}/m²'.replace(',','X').replace('.',',').replace('X','.') if p and a else 'Não calculado'))
        doc.add_paragraph(f'Distância em linha reta: {r.get("distancia_reta_m")} m; dentro do raio: {r.get("dentro_raio")}.')
    doc.add_heading('Ressalvas metodológicas',level=2)
    doc.add_paragraph('O documento é um levantamento preliminar de ofertas e informações fornecidas pelo avaliador. Não constitui, isoladamente, determinação do valor de mercado. A seleção de comparáveis, tratamento de dados, fatores de homogeneização, data-base e fundamentação deverão ser realizados e documentados no PTAM pelo profissional responsável.')
    bio=io.BytesIO();doc.save(bio);return bio.getvalue()


def render():
    st.title('PTAM GEO | Pesquisa de amostras mercadológicas')
    st.caption('Módulo independente • Pesquisa por logradouros • Importação e cadastro • Conferência profissional • Word editável')
    st.info('A pesquisa assistida abre o Google com consultas por logradouro, bairro e cidade. Não há extração automática de anúncios nem acesso a preços negociados. A confirmação do raio depende das coordenadas verificadas de cada amostra.')
    if 'samples_seq' not in st.session_state: st.session_state.samples_seq=0
    seq=st.session_state.samples_seq
    with st.sidebar:
        st.subheader('Amostras mercadológicas')
        if st.button('Nova pesquisa de amostras',key='samples_reset_request'):
            st.session_state.samples_confirm=True
        if st.session_state.get('samples_confirm'):
            st.warning('Exporte os dados antes de limpar a pesquisa.')
            a,b=st.columns(2)
            if a.button('Confirmar',key='samples_reset_confirm'):
                st.session_state.samples_seq+=1
                for k in ('samples_rows','samples_origin','samples_rev','samples_confirm'):
                    st.session_state.pop(k,None)
                st.rerun()
            if b.button('Cancelar',key='samples_reset_cancel'):
                st.session_state.samples_confirm=False;st.rerun()
    left,right=st.columns(2)
    with left:
        reference=st.text_input('Link Google Maps ou coordenadas do imóvel avaliando',key=f'samples_ref_{seq}',placeholder='-8.28, -35.97 ou link Google Maps')
        city=st.text_input('Cidade / bairro para pesquisar anúncios',key=f'samples_city_{seq}',placeholder='Ex.: Maurício de Nassau, Caruaru, PE')
    with right:
        kind=st.selectbox('Tipo de imóvel avaliando',TYPES,key=f'samples_kind_{seq}')
        radius=st.number_input('Raio de triagem (metros)',min_value=100,max_value=20000,value=1000,step=100,key=f'samples_radius_{seq}')
    origin=None
    if reference.strip():
        try:
            origin=resolve_input(reference)
            st.success(f'Origem identificada: {origin[0]:.6f}, {origin[1]:.6f}')
        except Exception as exc:
            st.warning(f'Não foi possível confirmar a origem: {exc}. Você ainda pode pesquisar e cadastrar amostras, mas não será possível conferir o raio automaticamente.')
    st.subheader('1. Encontrar links de anúncios próximos')
    st.info('Pesquisa por logradouro e região no Google, sem API adicional. O Google não oferece filtro circular de 500 m ou 1 km para anúncios: o raio é referência de triagem e não garantia de localização dos resultados.')
    street=st.text_input('Logradouro do imóvel avaliando',key=f'samples_street_{seq}',placeholder='Ex.: Avenida Portugal')
    neighborhood=st.text_input('Bairro do imóvel avaliando',key=f'samples_neighborhood_{seq}',placeholder='Ex.: Universitário')
    municipality=st.text_input('Cidade e UF',key=f'samples_municipality_{seq}',placeholder='Ex.: Caruaru PE')
    nearby=st.text_area('Outros logradouros próximos (opcional; um por linha)',key=f'samples_nearby_{seq}',height=90,placeholder='Ex.: Rua A\nRua B')
    st.caption('O link do Google Maps fornece a referência geográfica para conferência das amostras, mas não revela automaticamente o nome da rua. Informe o logradouro para uma busca mais precisa.')
    # Não inserir "500 metros"/"1 km" na consulta: buscadores não aplicam esse raio a anúncios.
    def google_search(parts):
        q=' '.join(str(part).strip() for part in parts if str(part).strip())
        return 'https://www.google.com/search?q='+quote_plus(q)
    place=municipality.strip() or city.strip()
    target=street.strip()
    area=neighborhood.strip()
    if not target and not area and not place:
        st.warning('Informe ao menos o logradouro, o bairro ou a cidade para preparar a busca.')
    else:
        main_parts=[f'"{target}"' if target else '',f'"{area}"' if area else '',place]
        primary=google_search([kind,'à venda','imóvel',*main_parts])
        st.link_button('Pesquisar anúncios no Google',primary,type='primary')
        st.caption('A pesquisa prioriza o logradouro informado. Abra os anúncios e confira a localização antes de considerar qualquer resultado dentro do raio.')
        searches=[]
        if target and area:
            searches.append(('Buscar pelo logradouro (sem exigir bairro)',google_search([kind,'à venda',f'"{target}"',place])))
        if area:
            searches.append(('Buscar pelo bairro',google_search([kind,'à venda',f'"{area}"',place])))
        unique_streets=[]
        for line in nearby.splitlines():
            v=line.strip()
            if v and v.casefold() not in [x.casefold() for x in unique_streets] and v.casefold()!=target.casefold():
                unique_streets.append(v)
        for nearby_street in unique_streets[:12]:
            searches.append((f'Buscar na {nearby_street}',google_search([kind,'à venda',f'"{nearby_street}"',place])))
        if searches:
            with st.expander('Ampliar pesquisa para bairro e logradouros próximos'):
                for title,url in searches:
                    st.link_button(title,url)
        st.caption(f'Raio de referência escolhido: {radius} m. Somente amostras com coordenadas confirmadas podem ser classificadas como dentro ou fora do raio na tabela abaixo.')
    st.subheader('2. Cadastro, importação e seleção de amostras')
    if 'samples_rows' not in st.session_state: st.session_state.samples_rows=[]
    if 'samples_rev' not in st.session_state: st.session_state.samples_rev=0
    with st.expander('Importar planilha CSV (opcional)'):
        st.caption('CSV UTF-8 com colunas: '+', '.join(FIELDS)+'. Colunas ausentes recebem valores em branco. Confira os dados importados.')
        uploaded=st.file_uploader('Arquivo CSV',type=['csv'],key=f'samples_csv_{seq}')
        if uploaded is not None and st.button('Importar CSV',key=f'samples_import_{seq}'):
            try:
                raw=pd.read_csv(uploaded,sep=None,engine='python',dtype=str,keep_default_na=False)
                if len(raw)>300: raise ValueError('Limite de 300 linhas por importação.')
                new=[]
                for _,row in raw.iterrows():
                    d=blank()
                    for field in FIELDS:
                        if field in raw.columns: d[field]=row[field]
                    d['incluir']=str(d['incluir']).strip().lower() not in ('false','0','não','nao','')
                    new.append(d)
                st.session_state.samples_rows+=new
                st.session_state.samples_rev+=1
                st.rerun()
            except Exception as exc:
                st.error(f'Importação não concluída: {exc}')
    if st.button('Adicionar amostra',key='samples_add'):
        st.session_state.samples_rows.append(blank())
        st.session_state.samples_rev+=1
        st.rerun()
    df=pd.DataFrame(st.session_state.samples_rows,columns=FIELDS)
    edited=st.data_editor(df,num_rows='dynamic',hide_index=True,use_container_width=True,key=f'samples_editor_{seq}_{st.session_state.samples_rev}',column_config={
        'incluir':st.column_config.CheckboxColumn('Incluir'),
        'tipo':st.column_config.SelectboxColumn('Tipo',options=TYPES),
        'situacao':st.column_config.SelectboxColumn('Situação',options=SITUATIONS),
        'preco':st.column_config.NumberColumn('Preço (R$)',min_value=0,format='%.2f'),
        'area_m2':st.column_config.NumberColumn('Área (m²)',min_value=0,format='%.2f'),
        'latitude':st.column_config.NumberColumn('Latitude',format='%.7f'),
        'longitude':st.column_config.NumberColumn('Longitude',format='%.7f'),
        'url':st.column_config.LinkColumn('Anúncio / fonte'),
        'quartos':st.column_config.NumberColumn('Quartos',min_value=0,step=1),
    })
    if st.button('Salvar tabela de amostras',type='primary',key='samples_save'):
        st.session_state.samples_rows=edited.to_dict('records')
        st.session_state.samples_rev+=1
        st.rerun()
    result=enrich(edited.to_dict('records'),origin,radius)
    st.subheader('3. Conferência geográfica e indicadores')
    preview=pd.DataFrame([{'Incluir':bool(r.get('incluir')),'Imóvel':r.get('titulo'),'Tipo':r.get('tipo'),'Preço (R$)':number(r.get('preco')),'Área (m²)':number(r.get('area_m2')),'R$/m²':r['preco_m2'],'Distância reta (m)':r['distancia_reta_m'],'Dentro do raio':r['dentro_raio'],'Situação':r.get('situacao')} for r in result])
    st.dataframe(preview,use_container_width=True,hide_index=True)
    chosen=[r for r in result if bool(r.get('incluir'))]
    if origin:
        outside=sum(r['dentro_raio']=='Não' for r in chosen)
        unknown=sum(r['dentro_raio']=='Não verificado' for r in chosen)
        if outside:st.warning(f'{outside} amostra(s) selecionada(s) estão fora do raio de {radius} m.')
        if unknown:st.warning(f'{unknown} amostra(s) selecionada(s) não possuem coordenadas para verificar o raio.')
    prices=[r['preco_m2'] for r in chosen if r['preco_m2'] is not None]
    if prices:
        st.metric('Média simples de R$/m² das amostras selecionadas com dados válidos',f'R$ {sum(prices)/len(prices):,.2f}'.replace(',','X').replace('.',',').replace('X','.'))
        st.caption('Indicador descritivo de preços informados, sem homogeneização, sem tratamento de ofertas e sem estimativa automática do valor do imóvel avaliando.')
    st.subheader('4. Exportação')
    st.caption('Os arquivos incluem apenas os registros selecionados. Confira preços, fontes, datas, comparabilidade e localização antes de utilizar no PTAM.')
    if chosen:
        export_rows=[]
        for r in chosen:
            d=dict(r)
            d['url']=validated_url(d.get('url'))
            export_rows.append(d)
        csv_text=pd.DataFrame(export_rows).to_csv(index=False,sep=';',decimal=',').encode('utf-8-sig')
        a,b=st.columns(2)
        a.download_button('Exportar amostras em CSV',csv_text,'PTAM_GEO_Amostras.csv','text/csv',use_container_width=True)
        b.download_button('Exportar amostras em Word',export_docx(export_rows,reference or city,radius,kind),'PTAM_GEO_Amostras.docx','application/vnd.openxmlformats-officedocument.wordprocessingml.document',use_container_width=True)
    else:
        st.info('Adicione e selecione pelo menos uma amostra para exportar.')
    st.warning('Os registros ficam somente na sessão. Exporte os arquivos antes de sair ou iniciar nova pesquisa. Não inclua dados pessoais desnecessários de anunciantes.')
