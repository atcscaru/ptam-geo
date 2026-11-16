# PTAM GEO v1.0

Aplicativo web Streamlit para pesquisa geográfica, conferência humana e exportação de considerandos para PTAM em Word editável.

## Instalação

Requer Python 3.10 ou superior.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Abra o endereço local exibido pelo Streamlit (normalmente http://localhost:8501).

## Fluxo

1. Cole um link do Google Maps que contenha coordenadas, ou digite latitude/longitude.
2. Consulte POIs no raio padrão de 1.000 m. Resultados dependem da cobertura do OpenStreetMap.
3. Confira a lista, selecione registros e, se desejar, calcule percurso viário para até 15 locais selecionados.
4. Edite textos, adicione considerandos comprovados e assinale a revisão obrigatória.
5. Exporte o arquivo Word.

## Fontes e limitações

- POIs e via: OpenStreetMap via Overpass. A natureza pública/privada não é comprovada apenas pela categoria OSM. A categoria 'Educação pública' é temática e exige validação administrativa de cada escola.
- Distâncias em linha reta: Haversine entre coordenadas, aproximadas ao metro. Não representam distância de caminhada nem levantamento topográfico.
- Percurso viário: serviço público OSRM de demonstração. Pode não funcionar, não representa trajetos de pedestres e não é medição pelo Google Earth.
- Pavimentação: etiqueta `surface` do OSM, quando existente; depende de vistoria.
- Esquina mais próxima, redes de esgoto, drenagem, iluminação e funcionamento de unidades não são determinados automaticamente nesta versão.
- Links curtos do Google podem falhar ao resolver; nesse caso, informe as coordenadas.
- Não há banco de dados nem salvamento permanente de modelo de considerandos; a sessão Streamlit pode manter dados temporários durante o uso.
- Fontes de terceiros e seus termos de uso devem ser observados antes da implantação comercial.

## Chaves de API e custos

| Integração | Nesta versão | Chave | Custos |
|---|---|---|---|
| OpenStreetMap/Overpass público | Sim | Não | Sem tarifa direta, com limites e disponibilidade variável |
| OSRM demonstração | Sim, opcional | Não | Sem tarifa direta, limitado; produção exige serviço próprio/provedor |
| Google Maps Places/Routes/Geocoding | Não | Sim | Cobrança por consumo, faturamento Google Cloud |
| Google Earth medição automática | Não | Não implementada | Depende de solução/licenciamento disponível |
| Exportação Word | Sim | Não | Sem tarifa por documento |
| Hospedagem em nuvem | Não | Conforme provedor | Pode haver cobrança |

## Segurança

O app não implementa autenticação, controle de acesso ou banco de dados. Para uso profissional com informações confidenciais, hospede em ambiente protegido com HTTPS, autenticação e política de retenção. Não publique dados pessoais em servidores públicos de geocodificação.
