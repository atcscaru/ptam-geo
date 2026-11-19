## PTAM GEO v2.8: percurso a pé por logradouros públicos

O Google Routes agora consulta o modo `WALK`, não automóvel. O critério adotado é o menor percurso a pé por ruas, avenidas, travessas e demais logradouros públicos regulares identificados no mapa. Não utilizar becos, vielas, atalhos por terrenos ou travessias não oficiais de cursos d’água. Pontes e travessias oficiais de pedestres integradas aos logradouros são admitidas.

**Limitação:** a API Google Routes não permite proibir automaticamente todas essas passagens. O avaliador deve conferir o trajeto, corrigir manualmente a distância quando necessário, registrar fonte e marcar **Trajeto por logradouros conferido**. A exportação de registros selecionados fica bloqueada sem essa validação. O botão de cálculo desmarca a conferência das rotas recalculadas.

Cadastro manual sem coordenadas, preservação de distâncias conferidas, autenticação Google e exportação Word permanecem. Não há persistência entre sessões. Para instalar, substituir os arquivos do repositório GitHub pelos do ZIP e aguardar deploy do Streamlit. Segredos permanecem somente no Streamlit Cloud.


## Categorias ampliadas na v2.8
- Academias (gym).
- Shoppings e centros de compras (shopping_mall e busca textual por centros comerciais/galerias).
- Saúde: hospitais, clínicas, médicos e farmácias, com buscas textuais complementares para UBS, USF/PSF, UPA, maternidades, clínicas/hospitais veterinários e USB.
- A pesquisa utiliza o raio geográfico informado. A distância por percurso a pé é calculada posteriormente para os pontos selecionados.
- As buscas textuais são indicativas, podem retornar resultados imprecisos ou incompletos e exigem confirmação humana de categoria, natureza e funcionamento.
- As buscas complementares aumentam o consumo da Places API. O contador preventivo contabiliza todas as requisições previstas antes de pesquisar.


## Fluxo simplificado v2.8
1. Pesquise os estabelecimentos e marque **Incluir** nos relevantes.
2. Clique **Calcular percursos a pé dos selecionados**. São processados até dez locais por lote, sujeitos à cota da sessão.
3. Confira os trajetos em logradouros públicos e marque a validação apenas após verificar.
4. Corrija somente distâncias incorretas, escolhendo a origem da medição (Google Earth, medição manual ou outra).
5. Clique **Salvar e proteger correções da tabela** e exporte o Word após a validação.

Distâncias editadas são automaticamente protegidas de cálculos posteriores. O botão de ajuste de origem e coordenadas fica na seção excepcional. Se a localização do imóvel ou do estabelecimento estiver incorreta, ajuste-a e recalcule o percurso afetado. Dados permanecem apenas na sessão Streamlit, sem armazenamento permanente. O Google Routes não garante automaticamente exclusão de vielas e atalhos.


## Versão 2.8.2: botão Nova avaliação
Na barra lateral, selecione **Nova avaliação** e confirme. O aplicativo descarta os resultados, revisões, formulário de infraestrutura, texto complementar e confirmação de exportação da avaliação anterior. Os campos de endereço e localização são reiniciados. O login Google e os contadores de consumo de APIs da sessão são preservados. **Exporte o Word antes de confirmar:** não existe recuperação automática da avaliação descartada. Não use Limpar caches para iniciar outro imóvel. A dependência `httpx` foi explicitamente mantida em `requirements.txt` para o login Google.
