# PTAM GEO v2.0

Aplicativo Streamlit de pesquisa geográfica para subsidiar os considerandos de PTAM. Integra Google Places API (New), Routes API e exportação Word. Revisão humana obrigatória. Não substitui vistoria, fontes oficiais ou responsabilidade técnica.

## Publicação no Streamlit Cloud

1. Substitua os arquivos `app.py`, `geo.py`, `exporter.py`, `requirements.txt` e `README.md` no repositório GitHub existente. O nome do aplicativo e o endereço publicado podem permanecer os mesmos.
2. Google Cloud Console: crie ou selecione projeto, ative faturamento e habilite **Places API (New)** e **Routes API**. Crie uma chave de API com restrições adequadas às chamadas de servidor (restrição por API e, quando aplicável, por origem/IP). Não coloque a chave no GitHub.
3. Streamlit Cloud > aplicativo > Settings > Secrets, adicione:

```toml
GOOGLE_MAPS_API_KEY = "SUA_CHAVE_PRIVADA_AQUI"
```

4. Salve Secrets, reinicie o aplicativo e teste com coordenadas não sensíveis. A chave deve permanecer confidencial.

## Custos e limites

A cobrança é por uso conforme a tabela vigente do Google Maps Platform. A pesquisa faz até uma requisição Places Nearby Search por categoria selecionada, com até 20 resultados por categoria; o botão de rotas faz até 15 requisições Routes por acionamento. Há custos mesmo que não haja resultado em alguns cenários, conforme política do provedor. Configure alertas e cotas no Google Cloud; alertas de orçamento não equivalem a limite rígido de gastos.

## Limitações

- Somente Google Maps URLs com coordenadas explícitas ou links curtos resolvíveis. Caso contrário, informe latitude e longitude.
- Distância em linha reta é calculada por Haversine. Percurso viário usa modo automóvel e não é medição do Google Earth.
- Resultado do Places não comprova funcionamento, natureza pública/privada, pavimentação ou disponibilidade de serviços.
- Os resultados por categoria são limitados a 20 e não constituem levantamento exaustivo.
- Não há autenticação de usuários, armazenamento persistente nem gestão de dados confidenciais.
- O aplicativo não reutiliza nem armazena o documento de exemplo enviado pelo usuário.
