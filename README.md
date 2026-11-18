## PTAM GEO v2.7: percurso a pé por logradouros públicos

O Google Routes agora consulta o modo `WALK`, não automóvel. O critério adotado é o menor percurso a pé por ruas, avenidas, travessas e demais logradouros públicos regulares identificados no mapa. Não utilizar becos, vielas, atalhos por terrenos ou travessias não oficiais de cursos d’água. Pontes e travessias oficiais de pedestres integradas aos logradouros são admitidas.

**Limitação:** a API Google Routes não permite proibir automaticamente todas essas passagens. O avaliador deve conferir o trajeto, corrigir manualmente a distância quando necessário, registrar fonte e marcar **Trajeto por logradouros conferido**. A exportação de registros selecionados fica bloqueada sem essa validação. O botão de cálculo desmarca a conferência das rotas recalculadas.

Cadastro manual sem coordenadas, preservação de distâncias conferidas, autenticação Google e exportação Word permanecem. Não há persistência entre sessões. Para instalar, substituir os arquivos do repositório GitHub pelos do ZIP e aguardar deploy do Streamlit. Segredos permanecem somente no Streamlit Cloud.


## Categorias ampliadas na v2.7
- Academias (gym).
- Shoppings e centros de compras (shopping_mall e busca textual por centros comerciais/galerias).
- Saúde: hospitais, clínicas, médicos e farmácias, com buscas textuais complementares para UBS, USF/PSF, UPA, maternidades, clínicas/hospitais veterinários e USB.
- A pesquisa utiliza o raio geográfico informado. A distância por percurso a pé é calculada posteriormente para os pontos selecionados.
- As buscas textuais são indicativas, podem retornar resultados imprecisos ou incompletos e exigem confirmação humana de categoria, natureza e funcionamento.
- As buscas complementares aumentam o consumo da Places API. O contador preventivo contabiliza todas as requisições previstas antes de pesquisar.
