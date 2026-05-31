# WhatsApp Implementation: Evolution Go API Backend

## O que mudou

O gateway WhatsApp do Hermes agora usa a API Evolution Go local como backend padrão. A classe pública continua sendo `WhatsAppAdapter` em `gateway/platforms/whatsapp.py`, então o restante do gateway continua chamando os mesmos métodos (`connect`, `send`, `edit_message`, envio de mídia, digitação e webhook/event handling).

## Antes

- O adapter exigia Node.js em `check_whatsapp_requirements()`.
- `connect()` iniciava o bridge Node.js em `scripts/whatsapp-bridge/bridge.js`.
- A porta padrão do bridge era `3000`.
- O bridge exigia `creds.json` em `$HERMES_HOME/whatsapp/session`.
- Entrada de mensagens vinha de polling em `GET /messages`.
- Saída usava endpoints locais do bridge: `/send`, `/edit`, `/send-media`, `/typing` e `/chat/{chat_id}`.

## Agora

- O backend padrão é `evolution`.
- O fallback legado continua disponível com `whatsapp.backend: bridge` ou `WHATSAPP_GATEWAY_BACKEND=bridge`.
- `connect()` garante `.env` do projeto Evolution Go, força `SERVER_PORT=9991`, verifica `GET /server/ok` e, se necessário, executa `make build` seguido de `make dev` em `gateway/platforms/whatsapp/`.
- O adapter cria/conecta uma instância Evolution Go usando `/instance/create` e `/instance/connect`.
- Mensagens de entrada chegam por webhook local do Hermes e são normalizadas para `MessageEvent`.
- Envio de texto usa `POST /send/text`.
- Edição usa `POST /message/edit`.
- Mídia usa `POST /send/media`.
- Digitação/presença usa `POST /message/presence`.

## Configuração

Opções não secretas podem ficar em `config.yaml` na seção `whatsapp` ou em `gateway.platforms.whatsapp.extra`:

```yaml
whatsapp:
  backend: evolution
  service_port: 9991
  api_base_url: http://127.0.0.1:9991
  instance_id: hermes
  instance_name: Hermes
  auto_start: true
  build_on_start: true
  webhook_host: 127.0.0.1
  webhook_port: 9992
  webhook_path: /webhook/evolution
```

Segredos como a API key devem ficar fora do repositório, por exemplo em `~/.hermes/.env`:

```bash
WHATSAPP_ENABLED=true
WHATSAPP_EVOLUTION_API_KEY=...
WHATSAPP_EVOLUTION_INSTANCE_TOKEN=...
```

## Arquivos alterados

- `gateway/platforms/whatsapp.py`: adiciona o cliente/launcher Evolution Go, webhook local, mapeamento de endpoints e fallback legado.
- `gateway/config.py`: propaga chaves `whatsapp.*` para `PlatformConfig.extra`.
- `hermes_cli/config.py`: adiciona defaults não secretos do backend Evolution Go e permite env vars específicas.
- `tests/gateway/test_whatsapp_evolution.py`: cobre `.env` com `SERVER_PORT=9991`, envio por `/send/text` e normalização de webhook.
