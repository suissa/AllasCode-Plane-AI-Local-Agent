# Discovery and Baseline Mapping: WhatsApp Gateway

Este documento registra a etapa **1. Discovery and Baseline Mapping** do `TODO.md`. Ele não altera a execução do gateway; apenas mapeia o estado atual para orientar a troca futura para o serviço Evolution Go em `gateway/platforms/whatsapp/`.

## Escopo verificado

- Gateway Hermes atual: `gateway/run.py`, `gateway/config.py`, `gateway/platforms/whatsapp.py`, `gateway/whatsapp_identity.py`.
- Projeto Evolution Go local: `gateway/platforms/whatsapp/`.
- Configuração e instalação relacionadas: `hermes_cli/config.py`, `scripts/install.sh`, `gateway/platforms/whatsapp/.env.example`, `gateway/platforms/whatsapp/Makefile`, `gateway/platforms/whatsapp/pkg/routes/routes.go`, `gateway/platforms/whatsapp/pkg/config/config.go`.

## Resultado resumido

O Hermes já possui uma pasta `gateway/platforms/whatsapp/` contendo o projeto Evolution Go. O adaptador ativo continua sendo `gateway/platforms/whatsapp.py`, mas agora o backend padrão dele é a API Evolution Go local. O bridge Node.js anterior permanece disponível somente como fallback explícito com `whatsapp.backend: bridge` ou `WHATSAPP_GATEWAY_BACKEND=bridge`.

O backend Evolution Go preserva a interface do `BasePlatformAdapter`: `connect()` prepara/verifica o serviço Go em `gateway/platforms/whatsapp/`, força `SERVER_PORT=9991` no `.env`, executa `make build` antes de `make dev` quando precisa subir o serviço local, faz health check em `/server/ok`, cria/conecta a instância e redireciona envio/edição/mídia/digitação para endpoints Evolution Go.

## 1. Fluxo atual de startup do gateway

1. `start_gateway()` cria um `GatewayRunner`, que carrega `GatewayConfig` via `load_gateway_config()` quando uma configuração explícita não é passada.
2. `GatewayRunner.start()` executa verificações globais, descobre plugins e percorre `self.config.platforms`.
3. Para cada plataforma com `PlatformConfig.enabled == True`, o runner chama `_create_adapter(platform, platform_config)`.
4. Para `Platform.WHATSAPP`, `_create_adapter()` importa `WhatsAppAdapter` e `check_whatsapp_requirements()` de `gateway.platforms.whatsapp`, exige Node.js e retorna `WhatsAppAdapter(config)`.
5. O runner injeta handlers comuns no adapter e chama `adapter.connect()` com timeout.
6. Se `connect()` retornar sucesso, o adapter é registrado em `self.adapters` e passa a receber/envia mensagens pelo fluxo comum do gateway.

### Pontos de seleção do WhatsApp

- O enum `Platform.WHATSAPP = "whatsapp"` define o nome canônico da plataforma.
- `GatewayConfig.get_connected_platforms()` só considera plataformas `enabled` e conectadas; para WhatsApp, o checker atual sempre retorna `True` porque a autenticação é delegada ao bridge.
- `_apply_env_overrides()` ativa WhatsApp quando `WHATSAPP_ENABLED=true|1|yes`; se `WHATSAPP_ENABLED=false|0|no`, desativa uma configuração YAML existente.
- Uma configuração YAML em `platforms.whatsapp` ou `gateway.platforms.whatsapp` também pode habilitar a plataforma pelo campo `enabled`.

## 2. Implementação WhatsApp ativa hoje

O arquivo ativo é `gateway/platforms/whatsapp.py`. A classe `WhatsAppAdapter` agora usa Evolution Go por padrão e mantém o bridge Node.js como backend legado. No modo legado, ela ainda:

- usa `bridge_port` em `config.extra`, com padrão `3000`;
- usa `bridge_script` em `config.extra`, com padrão `scripts/whatsapp-bridge/bridge.js`;
- usa `session_path` em `config.extra`, com padrão compatível com `$HERMES_HOME/whatsapp/session`;
- aplica políticas de DM/grupo por `dm_policy`, `allow_from`, `group_policy`, `group_allow_from`, `require_mention`, `mention_patterns` e `free_response_chats`;
- antes de subir o bridge, exige que `creds.json` exista no diretório de sessão;
- instala dependências Node com `npm install --silent` se `node_modules` não existir;
- verifica se já existe bridge em `http://127.0.0.1:{bridge_port}/health`;
- mata bridge órfão/pid antigo e processo usando a porta;
- sobe `node bridge.js --port {bridge_port} --session {session_path} --mode {WHATSAPP_MODE}`;
- aguarda `/health` e status `connected`;
- cria um `aiohttp.ClientSession` persistente;
- faz polling de mensagens em `/messages`.

### Operações bridge usadas hoje

| Operação Hermes | Endpoint bridge atual | Método |
| --- | --- | --- |
| Health check | `/health` | GET |
| Receber mensagens | `/messages` | GET |
| Enviar texto | `/send` | POST |
| Editar mensagem | `/edit` | POST |
| Enviar mídia | `/send-media` | POST |
| Indicador de digitação | `/typing` | POST |
| Informações de chat | `/chat/{chat_id}` | GET |

Essas operações foram redirecionadas no backend padrão para `/send/text`, `/message/edit`, `/send/media`, `/message/presence` e webhook de entrada do Evolution Go.

## 3. Projeto Evolution Go local

A pasta `gateway/platforms/whatsapp/` contém um projeto Go completo com `Makefile`, `Dockerfile`, `go.mod`, `cmd/evolution-go/main.go`, documentação local, Swagger e rotas em `pkg/routes/routes.go`.

### Comandos disponíveis no Makefile

- `make dev`: executa `go run ... cmd/evolution-go/main.go -dev`.
- `make build`: compila o binário em `build/evolution-go`.
- `make run`: executa a aplicação sem a flag `-dev`.
- `make docker-build` e `make docker-run`: existem como alvos do Makefile e devem ser revisados na etapa Docker.
- `make deps`: baixa e verifica dependências Go.
- `make test`: executa `go test -v ./...`.

### Ambiente esperado pelo Evolution Go

O `.env.example` do projeto define `SERVER_PORT=8080`; a solicitação original pede que qualquer `.env` gerado ou modificado use `SERVER_PORT=9991`. A implementação futura precisa tratar essa divergência explicitamente.

Variáveis importantes já visíveis no projeto:

- `SERVER_PORT` para porta HTTP;
- `POSTGRES_AUTH_DB` e `POSTGRES_USERS_DB`, ou alternativa por `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`;
- `DATABASE_SAVE_MESSAGES`;
- `GLOBAL_API_KEY`;
- `CLIENT_NAME`;
- `CONNECT_ON_STARTUP`;
- `WEBHOOK_URL`;
- opções AMQP, NATS, Minio, proxy, eventos e QR code.

O carregamento de configuração em Go falha se faltarem banco de dados, `DATABASE_SAVE_MESSAGES` ou `GLOBAL_API_KEY`; isso torna a geração de `.env` uma tarefa obrigatória antes de `make dev`.

### Rotas Evolution Go relevantes para substituição do bridge

O mapeamento exato precisa ser validado com payloads e documentação, mas o arquivo de rotas local já mostra candidatos diretos:

| Necessidade Hermes | Candidato Evolution Go |
| --- | --- |
| Health check do serviço | `GET /server/ok` |
| Listar instâncias | `GET /instance/all` |
| Criar instância | `POST /instance/create` |
| Conectar instância | `POST /instance/connect` |
| Status da instância | `GET /instance/status` |
| QR code | `GET /instance/qr` |
| Pareamento | `POST /instance/pair` |
| Desconectar | `POST /instance/disconnect` |
| Reconnect | `POST /instance/reconnect` |
| Enviar texto | `POST /send/text` |
| Enviar mídia | `POST /send/media` |
| Editar mensagem | `POST /message/edit` |
| Presença/digitação | `POST /message/presence` |
| Dados de usuário | `POST /user/info` |
| Contatos | `GET /user/contacts` |
| Grupos do usuário | `GET /group/myall` |

O endpoint de recebimento/polling de novas mensagens não aparece como equivalente direto nas rotas REST listadas. A etapa de integração precisa decidir se o Hermes consumirá eventos por webhook, filas/eventos configurados no Evolution Go, banco, ou outra rota documentada.

## 4. Configuração Hermes atual do WhatsApp

### Fontes de configuração

- `.env`: `WHATSAPP_ENABLED` e `WHATSAPP_MODE` aparecem como variáveis opcionais reconhecidas pelo loader.
- `config.yaml`: há uma seção `whatsapp` no `DEFAULT_CONFIG`, mas hoje ela só documenta o prefixo de resposta; chaves como `require_mention`, `mention_patterns`, `free_response_chats`, `dm_policy`, `allow_from`, `group_policy` e `group_allow_from` são lidas pelo gateway e/ou adapter.
- `gateway.platforms.whatsapp.extra` / `platforms.whatsapp.extra`: é o local já usado para opções específicas do adapter, como `bridge_port`, `bridge_script`, `session_path`, políticas e batching.

### Sobre o “su” mencionado na solicitação

Não encontrei uma chave literal `su` específica do gateway WhatsApp no código atual. As chaves próximas ao requisito são:

- `WHATSAPP_ENABLED`, que habilita o adapter por `.env`;
- `platforms.whatsapp.enabled` ou `gateway.platforms.whatsapp.enabled`, que habilitam por YAML;
- `WHATSAPP_MODE`, que seleciona modo `self-chat`/`bot` para o bridge Node;
- `terminal.backend` / `TERMINAL_ENV`, que podem indicar execução Docker para comandos do agente, mas não são uma configuração específica do serviço Evolution Go.

Para a implementação, a recomendação é introduzir nomes explícitos em `gateway.platforms.whatsapp.extra`, por exemplo `service_backend`, `service_path`, `service_port`, `service_mode`, `docker_enabled`, `api_base_url`, `api_key`, `instance_id` e `startup_command`, evitando reaproveitar uma chave ambígua.

## 5. Pontos mínimos prováveis de alteração

A troca foi concentrada para reduzir risco:

1. `gateway/platforms/whatsapp.py`
   - Adiciona backend Evolution Go como padrão e mantém o bridge Node em `_connect_bridge()` para fallback.
   - Preserva os métodos públicos do adapter: `connect()`, `disconnect()`, `send()`, `edit_message()`, `_send_media_to_bridge()`, `send_typing()`, `get_chat_info()` e o tratamento de eventos.
   - Mantém políticas de acesso e normalização de eventos já existentes.

2. `gateway/config.py`
   - Faz bridge de chaves top-level `whatsapp` para `PlatformConfig.extra`.
   - Preserva `WHATSAPP_ENABLED` como gatilho de habilitação.

3. `hermes_cli/config.py`
   - Adiciona defaults não secretos para Evolution Go e permite env vars específicas da integração.
   - API keys continuam fora dos defaults e devem vir de `.env`/config local segura.

4. `scripts/install.sh` ou fluxo de setup equivalente
   - Se o setup não puder interagir via TUI, documentar/gerar o arquivo final de configuração.
   - Atualizar a lógica que hoje sugere `hermes whatsapp` para pareamento via QR se o pareamento passar a ser feito pelo Evolution Go.

5. Novo suporte ao projeto Go
   - Criar script/cliente leve para garantir `.env` com `SERVER_PORT=9991`.
   - Executar `make build` antes do primeiro `make dev` no modo local.
   - Verificar `GET http://127.0.0.1:9991/server/ok` antes de entregar o adapter como conectado.
   - Implementar caminho Docker depois de revisar a documentação de instalação.

6. `WHATSAPP-IMPLEMENTATION.md`
   - Documentar “antes/depois” de cada alteração real feita no código.

## 6. Lacunas e riscos identificados

- **Recebimento de mensagens:** o bridge atual oferece `GET /messages`; nas rotas Evolution Go locais não há equivalente óbvio. Esse é o maior ponto de descoberta restante para a integração.
- **Modelo de instância:** Evolution Go trabalha com instâncias (`/instance/...`), enquanto o bridge atual usa uma sessão local com `creds.json`. A integração precisará mapear `session_path`/pareamento para `instanceId`/conexão.
- **Autenticação da API:** Evolution Go exige `GLOBAL_API_KEY`; o adapter Hermes hoje não envia API key para o bridge Node local. Será necessário adicionar cabeçalho `apikey`/`Authorization` conforme o middleware do projeto/documentação.
- **Porta padrão divergente:** Hermes bridge atual usa `3000`; `.env.example` Evolution Go usa `8080`; a solicitação exige `9991`.
- **Banco de dados:** Evolution Go requer Postgres ou DSNs configurados; o bridge Node atual não requer Postgres no fluxo Hermes.
- **Docker:** o Hermes possui avisos para backend Docker de execução de comandos, mas isso não equivale automaticamente a rodar o serviço Evolution Go em Docker.
- **Segredos:** `GLOBAL_API_KEY` do `.env.example` é exemplo e não deve ser tratado como segredo de produção.

## 7. Próxima tarefa recomendada

A próxima etapa deve ser **Evolution Go Documentation Route Scraper**:

1. criar o scraper JS puro em `gateway/platforms/whatsapp/` ou em subpasta apropriada;
2. gerar `routes.json` em `gateway/platforms/whatsapp/routes.json`;
3. comparar as rotas documentadas com `pkg/routes/routes.go`;
4. identificar oficialmente o mecanismo de entrada de mensagens/eventos para substituir `GET /messages`.
