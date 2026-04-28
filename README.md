# Rüpü Gateway - Document Processing Pipeline

Sistema de orquestación de procesamiento de documentos basado en microservicios, diseñado para ser resiliente, escalable y asíncrono.

## Arquitectura

El sistema utiliza un diseño orientado a eventos para separar la recepción de documentos de su procesamiento intensivo:

1.  **API (FastAPI & gRPC):** Recibe las solicitudes y persiste el "Job" en una base de datos SQLite. Expone tanto una interfaz REST tradicional como un servicio gRPC de alto rendimiento (compartiendo la misma lógica de negocio).
2.  **Message Broker (RabbitMQ):** Actúa como buffer y distribuidor de tareas.
    *   Cola `tasks`: Órdenes directas de procesamiento para los Workers.
    *   Exchange `events_exchange` (Fanout): Patrón Pub/Sub que implementa **Consumer Groups**. Permite que múltiples sistemas (o réplicas de un mismo sistema) escuchen las notificaciones de estado de forma balanceada y persistente.
3.  **Worker (Python):** Consumidor asíncrono que ejecuta el pipeline de procesamiento (Extracción -> Análisis -> Enriquecimiento) utilizando un sistema de inyección de dependencias para los proveedores.
4.  **Logger Consumer:** Un servicio downstream de ejemplo que escucha los eventos del pipeline a través de su propio consumer group, demostrando el desacoplamiento del sistema.


## Tecnologías

*   **Lenguaje:** Python 3.10+
*   **Framework API:** FastAPI
*   **RPC:** gRPC (grpcio)
*   **Base de Datos:** SQLAlchemy + SQLite
*   **Messaging:** RabbitMQ + Pika
*   **Contenedores:** Docker & Docker Compose

## Cómo ejecutar

1.  Tener Docker instalado.
2.  Levanta la infraestructura completa (API, Worker, Logger, gRPC y RabbitMQ):
    ```bash
    docker compose up --build -d
    ```
3.  **Para REST:** La API estará disponible en `http://localhost:8000`. Podes probarla usando la documentación interactiva Swagger en `http://localhost:8000/docs`.
4.  **Para ver eventos en tiempo real:** Puedes seguir los logs del grupo de consumidores downstream:
    ```bash
    docker compose logs -f gateway-logger
    ```

**Para ejecutar todos los tests (REST & Pipeline):**
```bash
docker compose exec gateway-api pytest
```

**Para probar el servidor gRPC :**
Incluido un script cliente de prueba que se conecta al servidor gRPC interno de Docker, crea un Job y luego consulta su estado.
```bash
docker compose exec gateway-api python src/grpc/client_test.py
```
