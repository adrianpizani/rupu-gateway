# ToMS - LangChain LLM Microservice

> **ToMS** (Transformation of MicroService): Plan de transformación de Rüpü Gateway a un microservicio de procesamiento LLM con LangChain y servicios asíncronos.

---

## 📋 Análisis del Proyecto Actual

**Rüpü Gateway** es un pipeline de procesamiento de documentos con:

| Componente | Tecnología Actual |
|---|---|
| API REST | FastAPI |
| RPC | gRPC (bonus implementado) |
| Base de datos | SQLite + SQLAlchemy |
| Async messaging | RabbitMQ + Pika (`BlockingConnection`) |
| Workers | Consumidor RabbitMQ síncrono que ejecuta `asyncio.run()` |
| Proveedores | Mocks que simulan latencia (Extract, Analyze, Enrich) |
| Resiliencia | Retry con exponential backoff (3 intentos) |
| Testing | pytest + pytest-asyncio + TestClient FastAPI |
| Orquestación | Docker Compose (4 servicios: API, Worker, Logger, gRPC) |

### Arquitectura Actual

```
┌─────────────┐    ┌──────────────────────────────────────────┐
│   Cliente    │    │         Rüpü Gateway                     │
│  (REST/gRPC) │───►│                                          │
└─────────────┘    │  ┌────────┐    ┌──────────────────────┐  │
                   │  │ FastAPI │    │   Worker (síncrono)  │  │
                   │  │  REST   │    │                      │  │
                   │  └───┬─────┘    │  ┌────────────────┐ │  │
                   │      │          │  │ Mock Providers  │ │  │
                   │  ┌───▼─────┐    │  │ - FastExtractor │ │  │
                   │  │  gRPC   │    │  │ - SlowExtractor │ │  │
                   │  │ Server  │    │  │ - Analyzer      │ │  │
                   │  └───┬─────┘    │  │ - Enricher      │ │  │
                   │      │          │  └────────────────┘ │  │

## 🎯 Objetivo

Convertir Rüpü Gateway en un microservicio especializado en:

- **Orquestación de chains de LangChain** como pipeline de procesamiento
- **Inferencia directa** vía API REST/Streaming
- **Procesamiento asíncrono** de jobs LLM con colas de trabajo
- **Soporte multi-modelo** (OpenAI, Anthropic, Ollama para modelos locales)
- **Event-driven** con publicación de resultados para sistemas downstream

---

## 🏗️ Arquitectura Propuesta

```
┌─────────────┐    ┌──────────────────────────────────────────────────┐
│   Cliente    │    │           ToMS - LangChain LLM Service           │
│  (REST/gRPC) │───►│                                                  │
└─────────────┘    │  ┌──────────┐  ┌─────────────────────────────┐   │
                   │  │ FastAPI   │  │    Async Worker Pool         │   │
                   │  │ REST + SSE│  │                             │   │
                   │  └───┬───────┘  │  ┌───────────────────────┐  │   │
                   │      │          │  │   LangChain Chains     │  │   │
                   │  ┌───▼──────┐   │  │                       │  │   │
                   │  │  gRPC    │   │  │  ┌─────────────────┐  │  │   │
                   │  │ Server   │   │  │  │ ExtractionChain  │  │  │   │
                   │  └───┬──────┘   │  │  │ (info structure) │  │  │   │
                   │      │          │  │  ├─────────────────┤  │  │   │
                   │  ┌───▼──────────────────┐              │  │  │   │
                   │  │     RabbitMQ         │  │  AnalysisChain   │  │   │
                   │  │    (aio-pika)        │  │  (sentimiento,   │  │   │
                   │  │  tasks + events      │  │   entidades)     │  │   │
                   │  └──────────────────────┘  ├─────────────────┤  │   │
                   │                           │  EnrichmentChain │  │   │
                   │                           │  (enriquecer)   │  │   │
                   │                           └────────┬────────┘  │   │
                   │                                    │            │   │
                   │                           ┌────────▼────────┐  │   │
                   │                           │  LLM Providers   │  │   │
                   │                           │  ┌──────────┐   │  │   │
                   │                           │  │ OpenAI   │   │  │   │
                   │                           │  ├──────────┤   │  │   │
                   │                           │  │ Anthropic│   │  │   │
                   │                           │  ├──────────┤   │  │   │
                   │                           │  │ Ollama   │   │  │   │
                   │                           │  └──────────┘   │  │   │
                   │                           └─────────────────┘  │   │
                   └──────────────────────────────────────────────────┘
                                        │
                              ┌─────────▼─────────┐
                              │   Downstream        │
                              │   Consumers         │
                              │   (Logger, Webhook) │
                              └───────────────────┘
```


---

## 📦 Estructura de Directorios Propuesta

```
rupu-gateway/
├── src/
│   ├── __init__.py
│   ├── main.py                          # FastAPI app (punto de entrada)
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── schemas.py                   # Schemas Pydantic extendidos
│   │   ├── routes_jobs.py               # Endpoints REST de jobs
│   │   └── routes_llm.py               # [NUEVO] Endpoints LLM directos (chat, stream)
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py                    # Settings con LLM configs
│   │   ├── job_service.py              # Lógica de negocio de jobs
│   │   └── pipeline.py                 # Orquestador de pipeline (actualizado)
│   │
│   ├── llm/                             # [NUEVO] Módulo LangChain
│   │   ├── __init__.py
│   │   ├── chains/
│   │   │   ├── __init__.py
│   │   │   ├── base.py                 # Chain base abstracta
│   │   │   ├── extraction_chain.py     # Extracción estructurada con LLM
│   │   │   ├── analysis_chain.py       # Análisis con LLM
│   │   │   └── enrichment_chain.py     # Enriquecimiento con LLM
│   │   ├── providers/
│   │   │   ├── __init__.py
│   │   │   ├── factory.py             # Fábrica de providers LLM
│   │   │   └── models.py              # Configs de modelos (OpenAI, Anthropic, Ollama)
│   │   └── streaming/
│   │       ├── __init__.py
│   │       └── handlers.py            # Manejo de streaming SSE
│   │
│   ├── messaging/
│   │   ├── __init__.py
│   │   ├── publisher.py                # Publisher síncrono (legacy)
│   │   ├── async_publisher.py          # [NUEVO] Publisher async con aio-pika
│   │   ├── worker.py                   # Worker síncrono (legacy)
│   │   ├── async_worker.py            # [NUEVO] Worker 100% async
│   │   └── logger_consumer.py          # Consumer downstream (legacy)
│   │
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── base.py                     # BaseProvider (se mantiene para compatibilidad)
│   │   ├── extractors.py              # Extractors mock (legacy)
│   │   ├── analyzers.py               # Analyzers mock (legacy)
│   │   └── enrichers.py               # Enrichers mock (legacy)
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── database.py                 # SQLAlchemy engine
│   │   └── job.py                      # Modelo Job (extendido)
│   │
│   └── grpc/
│       ├── gateway.proto
│       ├── gateway_pb2.py
│       ├── gateway_pb2_grpc.py
│       ├── server.py
│       └── client_test.py

---

## 🔄 Fases de Implementación

### Fase 0: Preparación y Dependencias

**Objetivo:** Preparar el entorno con las nuevas librerías.

**Tareas:**
1. Agregar dependencias a `requirements.txt`:
   ```txt
   langchain>=0.3.0
   langchain-community>=0.3.0
   langchain-openai>=0.2.0
   langchain-anthropic>=0.2.0
   aio-pika>=9.0.0
   sse-starlette>=2.0.0
   ```
2. Crear directorios: `src/llm/chains/`, `src/llm/providers/`, `src/llm/streaming/`
3. Extender `Settings` en `config.py` con variables para múltiples LLM

**Archivos a modificar:**
- `requirements.txt`
- `src/core/config.py`

**Criterio de éxito:** `pip install -r requirements.txt` se completa sin errores.

---

### Fase 1: Configuración Multi-Modelo

**Objetivo:** Soportar múltiples proveedores LLM configurables por entorno.

**Tareas:**
1. Crear `src/llm/providers/models.py` con:
   - Enum de proveedores: `OPENAI`, `ANTHROPIC`, `OLLAMA`
   - Función `get_llm(model_config)` que retorna el LLM correcto
   - Configuración vía variables de entorno (API keys, endpoints, modelos)

2. Crear `src/llm/providers/factory.py` con:
   - Fábrica de LLMs basada en el nombre del modelo/provider
   - Cache de instancias para reutilizar conexiones

**Archivos a crear:**
- `src/llm/__init__.py`
- `src/llm/providers/__init__.py`
- `src/llm/providers/models.py`
- `src/llm/providers/factory.py`

---

### Fase 2: LangChain Chains como Providers

**Objetivo:** Reemplazar los mocks con chains de LangChain que usan LLMs reales.

**Tareas:**

1. Crear `src/llm/chains/base.py`:
   ```python
   from abc import ABC, abstractmethod
   from langchain_core.language_models import BaseLanguageModel
   
   class BaseLLMChain(ABC):
       def __init__(self, llm: BaseLanguageModel):
           self.llm = llm
       
       @abstractmethod
       async def process(self, data: str) -> str:
           pass
   ```

2. Crear `src/llm/chains/extraction_chain.py`:
   - Extrae información estructurada del texto usando un LLM
   - Ejemplo: extraer nombre, fecha, entidades, resumen
   - Usa `StrOutputParser` + `ChatPromptTemplate`

3. Crear `src/llm/chains/analysis_chain.py`:
   - Analiza sentimiento, categoriza el texto
   - Detecta entidades nombradas (NER)
   - Retorna JSON estructurado

4. Crear `src/llm/chains/enrichment_chain.py`:
   - Enriquece el análisis con contexto adicional
   - Genera metadatos, tags, descripciones

5. Adaptar `src/core/pipeline.py`:
   - Agregar flag `use_llm` en pipeline_config
   - Si `use_llm=True`, usa LangChain chains en lugar de providers mock
   - Mantener compatibilidad con providers mock como fallback

**Archivos a crear:**
- `src/llm/chains/__init__.py`
- `src/llm/chains/base.py`
- `src/llm/chains/extraction_chain.py`
- `src/llm/chains/analysis_chain.py`
- `src/llm/chains/enrichment_chain.py`

**Archivos a modificar:**
- `src/core/pipeline.py` (agregar soporte LLM)
- `src/api/schemas.py` (extender PipelineConfig con flag `use_llm`)

**Ejemplo de ExtractionChain:**

```python
# src/llm/chains/extraction_chain.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from src.llm.chains.base import BaseLLMChain

EXTRACTION_PROMPT = ChatPromptTemplate.from_messages([
    ("system", "Eres un extractor de información. Extrae del texto: "
               "1) Tema principal, 2) Entidades (personas, lugares, organizaciones), "
               "3) Fechas mencionadas, 4) Resumen de 1 oración. "
               "Responde en formato JSON."),
    ("human", "{text}")
])

class ExtractionChain(BaseLLMChain):
    async def process(self, data: str) -> str:
        chain = EXTRACTION_PROMPT | self.llm | StrOutputParser()
        return await chain.ainvoke({"text": data})
```


**Ejemplo de configuración:**

```python
# src/llm/providers/models.py
from enum import Enum
from pydantic import BaseModel

class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"

class LLMConfig(BaseModel):
    provider: LLMProvider = LLMProvider.OPENAI
    model: str = "gpt-4o-mini"
    temperature: float = 0.0
    max_tokens: int = 4096
    api_key: str | None = None
    base_url: str | None = None
```

│
├── tests/
│   ├── conftest.py
│   ├── test_api_jobs.py
│   ├── test_core_jobs.py
│   ├── test_pipeline.py
│   ├── test_providers.py
│   ├── test_resilience.py
│   ├── test_messaging_integration.py
│   ├── test_e2e_flow.py
│   ├── test_llm_chains.py             # [NUEVO] Tests de chains LangChain
│   ├── test_llm_api.py                # [NUEVO] Tests de endpoints LLM
│   └── test_async_messaging.py        # [NUEVO] Tests de messaging async
│
├── Dockerfile
├── docker-compose.yml                  # Actualizado con nuevos servicios
├── requirements.txt                    # Actualizado con LangChain, aio-pika
├── CHALLENGE.md
├── README.md
└── ToMS-LangChain-LLM.md              # ← Este archivo
```

                   │  ┌───▼──────────┐                     │  │
                   │  │   RabbitMQ   │                     │  │
                   │  │  (pika sync) │                     │  │
                   │  └──────────────┘                     │  │
                   └──────────────────────────────────────────┘
                                        │
                              ┌─────────▼─────────┐
                              │   Logger Consumer  │
                              │   (downstream)     │
                              └───────────────────┘
```

### Puntos Clave a Transformar

| # | Problema Actual | Solución Propuesta |
|---|---|---|
| 1 | Providers mock con latencia fija | **Chains de LangChain** con LLMs reales (OpenAI, Anthropic, Ollama) |
| 2 | `pika.BlockingConnection` (bloqueante) | **`aio-pika`** para RabbitMQ 100% asíncrono |
| 3 | Worker usa `asyncio.run()` en callback síncrono | **AsyncWorker** nativo con `asyncio` |
| 4 | Sin soporte para streaming | **SSE (Server-Sent Events)** para respuestas LLM en tiempo real |
| 5 | Sin observabilidad LLM | **Tracing** con LangSmith, logging de tokens/latencia |
| 6 | Sin configuración de modelos | **Settings extensibles** para múltiples proveedores LLM |
