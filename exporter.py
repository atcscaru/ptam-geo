from io import BytesIO
from datetime import date
from docx import Document
from docx.shared import Cm,Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT


def build_docx(address,lat,lon,rows,road,notes,method='Linha reta geodésica e, quando disponível, percurso viário'):
    doc=Document();sec=doc.sections[0]
    sec.top_margin=Cm(3);sec.left_margin=Cm(3);sec.bottom_margin=Cm(2);sec.right_margin=Cm(2)
    normal=doc.styles['Normal'];normal.font.name='Times New Roman';normal.font.size=Pt(12)
    normal.paragraph_format.line_spacing=1.5;normal.paragraph_format.first_line_indent=Cm(1.25)
    def para(s):
        p=doc.add_paragraph(s);p.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY;return p
    h=doc.add_heading('CONSIDERANDOS DA ANÁLISE MERCADOLÓGICA',0);h.alignment=WD_ALIGN_PARAGRAPH.CENTER
    para('PTAM GEO | Pesquisa geográfica preliminar com revisão do avaliador')
    para(f'Imóvel de referência: {address or "Localização por coordenadas"}. Coordenadas: {lat:.7f}, {lon:.7f}. Data da pesquisa: {date.today():%d/%m/%Y}.')
    doc.add_heading('Considerandos',level=1)
    if road and road.get('logradouro') and road.get('logradouro')!='Não identificado':
        para(f'Considerando que o imóvel está localizado nas proximidades do logradouro {road["logradouro"]}, conforme identificação cartográfica do OpenStreetMap, sujeita a confirmação no local;')
    if road and road.get('pavimentação') and road.get('pavimentação')!='Não informada no OSM':
        para(f'Considerando que o cadastro cartográfico indica pavimentação do tipo “{road["pavimentação"]}” na via identificada, informação que depende de vistoria física para confirmação;')
    for row in rows:
        if not row.get('incluir'):continue
        if row.get('texto_editado','').strip():
            s=row['texto_editado'].strip()
        else:
            d=row.get('distância_reta_m');v=row.get('distância_vias_m')
            metrics=f'a aproximadamente {d} metros em linha reta' if d is not None else 'nas proximidades'
            if v is not None:metrics+=f' e {v} metros por percurso viário estimado'
            s=f'Considerando que, na categoria {row.get("categoria", "serviços")}, consta o estabelecimento {row.get("nome", "não identificado")}, situado {metrics}, conforme cadastro geográfico consultado, sujeito a confirmação de funcionamento e localização;'
        para(s)
    if notes.strip():
        doc.add_heading('Informações complementares validadas pelo avaliador',level=1)
        for line in notes.splitlines():
            if line.strip():para(line.strip())
    doc.add_heading('Critérios, fontes e limitações',level=1)
    para(f'As distâncias em linha reta foram calculadas pela fórmula geodésica de Haversine, entre as coordenadas do imóvel e os pontos cadastrados. {method}. As distâncias viárias, quando disponíveis, são estimativas de roteamento, não medições certificadas pelo Google Earth. Os cadastros do OpenStreetMap são colaborativos e podem estar incompletos ou desatualizados. A proximidade de uma instalação não comprova seu funcionamento, natureza jurídica, acesso ou infraestrutura efetivamente disponível no imóvel.')
    para('A pavimentação, a existência de esgotamento sanitário, drenagem, iluminação pública e a identificação da esquina mais próxima exigem confirmação documental ou vistoria. Não foram presumidas características ausentes das fontes.')
    para('Documento auxiliar de pesquisa para subsidiar PTAM extrajudicial. Não constitui, isoladamente, parecer técnico completo, nem substitui a responsabilidade profissional do avaliador. Uso restrito ao destinatário autorizado. Evitar a inserção de dados pessoais desnecessários.')
    doc.add_heading('Rastreabilidade dos registros selecionados',level=1)
    t=doc.add_table(rows=1,cols=4);t.style='Table Grid';t.alignment=WD_TABLE_ALIGNMENT.CENTER
    for cell,label in zip(t.rows[0].cells,['Estabelecimento','Dist. reta','Dist. via','Fonte / confiabilidade']):cell.text=label
    for row in rows:
        if row.get('incluir'):
            cells=t.add_row().cells
            for cell,value in zip(cells,[row.get('nome',''),str(row.get('distância_reta_m',''))+' m',str(row.get('distância_vias_m') or 'Não disponível'),row.get('fonte','')+' | '+row.get('confiança','')]):cell.text=str(value)
    if road and road.get('fonte'):para('Fonte da via: '+road['fonte'])
    para('Conferência e aprovação técnica pelo avaliador: __________________________________')
    b=BytesIO();doc.save(b);return b.getvalue()
