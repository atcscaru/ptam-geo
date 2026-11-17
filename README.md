## PTAM GEO v2.6: percurso a pé por logradouros públicos

O Google Routes agora consulta o modo `WALK`, não automóvel. O critério adotado é o menor percurso a pé por ruas, avenidas, travessas e demais logradouros públicos regulares identificados no mapa. Não utilizar becos, vielas, atalhos por terrenos ou travessias não oficiais de cursos d’água. Pontes e travessias oficiais de pedestres integradas aos logradouros são admitidas.

**Limitação:** a API Google Routes não permite proibir automaticamente todas essas passagens. O avaliador deve conferir o trajeto, corrigir manualmente a distância quando necessário, registrar fonte e marcar **Trajeto por logradouros conferido**. A exportação de registros selecionados fica bloqueada sem essa validação. O botão de cálculo desmarca a conferência das rotas recalculadas.

Cadastro manual sem coordenadas, preservação de distâncias conferidas, autenticação Google e exportação Word permanecem. Não há persistência entre sessões. Para instalar, substituir os arquivos do repositório GitHub pelos do ZIP e aguardar deploy do Streamlit. Segredos permanecem somente no Streamlit Cloud.
