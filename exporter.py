from io import BytesIO
from datetime import date
from docx import Document
from docx.shared import Cm,Pt
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT


def build_docx(address,lat,lon,rows,road,notes,method='Linha reta geodésica e, quando disponível, percurso viário',infra_text=''):
    doc=Document();sec=doc.sections[0]
    sec.top_margin=Cm(3);sec.left_margin=Cm(3);sec.bottom_margin=Cm(2);sec.right_margin=Cm(2)
    normal=doc.styles['Normal'];normal.font.name='Times New Roman';normal.font.size=Pt(12)
    normal.paragraph_format.line_spacing=1.5;normal.paragraph_format.first_line_indent=Cm(1.25)
    def para(s):
        p=doc.add_paragraph(s);p.alignment=WD_ALIGN_PARAGRAPH.JUSTIFY;return p
    h=doc.add_heading('CONSIDERANDOS DA ANÁLISE MERCADOLÓGICA',0);h.alignment=WD_ALIGN_PARAGRAPH.CENTER
    para('PTAM GEO | Pesquisa geográfica preliminar com revisão do avaliador')
    para(f'Imóvel de referência: {address or "Imóvel informado pelo avaliador"}.' + (f' Coordenadas confirmadas: {lat:.7f}, {lon:.7f}.' if lat is not None and lon is not None else ' Localização geográfica eletrônica não informada.') + f' Data da pesquisa: {date.today():%d/%m/%Y}.')
    doc.add_heading('Considerandos',level=1)
    if road and road.get('logradouro') and road.get('logradouro') not in ('Não identificado', 'Não verificado automaticamente'):
        para(f'Considerando que o imóvel está localizado nas proximidades do logradouro {road["logradouro"]}, conforme fonte cartográfica informada, sujeita a confirmação no local;')
    if road and road.get('pavimentação') and road.get('pavimentação') not in ('Não informada no OSM', 'Não verificada'):
        para(f'Considerando que o cadastro cartográfico indica pavimentação do tipo “{road["pavimentação"]}” na via identificada, informação que depende de vistoria física para confirmação;')
    for row in rows:
        if not row.get('incluir'):continue
        if row.get('texto_editado','').strip():
            s=row['texto_editado'].strip()
        else:
            v=row.get('distância_vias_m')
            metrics=(f'a aproximadamente {float(v):g} metros por percurso viário' if v is not None else 'nas proximidades')
            source_distance=row.get('origem_distancia') or 'Fonte não especificada'
            metrics+=f' (fonte da distância: {source_distance})' if v is not None else ''
            if row.get('categoria') == 'Cemitérios':
                nature = row.get('natureza_cemiterio', 'Não verificada')
                qualifier = ('público' if nature == 'Público' else 'privado' if nature == 'Privado' else 'de natureza administrativa não verificada')
                s=f'Considerando que, no entorno do imóvel avaliando, foi identificado o cemitério {row.get("nome", "não identificado")}, {qualifier}, localizado {metrics}, conforme levantamento informado e conferido pelo avaliador, com localização, acesso e natureza sujeitos à confirmação documental ou em vistoria;'
            else:
                s=f'Considerando que, na categoria {row.get("categoria", "serviços")}, consta o estabelecimento {row.get("nome", "não identificado")}, situado {metrics}, conforme fonte indicada no levantamento, sujeito a confirmação de funcionamento e localização;'
        para(s)
    if infra_text:
        para(infra_text)
    if notes.strip():
        doc.add_heading('Informações complementares validadas pelo avaliador',level=1)
        for line in notes.splitlines():
            if line.strip():para(line.strip())
    doc.add_heading('Critérios, fontes e limitações',level=1)
    para(f'{method}. As distâncias viárias são aproximadas e dependem do ponto de acesso, sentido de circulação e rota adotada. Medições manuais não foram automaticamente verificadas pelo sistema. O cadastro Google Places pode estar incompleto ou desatualizado; a proximidade não comprova funcionamento, natureza jurídica ou infraestrutura efetivamente disponível.')
    para('A pavimentação, a existência de esgotamento sanitário, drenagem, iluminação pública e a identificação da esquina mais próxima exigem confirmação documental ou vistoria. Não foram presumidas características ausentes das fontes.')
    para('Documento auxiliar de pesquisa para subsidiar PTAM extrajudicial. Não constitui, isoladamente, parecer técnico completo, nem substitui a responsabilidade profissional do avaliador. Uso restrito ao destinatário autorizado. Evitar a inserção de dados pessoais desnecessários.')
    doc.add_heading('Rastreabilidade dos registros selecionados',level=1)
    t=doc.add_table(rows=1,cols=4);t.style='Table Grid';t.alignment=WD_TABLE_ALIGNMENT.CENTER
    for cell,label in zip(t.rows[0].cells,['Estabelecimento','Distância viária','Origem da medição','Fonte / observação']):cell.text=label
    for row in rows:
        if row.get('incluir'):
            cells=t.add_row().cells
            for cell,value in zip(cells,[row.get('nome',''),(f"{float(row['distância_vias_m']):g} m" if row.get('distância_vias_m') is not None else 'Não disponível'),row.get('origem_distancia') or 'Não informada',str(row.get('fonte') or '')+' | '+str(row.get('observação') or '')]):cell.text=str(value)
    if road and road.get('fonte'):para('Fonte da via: '+road['fonte'])
    para('Conferência e aprovação técnica pelo avaliador: __________________________________')
    b=BytesIO();doc.save(b);return b.getvalue()
