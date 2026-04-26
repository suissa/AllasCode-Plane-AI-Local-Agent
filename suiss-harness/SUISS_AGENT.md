# SuissAgent ☤

Este é o **SuissAgent**, um harness completo projetado para arquiteturas de alto desempenho que utilizam **CQRS (Command Query Responsibility Segregation)**, **Event Sourcing** e **CDC (Change Data Capture)**.

## Arquitetura: CQRS Cabuloso

O SuissAgent utiliza uma abordagem poliglota para persistência de dados, garantindo que cada componente seja otimizado para sua responsabilidade específica:

1.  **Escrita (Command Side):**
    *   **EventStoreDB**: Atua como o Source of Truth (Single Source of Truth), armazenando todos os estados como uma sequência imutável de eventos.
    *   **Postgres**: Utilizado para snapshots de estado e persistência relacional onde a integridade referencial é crítica.

2.  **Leitura (Query Side):**
    *   **MongoDB**: Projeções otimizadas para leitura rápida de documentos e visualizações complexas.
    *   **Neo4j**: Armazena relações complexas para consultas de grafos e análise de rede.
    *   **Milvus**: Banco de dados vetorial para busca semântica e integração com LLMs (IA).

3.  **Mensageria e Streaming:**
    *   **NATS (JetStream)**: Backbone de mensageria para distribuição de eventos e desacoplamento de serviços.
    *   **Debezium**: Implementa CDC (Change Data Capture) monitorando o Postgres e transmitindo alterações para o NATS.

4.  **Performance:**
    *   **Redis**: Camada de cache ultra-rápida para dados voláteis e redução de latência.

## Observabilidade (OpenTelemetry)

O SuissAgent é nativamente integrado com **OpenTelemetry**. O stack de observabilidade (LGTM) está configurado para coletar e correlacionar:

*   **Métricas**: Prometheus
*   **Logs**: Loki
*   **Traces**: Tempo
*   **Visualização**: Grafana

O **Otel Collector** centraliza o recebimento de dados via OTLP (gRPC/HTTP) e os distribui para os respectivos backends.
