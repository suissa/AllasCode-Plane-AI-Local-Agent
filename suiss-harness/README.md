# Suiss Harness

Harness completo com Redis, NATS, Postgres, MongoDb, Milvus, Neo4j, EventStoreDB e Observabilidade (Otel).

## Como iniciar

Certifique-se de que o Docker e o Docker Compose estão instalados.

```bash
cd suiss-harness
docker compose up -d
```

## Mapeamento de Portas

| Serviço | Porta Externa | Porta Interna |
| :--- | :--- | :--- |
| **Redis** | 4004 | 6379 |
| **NATS** | 4005 | 4222 |
| **Postgres** | 4006 | 5432 |
| **MongoDB** | 4007 | 27017 |
| **Milvus** | 4008 | 19530 |
| **Neo4j (HTTP)** | 4009 | 7474 |
| **Neo4j (Bolt)** | 4010 | 7687 |
| **EventStoreDB** | 4011 | 2113 |
| **Prometheus** | 4012 | 9090 |
| **Loki** | 4013 | 3100 |
| **Tempo** | 4014 | 3200 |
| **Grafana** | 4015 | 3000 |
| **Otel Collector (gRPC)** | 4016 | 4317 |
| **Otel Collector (HTTP)** | 4017 | 4318 |
| **Debezium Server** | 4018 | 8080 |

## Stack de Observabilidade

O **OpenTelemetry Collector** está disponível nas portas **4016 (gRPC)** e **4017 (HTTP)**.
As aplicações devem enviar seus dados OTLP para esses endpoints.

O **Grafana** pode ser acessado em `http://localhost:4015` com login anônimo de Admin habilitado.
Os datasources para Prometheus, Loki e Tempo já vêm pré-configurados.
