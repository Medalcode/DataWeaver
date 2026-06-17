# Agents — Agentes de Procesamiento Asíncrono

> **Versión del documento**: 1.0  
> **Referencia de código**: [`backend/app/tasks/`](../backend/app/tasks/)

---

## ¿Qué es un Agente?

En la arquitectura de DataWeaver, un **agente** es un **worker Celery** que consume tareas de la cola Redis y las ejecuta de forma desacoplada del ciclo de vida HTTP. Los agentes son la pieza que hace posible el procesamiento asíncrono de archivos Excel sin bloquear la API.

```
Cliente HTTP
    │  POST /executions
    ▼
FastAPI (API Layer)
    │  1. Crea registro Execution (status=pending)
    │  2. Encola tarea en Redis
    │  3. Devuelve execution_id al cliente
    ▼
Redis (Broker)
    │  Cola: execute_workflow
    ▼
Celery Worker (Agente)
    │  Consume la tarea
    │  Ejecuta el motor de reglas
    │  Persiste logs y outputs
    ▼
PostgreSQL + File System
```

---

## Agente Generalista: The Weaver (Orquestador)

| Atributo           | Valor                                                                 |
|--------------------|-----------------------------------------------------------------------|
| **Nombre de tarea**| `execute_workflow`                                                    |
| **Rol**            | **Orquestador Central** de Procesamiento                              |
| **Módulo**         | `app.tasks.workflow_execution`                                        |
| **Versatilidad**   | Alta (Capaz de ejecutar cualquier lógica definida via Skills)          |

### Responsabilidades y Densidad

Para evitar la fragmentación, este agente actúa como un **contexto de ejecución universal**. No se deben crear agentes adicionales para transformaciones específicas; en su lugar, se deben parametrizar las Skills que este agente consume.

1. **Gestión de Estado**: Controla el ciclo `pending → running → success/failed`.
2. **Abstracción de Datos**: Carga, valida y persiste archivos sin importar la complejidad de las reglas internas.
3. **Dispatcher**: Inyecta el `ExecutionContext` en el motor de reglas de forma agnóstica.

---

## Ciclo de Vida de una Ejecución

```
                   ┌──────────┐
                   │  pending │  ← creado por la API
                   └────┬─────┘
                        │ agente consume la tarea
                   ┌────▼─────┐
                   │  running  │  ← execution.started_at = ahora
                   └────┬─────┘
              ┌─────────┴──────────┐
      OK       │                   │  Error / excepción
         ┌─────▼─────┐       ┌─────▼──────┐
         │  success  │       │   failed   │
         └─────┬─────┘       └─────┬──────┘
               │                   │
         execution.finished_at   execution.error_message
         output files creados
```

### Estados

| Estado    | Descripción                                      | Transición desde |
|-----------|--------------------------------------------------|------------------|
| `pending` | Tarea encolada, esperando un worker disponible   | API (POST)       |
| `running` | Worker procesando el archivo                     | `pending`        |
| `success` | Procesamiento completado, outputs disponibles    | `running`        |
| `failed`  | Error durante la ejecución, revisar `error_message` | `running`     |

---

## Configuración

### Variables de Entorno

| Variable                | Descripción                                      | Valor por defecto / Ejemplo      |
|-------------------------|--------------------------------------------------|----------------------------------|
| `CELERY_BROKER_URL`     | URL del broker Redis                             | `redis://localhost:6379/0`       |
| `CELERY_RESULT_BACKEND` | Backend para resultados de tareas                | `redis://localhost:6379/0`       |
| `DATABASE_URL`          | Conexión a PostgreSQL                            | `postgresql://user:pass@db/app`  |
| `UPLOAD_DIR`            | Directorio de archivos temporales                | `/tmp/uploads`                   |
| `FILE_EXPIRATION_HOURS` | Horas hasta expiración de archivos de salida     | `24`                             |

### Iniciar un Worker

```bash
# Desarrollo (1 worker, 1 proceso)
celery -A app.tasks.celery_app worker --loglevel=info

# Producción (4 procesos concurrentes)
celery -A app.tasks.celery_app worker --loglevel=warning --concurrency=4

# Con prefetch desactivado (recomendado para tareas largas)
celery -A app.tasks.celery_app worker --loglevel=warning --concurrency=4 --prefetch-multiplier=1
```

### Docker Compose

```yaml
# Fragmento relevante del docker-compose.yml
celery:
  build: .
  command: celery -A app.tasks.celery_app worker --loglevel=warning --concurrency=4
  environment:
    - CELERY_BROKER_URL=redis://redis:6379/0
    - DATABASE_URL=postgresql://user:pass@postgres/dataweaver
  depends_on:
    - redis
    - postgres
  volumes:
    - ./uploads:/tmp/uploads
```

---

## Escalabilidad

### Escalado Horizontal

Los workers Celery son **stateless**: no guardan estado local entre tareas. Puedes arrancar N workers en paralelo sin coordinación adicional.

```
Load Balancer (nginx / HAProxy)
        │
   ┌────┴────┐
   │   API   │  ×N instancias
   └────┬────┘
        │ Redis broker
   ┌────┴──────────────────────────┐
   │  Worker 1  Worker 2  Worker N │
   └───────────────────────────────┘
```

**Regla de escalado**: Monitoriza la longitud de la cola con Flower. Si la cola supera `X` tareas pendientes de forma sostenida, agrega más workers.

### Colas Dedicadas (Queue Partitioning)

Para separar cargas de trabajo (p. ej., archivos grandes vs. pequeños):

```bash
# Worker especializado en archivos grandes
celery -A app.tasks.celery_app worker -Q heavy --concurrency=2 --prefetch-multiplier=1

# Worker para tareas rápidas
celery -A app.tasks.celery_app worker -Q default --concurrency=8
```

Enrutar la tarea a la cola adecuada:

```python
execute_workflow_task.apply_async(args=[...], queue="heavy")
```

---

## Manejo de Errores y Reintentos

### Comportamiento Actual

La tarea `execute_workflow_task` está configurada con reintentos automáticos. En errores transitorios se reintenta hasta 3 veces con un retardo de 60 segundos entre intentos. Los errores permanentes marcan la ejecución como `failed` sin reintentar.

```python
@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    acks_late=True,
    reject_on_worker_lost=True,
    soft_time_limit=3600,
    time_limit=3900,
)
def execute_workflow_task(self, execution_id, workflow_version_id, input_file_id):
    ...
    except Exception as e:
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        execution.status = "failed"
        ...
```

| Configuración | Valor | Propósito |
|---|---|---|
| `max_retries=3` | 3 | Reintentos máximos antes de falla permanente |
| `default_retry_delay=60` | 60s | Espera entre reintentos |
| `acks_late=True` | — | No confirma el mensaje hasta que la tarea termina |
| `reject_on_worker_lost=True` | — | Reencola si el worker falla inesperadamente |
| `soft_time_limit=3600` | 1h | Tiempo máximo de ejecución (señal suave) |
| `time_limit=3900` | 1h 5m | Tiempo máximo de ejecución (matar worker) |

### Dead Letter Queue

Los mensajes que agotan sus reintentos se marcan automáticamente como `failed` en la base de datos (`execution.status = 'failed'`) con el mensaje de error almacenado en `execution.error_message`. El worker rechaza el mensaje (`reject_on_worker_lost=True`) para que el broker pueda encolarlo en una DLQ si está configurada.

---

## Observabilidad

### Flower — Dashboard de Monitoreo

```bash
# Instalar y arrancar
pip install flower
celery -A app.tasks.celery_app flower --port=5555

# Acceder en
open http://localhost:5555
```

Flower expone:
- Estado de workers en tiempo real
- Historial de tareas (success / failed / retry)
- Longitud de colas
- Throughput y tiempos de ejecución

### Métricas Recomendadas (Prometheus + Grafana)

Instala [`celery-exporter`](https://github.com/danihodovic/celery-exporter) para exportar métricas a Prometheus:

| Métrica                             | Descripción                               |
|-------------------------------------|-------------------------------------------|
| `celery_tasks_total{state="success"}` | Total de tareas completadas              |
| `celery_tasks_total{state="failure"}` | Total de tareas fallidas                 |
| `celery_task_duration_seconds`      | Histograma de duración de ejecución       |
| `celery_workers_online`             | Número de workers activos                 |
| `celery_queue_length`               | Tareas pendientes en cola                 |

### Alertas Recomendadas

| Condición                                   | Severidad | Acción                                |
|---------------------------------------------|-----------|---------------------------------------|
| `celery_queue_length > 50` por >5 min       | Warning   | Escalar workers                       |
| `celery_tasks_total{state="failure"}` > 5%  | Critical  | Revisar logs de ejecución             |
| `celery_workers_online == 0`                | Critical  | Reiniciar servicio worker             |
| Worker sin heartbeat por >60s               | Critical  | Alerta de worker caído                |

### Logging Estructurado

Configura el worker con logging JSON para facilitar la ingesta en herramientas como Datadog o Loki:

```bash
celery -A app.tasks.celery_app worker \
  --logfile=/var/log/dataweaver/celery.log \
  --loglevel=info
```

Cada paso del motor genera una entrada en `execution_logs` (PostgreSQL) con:
- `step_index` — posición dentro del workflow
- `step_type` — tipo de skill ejecutado
- `message` — descripción legible de la acción
- `affected_rows` — filas afectadas por el paso

---

## Cookbook: Añadir un Nuevo Agente / Tarea

### Paso 1 — Crear la tarea Celery

```
backend/app/tasks/my_task.py
```

```python
from app.tasks import celery_app
from app.database import SessionLocal


@celery_app.task(name="my_new_task")
def my_new_task(param_1: str, param_2: int):
    """Descripción del agente."""
    db = SessionLocal()
    try:
        # lógica de negocio
        pass
    except Exception as e:
        raise
    finally:
        db.close()
```

### Paso 2 — Registrar la importación

Importar la tarea en `backend/app/tasks/__init__.py` para que Celery la autodiscover:

```python
from app.tasks.workflow_execution import execute_workflow_task
from app.tasks.my_task import my_new_task  # ← añadir
```

### Paso 3 — Encolar desde la API

```python
from app.tasks.my_task import my_new_task

my_new_task.delay(param_1="value", param_2=42)
# o con opciones avanzadas:
my_new_task.apply_async(args=["value", 42], queue="default", countdown=10)
```

### Paso 4 — Tests

```python
# tests/test_my_task.py
from unittest.mock import patch
from app.tasks.my_task import my_new_task

def test_my_task_success():
    with patch("app.tasks.my_task.SessionLocal") as mock_db:
        result = my_new_task("value", 42)
        assert result is not None
```

---

## Referencias

| Recurso                         | Ruta                                                                          |
|---------------------------------|-------------------------------------------------------------------------------|
| Tarea principal de ejecución    | [`backend/app/tasks/workflow_execution.py`](../backend/app/tasks/workflow_execution.py) |
| Configuración Celery            | [`backend/app/tasks/__init__.py`](../backend/app/tasks/__init__.py)           |
| Motor de reglas                 | [`backend/app/engine/engine.py`](../backend/app/engine/engine.py)             |
| Modelos de BD (`Execution`, `ExecutionLog`) | [`backend/app/models.py`](../backend/app/models.py)               |
| Configuración de la app         | [`backend/app/config.py`](../backend/app/config.py)                           |
| Docker Compose                  | [`docker-compose.yml`](../docker-compose.yml)                                 |
| Catálogo de Skills              | [`docs/skills.md`](skills.md)                                                 |
| Arquitectura general            | [`docs/ARCHITECTURE.md`](ARCHITECTURE.md)                                     |
