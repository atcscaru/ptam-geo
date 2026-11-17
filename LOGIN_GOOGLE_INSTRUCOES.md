# PTAM GEO v2.4: login exclusivo com Google

## 1. Configurar Google Cloud

No projeto Google Cloud, abra **APIs e serviços > Tela de consentimento OAuth** (Google Auth Platform). Configure o nome do aplicativo e o e-mail de suporte. Se estiver em modo **Testing**, adicione seu e-mail Google em **Test users**. Para conta Gmail pessoal, normalmente escolha público **External**; não é necessário publicar o app para uso como usuário de teste, mas o modo Testing pode exigir nova autorização periodicamente.

Em **Clients / Credenciais > Criar cliente OAuth**, escolha **Aplicativo da Web** e configure em **URIs de redirecionamento autorizados**:

`https://SEU-APP.streamlit.app/oauth2callback`

Use o endereço HTTPS EXATO da sua aplicação Streamlit (sem barra final). Salve o **Client ID** e o **Client Secret**. Eles são credenciais OAuth diferentes da chave Google Maps.

## 2. Configurar Secrets no Streamlit Community Cloud

No painel do app > Settings > Secrets, preserve a chave Google Maps já existente e acrescente (substitua os exemplos):

```toml
GOOGLE_MAPS_API_KEY = "SUA_CHAVE_GOOGLE_MAPS_EXISTENTE"
ALLOWED_GOOGLE_EMAIL = "seu-email@gmail.com"

[auth]
redirect_uri = "https://SEU-APP.streamlit.app/oauth2callback"
cookie_secret = "COLE_UMA_STRING_ALEATORIA_FORTE_COM_PELO_MENOS_32_CARACTERES"
client_id = "SEU_GOOGLE_OAUTH_CLIENT_ID"
client_secret = "SEU_GOOGLE_OAUTH_CLIENT_SECRET"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

`ALLOWED_GOOGLE_EMAIL` precisa ser idêntico ao e-mail da conta Google que fará login. Não publique o conteúdo dos Secrets, nem capturas com os valores. Gere `cookie_secret` com um gerador criptograficamente seguro, por exemplo `python -c "import secrets; print(secrets.token_urlsafe(48))"` em seu computador.

## 3. Atualizar GitHub

Substitua os seis arquivos originais pelos arquivos deste pacote (incluindo `app.py` e `requirements.txt`). Acrescente este manual. Faça commit. O Streamlit fará o redeploy; se necessário, reinicie o aplicativo.

## 4. Testar

Abra o aplicativo em janela anônima. A página deve mostrar apenas o botão **Entrar com Google**. Entre com sua conta autorizada e confirme que o app abre. Teste com outra conta Google: deve mostrar **não autorizada**, sem permitir consultas. Teste **Sair**. Não execute consultas reais ao Maps até validar o acesso.

## Segurança e limites

A checagem de acesso é feita no servidor, antes da execução do aplicativo. O e-mail deve estar verificado pelo Google. Login não protege o repositório GitHub público nem cria banco de dados seguro para documentos pessoais. Mantenha os dados de clientes fora do código e do repositório. A chave Maps permanece nos Secrets. O login não altera os limites e custos das APIs; revise as cotas no Google Cloud.
