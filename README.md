# PTAM GEO v2.2 | Infraestrutura e conferência de coordenadas

Esta versão acrescenta formulário manual separado para **logradouro** e **imóvel avaliando** sobre pavimentação, abastecimento de água, saneamento/drenagem, esgotamento sanitário, energia elétrica e telefonia. Gera **um único considerando** no Word editável, com fonte obrigatória. Itens não verificados são omitidos.

Também permite editar a origem e as coordenadas dos estabelecimentos. Use **Recalcular linhas retas com coordenadas conferidas** antes de calcular rotas e exportar. A edição invalida rotas anteriores; o novo cálculo viário usa as coordenadas confirmadas. A posição do Google Places pode ser o centro da edificação, e não a entrada. A distância viária da Routes API pode diferir de uma medição manual no Earth devido a acesso e regras de trânsito.

**Atenção:** não há verificação automática da infraestrutura nem garantia de exatidão de coordenadas. O avaliador deve conferir no mapa/vistoria e aprovar os considerandos. Os limites de consumo continuam por sessão e não impedem cobrança global.

## Atualização

No repositório GitHub do PTAM GEO, substitua `app.py`, `geo.py`, `exporter.py`, `requirements.txt` e `README.md`, e **adicione** `infrastructure.py`. Faça commit e aguarde a atualização do Streamlit. A chave permanece em Secrets como `GOOGLE_MAPS_API_KEY`; não a inclua no GitHub.

# PTAM GEO v2.1 — revisão de APIs e controle preventivo de consumo

## Auditoria do código v2.0
- `query_google` chama `places.googleapis.com/v1/places:searchNearby` **uma vez por categoria** (5 categorias padrão), com `maxResultCount=20`. A máscara de campos é `places.id,places.displayName,places.location,places.formattedAddress,places.googleMapsUri,places.primaryType`. O SKU exato e a tarifa devem ser confirmados na tabela atual e no painel de faturamento, pois os campos solicitados determinam a modalidade. Não presumir SKU Essentials.
- `road_distance` chama `routes.googleapis.com/directions/v2:computeRoutes` **uma vez por estabelecimento selecionado** (até 15 por clique na v2.0), com `travelMode=DRIVE`, `routingPreference=TRAFFIC_UNAWARE` e máscara `routes.distanceMeters`. Confirmar SKU no painel.
- `haversine` é cálculo local, sem requisição externa. `street_context` não consulta API e não verifica pavimentação.
- A pesquisa Nearby retorna até 20 estabelecimentos por categoria e não é exaustiva.
- O arquivo `exporter.py` da v2.0 ainda mencionava OSM incorretamente; corrigido na v2.1.

## Controles da v2.1
- Limites **por sessão**: 20 consultas Places e 30 Routes. Cada clique de pesquisa reserva 1 consulta por categoria selecionada, inclusive quando houver falha; cada clique de rotas reserva 1 por registro selecionado. Máximo 10 rotas por clique.
- Estes limites **não são mensais nem globais**. Várias pessoas, abas ou reinicializações podem excedê-los. Não constituem garantia de custo zero.
- Recomenda-se, para até 100 avaliações/mês com cinco categorias e até 10 rotas por avaliação, estimar 500 solicitações Nearby e 1.000 solicitações Routes/mês, antes de pesquisas repetidas, erros ou testes.

## Configuração obrigatória no Google Cloud (antes de ativar uso)
1. Ativar apenas **Places API (New)** e **Routes API**. Não ativar serviços adicionais desnecessários.
2. Em **APIs e serviços > Cotas e limites do sistema**, configurar cotas diárias conservadoras nas métricas aplicáveis, quando editáveis. Começar com 25 solicitações Places/dia e 50 Routes/dia, e ajustar conforme uso real. Cotas podem ter granularidade distinta e algumas não são configuráveis.
3. Em **Faturamento > Orçamentos e alertas**, criar orçamento baixo (por exemplo R$ 20/mês) com alertas em 50%, 90% e 100%. Alertas NÃO bloqueiam cobranças.
4. Criar chave de API com **restrição às APIs Places API (New) e Routes API**. Para app Streamlit no servidor, a restrição por HTTP referrer normalmente não protege chamadas de backend; restrição por IP requer IP de saída fixo. Se a hospedagem não oferecer IP estável, proteja a chave em Secrets e monitore consumo.
5. Streamlit Cloud > App > Settings > Secrets: `GOOGLE_MAPS_API_KEY = "..."`. Nunca colocar chave no GitHub, screenshots ou chat.
6. Em **Faturamento > Relatórios**, conferir SKUs realmente cobrados após 1 pesquisa e 1 rota. Só então ampliar uso.

## Publicação
Substituir `app.py`, `geo.py`, `exporter.py`, `requirements.txt`, `README.md` no repositório já conectado ao Streamlit. Não é necessário criar novo link.

## Limitações
Não houve teste real com chave de API; testes realizados são de sintaxe e inspeção estática. Sem login, banco de dados de uso global, controle mensal persistente ou garantia de custo zero. Revisão humana continua obrigatória.
