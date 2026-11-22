# PTAM GEO v3.0 — Pesquisa assistida por logradouros

Atualização sobre a v2.9. Mantém o módulo de considerandos e substitui os três botões de buscas genéricas do módulo de amostras.

## Pesquisa de anúncios
- Informe o link ou coordenadas do imóvel para referência e verificação de distância das amostras cadastradas.
- Informe o logradouro, bairro e cidade/UF. O aplicativo não extrai automaticamente nomes de ruas a partir do link do Google Maps.
- Escolha o tipo de imóvel e clique em **Pesquisar anúncios no Google**.
- Opcionalmente, informe logradouros próximos, um por linha, para gerar pesquisas específicas.
- Abra os anúncios encontrados, confira o endereço e registre links e dados das amostras na tabela existente.

**Limitação essencial:** o Google Search não permite filtrar anúncios por círculo de 500 m ou 1 km. O raio escolhido é referência; somente amostras com coordenadas confirmadas são classificadas como dentro/fora do raio pelo aplicativo. Resultados de pesquisa não são amostras verificadas. Não há nova API nem coleta automatizada de sites.

## Instalação
Substitua os arquivos da raiz do repositório pelos arquivos desta pasta, mantendo as credenciais apenas nos Secrets do Streamlit Cloud. Verifique o funcionamento do módulo de considerandos e do módulo de amostras antes do uso profissional.


## Versão 3.1: recuperação de pesquisa

- A versão aparece no alto da tela, em ambos os módulos.
- Na barra lateral, **Baixar backup da pesquisa (.json)** cria um arquivo local com o estado salvo na sessão.
- **Restaurar backup (.json)** recupera dados depois de reinício ou desconexão.
- Antes do backup, clique em **Salvar e proteger correções da tabela** (considerandos) ou **Salvar alterações da tabela** (amostras), para incorporar edições ainda não confirmadas.
- Não há salvamento automático durável: a hospedagem Streamlit pode reiniciar e perder dados ainda não baixados. Para evitar perdas sem intervenção, será necessário integrar armazenamento persistente externo com controle de acesso.
- Não compartilhe arquivos de backup: podem conter dados confidenciais dos imóveis e da avaliação.
- Reinícios podem decorrer de deploy, memória, instabilidade ou encerramento da sessão. A causa específica exige logs do Streamlit Cloud no horário do ocorrido.


## Atualização 3.1.1
- Permite até 20 percursos a pé selecionados por lote.
- O limite preventivo de 30 consultas Routes por sessão continua ativo.
- A perda de sessão não está resolvida por esta atualização: o backup é manual.
- Para recuperação automática após reinício, configurar armazenamento persistente privado (banco de dados), com autenticação e controle de acesso.
- Verificar logs do Streamlit Cloud para determinar a causa específica dos reinícios.
