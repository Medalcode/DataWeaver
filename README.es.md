# Macro Builder

> **Plataforma de automatización Excel de bajo código para usuarios de negocio**

Transforma tareas repetitivas de Excel en flujos de trabajo automatizados sin escribir código VBA. Define reglas de negocio visualmente y deja que el sistema maneje la ejecución.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.109.0-009688.svg?style=flat&logo=FastAPI)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=flat&logo=python)](https://www.python.org)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1.svg?style=flat&logo=postgresql)](https://www.postgresql.org)
[![Celery](https://img.shields.io/badge/Celery-5.3-37814A.svg?style=flat&logo=celery)](https://docs.celeryq.dev)

[English](README.md) | **Español**

## 🎯 Problema

Las organizaciones enfrentan desafíos críticos con la automatización de Excel:

- **Dependencia de conocimiento**: Procesos atrapados en macros VBA conocidas solo por empleados específicos
- **Pesadilla de mantenimiento**: Pequeños cambios requieren reescribir macros completas
- **Riesgo de continuidad**: Cuando la "persona de Excel" se va, la automatización se detiene
- **Sin auditoría**: Macros de caja negra sin transparencia alguna

## 💡 Solución

Macro Builder convierte la lógica de negocio en **flujos de trabajo declarativos y versionables** que cualquiera puede crear y mantener.

### Propuestas de Valor Principales

✅ **Sin programación** - Constructor de reglas visual con descripciones en lenguaje natural  
✅ **Auditoría completa** - Cada ejecución registrada con detalles paso a paso  
✅ **Control de versiones** - Rastrea cambios, revierte y compara versiones de flujos  
✅ **Multi-tenant** - Aislamiento seguro por empresa con acceso basado en roles  
✅ **Escalable** - Ejecución asíncrona maneja archivos grandes eficientemente  

## 🏗️ Arquitectura

### Diseño del Sistema

```
┌─────────────┐
│   React UI  │ (Constructor de Reglas)
└──────┬──────┘
       │ HTTPS/REST
┌──────┴──────────────────────────┐
│       Backend FastAPI            │
│  ┌────────────┐  ┌────────────┐ │
│  │    Auth    │  │  Motor de  │ │
│  │   (JWT)    │  │  Workflow  │ │
│  └────────────┘  └────────────┘ │
└──────┬────────────────┬──────────┘
       │                │
┌──────┴──────┐  ┌──────┴──────┐
│ PostgreSQL  │  │   Celery    │
│ (Metadatos) │  │  (Async)    │
└─────────────┘  └──────┬──────┘
                        │
                 ┌──────┴──────┐
                 │    Redis    │
                 └─────────────┘
```

### Componentes Clave

| Componente | Tecnología | Propósito |
|-----------|-----------|---------|
| **Capa API** | FastAPI | Endpoints REST, validación, autenticación |
| **Motor de Reglas** | Python + Pandas | Lógica de ejecución de flujos |
| **Cola de Tareas** | Celery + Redis | Procesamiento asíncrono de trabajos |
| **Base de Datos** | PostgreSQL | Persistencia multi-tenant |
| **Almacenamiento** | Sistema de archivos | Almacenamiento temporal de Excel |

## 🚀 Inicio Rápido

### Prerequisitos

- Docker & Docker Compose
- Python 3.11+ (para desarrollo local)

### Ejecutar con Docker

```bash
# Clonar repositorio
git clone https://github.com/Medalcode/DataWeaver.git
cd DataWeaver

# Iniciar todos los servicios
docker-compose up -d

# Verificar salud
curl http://localhost:8000/health

# Acceder a documentación API
open http://localhost:8000/docs
```

La API estará disponible en `http://localhost:8000`

### Desarrollo Local

```bash
# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env

# Iniciar PostgreSQL y Redis
docker-compose up -d postgres redis

# Ejecutar migraciones
alembic upgrade head

# Iniciar servidor API
uvicorn app.main:app --reload

# En otra terminal, iniciar worker Celery
celery -A app.tasks.celery_app worker --loglevel=info
```

## 📖 Uso de la API

### 1. Registrar Usuario

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "usuario@empresa.com",
    "password": "contraseña_segura",
    "company_name": "Mi Empresa"
  }'
```

### 2. Iniciar Sesión

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -F "username=usuario@empresa.com" \
  -F "password=contraseña_segura"
```

Respuesta:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

### 3. Subir Archivo Excel

```bash
curl -X POST http://localhost:8000/api/v1/files/upload \
  -H "Authorization: Bearer {token}" \
  -F "file=@datos_ventas.xlsx"
```

La respuesta muestra las columnas disponibles:
```json
{
  "file_id": "uuid",
  "filename": "datos_ventas.xlsx",
  "columns": ["Fecha", "Producto", "Monto", "Estado"]
}
```

### 4. Crear Flujo de Trabajo

```bash
curl -X POST http://localhost:8000/api/v1/workflows \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Reporte Mensual de Ventas",
    "description": "Filtrar y agregar datos de ventas"
  }'
```

### 5. Crear Versión de Flujo (Definir Reglas)

```bash
curl -X POST http://localhost:8000/api/v1/workflows/{workflow_id}/versions \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "rules": {
      "steps": [
        {
          "type": "filter",
          "column": "Estado",
          "operator": "=",
          "value": "Aprobado"
        },
        {
          "type": "group_sum",
          "group_by": "Producto",
          "field": "Monto",
          "target_sheet": "Resumen_Productos"
        }
      ]
    }
  }'
```

### 6. Ejecutar Flujo de Trabajo

```bash
curl -X POST http://localhost:8000/api/v1/executions \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow_version_id": "uuid",
    "file_id": "uuid"
  }'
```

### 7. Verificar Estado de Ejecución

```bash
curl -X GET http://localhost:8000/api/v1/executions/{execution_id} \
  -H "Authorization: Bearer {token}"
```

### 8. Descargar Resultados

```bash
curl -X GET http://localhost:8000/api/v1/executions/{execution_id}/output \
  -H "Authorization: Bearer {token}" \
  --output resultado.xlsx
```

## 🎨 Reglas Disponibles

| Tipo de Regla | Descripción | Parámetros |
|-----------|-------------|------------|
| `filter` | Filtrar filas por condición | `column`, `operator`, `value` |
| `move` | Mover filas a nueva hoja | `target_sheet` |
| `group_sum` | Agrupar y agregar | `group_by`, `field`, `target_sheet` |

### Operadores Soportados

- `=` Igual
- `!=` Diferente
- `>` Mayor que
- `<` Menor que
- `>=` Mayor o igual
- `<=` Menor o igual
- `contains` Texto contiene

## 🗄️ Esquema de Base de Datos

### Arquitectura Multi-Tenant

```sql
companies (empresas)
├── users (usuarios, vía memberships)
├── workflows (flujos de trabajo)
│   └── workflow_versions (versiones)
│       └── executions (ejecuciones)
│           ├── execution_logs (registros)
│           └── execution_files (archivos)
└── files (archivos)
```

**Decisiones de Diseño Clave:**

- ✅ Base de datos única con aislamiento por `company_id`
- ✅ Versionado explícito para reproducibilidad
- ✅ Auditoría mediante registros de ejecución
- ✅ Expiración automática de archivos

## 🔐 Características de Seguridad

- **Autenticación JWT** - Autenticación segura basada en tokens
- **Aislamiento de Tenants** - Filtrado estricto por `company_id`
- **Hash de Contraseñas** - Bcrypt con sal
- **Expiración de Archivos** - Limpieza automática después de 24h
- **Validación de Entrada** - Esquemas Pydantic en todos los endpoints

## 🧪 Pruebas

```bash
# Ejecutar pruebas unitarias
pytest tests/

# Ejecutar con cobertura
pytest --cov=app tests/

# Probar módulo específico
pytest tests/test_engine.py -v
```

## 📦 Estructura del Proyecto

```
dataweaver/
├── backend/
│   └── app/
│       ├── engine/          # Motor de ejecución de reglas
│       │   ├── context.py   # Estado de ejecución
│       │   ├── engine.py    # Orquestador principal
│       │   ├── validator.py # Validación pre-ejecución
│       │   └── rules/       # Implementaciones de reglas
│       │       ├── base.py
│       │       ├── filter.py
│       │       ├── move.py
│       │       ├── group_sum.py
│       │       └── factory.py
│       ├── routes/          # Endpoints API
│       │   ├── auth.py
│       │   ├── workflows.py
│       │   ├── files.py
│       │   └── executions.py
│       ├── tasks/           # Tareas Celery
│       │   └── workflow_execution.py
│       ├── models.py        # Modelos SQLAlchemy
│       ├── schemas.py       # Esquemas Pydantic
│       ├── database.py      # Conexión BD
│       ├── auth.py          # Lógica de autenticación
│       ├── config.py        # Configuración
│       └── main.py          # App FastAPI
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## 🎯 Hoja de Ruta

### MVP (Actual)
- [x] Motor de reglas core (Filter, Move, GroupSum)
- [x] Arquitectura multi-tenant
- [x] Ejecución asíncrona
- [x] Autenticación JWT
- [x] Subida/descarga de archivos
- [x] Versionado de flujos

### v2 (Planeado)
- [ ] Reglas adicionales (Sort, Transform, Validate)
- [ ] Flujos multi-archivo
- [ ] Ejecuciones programadas
- [ ] Notificaciones por email
- [ ] Dashboard de historial

### v3 (Futuro)
- [ ] Frontend React (UI Constructor de Reglas)
- [ ] Marketplace de flujos
- [ ] Integraciones API (Google Sheets, Airtable)
- [ ] SDK desarrollo de reglas personalizadas
- [ ] SSO empresarial

## 📚 Documentación técnica

Se han añadido documentos técnicos y esquemas para facilitar la extensión del motor de reglas:

- `docs/agent.md`: Descripción del agente/orquestador (lifecycle, relación con Celery y la API).
- `docs/skills.md`: Catálogo de skills (mapeadas a las reglas existentes) y guía "Cómo añadir un skill".
- `docs/schemas/`: JSON Schema por tipo de skill (`filter`, `move`, `group_sum`).
- `docs/examples/sample_workflow.json`: Ejemplo de workflow válido.
- `tests/test_skills.py`: Plantilla de tests unitarios para skills. Los tests actuales pasan.

Para ejecutar los tests locales asegúrate de añadir `backend` al `PYTHONPATH`:

Windows PowerShell:

```powershell
$env:PYTHONPATH = "backend"
pytest -q
```

Linux / macOS:

```bash
export PYTHONPATH=backend
pytest -q
```


## 💼 Casos de Uso

### 1. Reportes Financieros Mensuales
**Problema**: Equipo de finanzas consolida manualmente datos de 10 sucursales  
**Solución**: Filtrar por fecha → Agrupar por sucursal → Sumar ingresos → Exportar resumen

### 2. Limpieza de Datos de Clientes
**Problema**: Exportaciones CRM contienen duplicados y emails inválidos  
**Solución**: Filtrar nulos → Eliminar duplicados → Validar emails → Marcar problemas

### 3. Reordenamiento de Inventario
**Problema**: Verificación manual de niveles de stock en almacenes  
**Solución**: Filtrar stock bajo → Agrupar por proveedor → Generar órdenes de compra

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Por favor sigue estas pautas:

1. Haz fork del repositorio
2. Crea una rama de feature (`git checkout -b feature/regla-increible`)
3. Commit de cambios (`git commit -m 'Añadir regla increíble'`)
4. Push a la rama (`git push origin feature/regla-increible`)
5. Abre un Pull Request

## 📄 Licencia

Licencia MIT - ver archivo [LICENSE](LICENSE)

## 🙋 Soporte

- **Documentación**: [docs.macrobuilder.io](https://docs.macrobuilder.io) (próximamente)
- **Issues**: [GitHub Issues](https://github.com/Medalcode/DataWeaver/issues)
- **Repositorio**: [GitHub](https://github.com/Medalcode/DataWeaver)

---

**Construido con ❤️ para usuarios de negocio que merecen algo mejor que VBA**
