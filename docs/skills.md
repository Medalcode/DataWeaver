# Skills — Catálogo de Reglas del Motor

> **Versión del documento**: 1.0  
> **Referencia de código**: [`backend/app/engine/rules/`](../backend/app/engine/rules/)

---

## ¿Qué es un Skill?

En DataWeaver / Macro Builder, un **skill** es la unidad atómica de procesamiento del motor de reglas. Cada skill:

- Se implementa como una subclase de `Rule` en `backend/app/engine/rules/`.
- Se registra en `RULE_REGISTRY` dentro de `factory.py`.
- Recibe un `ExecutionContext` (que encapsula el `DataFrame` activo y los outputs parciales) y un diccionario de parámetros.
- Escribe resultados en `context.outputs` y/o modifica `context.current_df`.
- Registra cada acción mediante `context.log(step_type, message, affected_rows)`.

```
ExecutionContext
   ├── current_df: pd.DataFrame   ← DataFrame activo (se puede modificar)
   ├── outputs: Dict[str, DataFrame] ← hojas de salida nombradas
   └── logs: List[dict]           ← pista de auditoría
```

---

## Esquema Canónico de un Step

Cada step en el JSON de reglas de un workflow debe seguir este contrato mínimo:

```json
{
  "type": "<skill_type>",
  "<param_1>": "<value_1>",
  "<param_2>": "<value_2>"
}
```

La clave `type` es **obligatoria** y debe coincidir exactamente con la clave registrada en `RULE_REGISTRY`. El resto de campos son específicos de cada skill.

**Ejemplo de workflow con múltiples steps:**

```json
{
  "steps": [
    { "type": "filter",    "column": "Status",   "operator": "=",  "value": "Approved" },
    { "type": "group_sum", "group_by": "Product", "field": "Amount", "target_sheet": "Summary" },
    { "type": "move",      "target_sheet": "Approved_Rows" }
  ]
}
```

---

## Catálogo de Skills

### 1. `filter` — Filtrar Filas

| Atributo        | Valor                                                  |
|-----------------|--------------------------------------------------------|
| **Clase**       | `FilterRule` (`app/engine/rules/filter.py`)            |
| **Registered as** | `"filter"`                                           |
| **Modifica**    | `context.current_df` (reemplaza por el subconjunto filtrado) |
| **Escribe outputs** | No                                                |

#### Parámetros

| Parámetro  | Tipo   | Requerido | Descripción                              |
|------------|--------|-----------|------------------------------------------|
| `column`   | string | ✅        | Nombre exacto de la columna a evaluar    |
| `operator` | string | ✅        | Operador de comparación (ver tabla)      |
| `value`    | any    | ✅        | Valor contra el que se compara la columna|

#### Operadores Soportados

| Operador    | Semántica                          | Ejemplo                              |
|-------------|------------------------------------|--------------------------------------|
| `=`         | Igual estricto                     | `"operator": "=", "value": "OK"`     |
| `!=`        | Distinto                           | `"operator": "!=", "value": "VOID"`  |
| `>`         | Mayor que                          | `"operator": ">", "value": 1000`     |
| `<`         | Menor que                          | `"operator": "<", "value": 500`      |
| `>=`        | Mayor o igual                      | `"operator": ">=", "value": 0`       |
| `<=`        | Menor o igual                      | `"operator": "<=", "value": 9999`    |
| `contains`  | Contiene subcadena (case-insensitive) | `"operator": "contains", "value": "Corp"` |

#### Ejemplo JSON

```json
{ "type": "filter", "column": "Region", "operator": "contains", "value": "Sur" }
```

#### Errores Comunes

| Mensaje                               | Causa                                             |
|---------------------------------------|---------------------------------------------------|
| `Column 'X' not found in dataframe`   | La columna especificada no existe en el archivo   |
| `Unsupported operator: X`             | El operador no pertenece a la lista soportada     |

---

### 2. `move` — Exportar DataFrame Activo a una Hoja

| Atributo        | Valor                                              |
|-----------------|----------------------------------------------------|
| **Clase**       | `MoveRule` (`app/engine/rules/move.py`)            |
| **Registered as** | `"move"`                                         |
| **Modifica**    | No modifica `context.current_df`                   |
| **Escribe outputs** | `context.outputs[target_sheet]` = copia del DF |

Copia el `current_df` en el momento de ejecución como una hoja nombrada en el resultado final. El DataFrame activo **no se vacía**; si se necesita aislar una hoja, usar `move` y luego aplicar más filtros.

#### Parámetros

| Parámetro      | Tipo   | Requerido | Descripción                               |
|----------------|--------|-----------|-------------------------------------------|
| `target_sheet` | string | ✅        | Nombre de la hoja en el archivo de salida |

#### Ejemplo JSON

```json
{ "type": "move", "target_sheet": "Clientes_Activos" }
```

#### Convención de Nombres de Hojas

- Usar `PascalCase` o `snake_case`, evitar espacios (Excel los permite pero dificultan el procesamiento posterior).
- Nombres únicos por ejecución; si dos steps apuntan al mismo `target_sheet`, el segundo sobreescribe al primero.

#### Errores Comunes

| Mensaje                  | Causa                              |
|--------------------------|------------------------------------|
| `target_sheet is required` | Parámetro `target_sheet` ausente o vacío |

---

### 3. `group_sum` — Agrupar y Sumar

| Atributo        | Valor                                                       |
|-----------------|-------------------------------------------------------------|
| **Clase**       | `GroupSumRule` (`app/engine/rules/group_sum.py`)            |
| **Registered as** | `"group_sum"`                                             |
| **Modifica**    | No modifica `context.current_df`                            |
| **Escribe outputs** | `context.outputs[target_sheet]` = DataFrame agrupado   |

Genera un DataFrame con dos columnas: la columna de agrupación (`group_by`) y la suma del campo numérico (`field`), y lo almacena como una hoja de salida.

#### Parámetros

| Parámetro      | Tipo   | Requerido | Descripción                                      |
|----------------|--------|-----------|--------------------------------------------------|
| `group_by`     | string | ✅        | Columna por la que se agrupa                     |
| `field`        | string | ✅        | Columna numérica que se suma                     |
| `target_sheet` | string | ✅        | Nombre de la hoja de salida con el resultado     |

#### Ejemplo JSON

```json
{
  "type": "group_sum",
  "group_by": "Sucursal",
  "field": "Ventas",
  "target_sheet": "Ventas_por_Sucursal"
}
```

#### Errores Comunes

| Mensaje                                       | Causa                                              |
|-----------------------------------------------|----------------------------------------------------|
| `group_by, field, and target_sheet are required` | Uno o más parámetros ausentes                   |
| `Column 'X' not found`                        | La columna `group_by` o `field` no existe en el DF |

---

## JSON Schemas de Validación

Los schemas JSON en `docs/schemas/` validan los steps antes de la ejecución:

| Skill       | Schema                                     |
|-------------|---------------------------------------------|
| `filter`    | [`docs/schemas/filter.schema.json`](schemas/filter.schema.json) |
| `move`      | [`docs/schemas/move.schema.json`](schemas/move.schema.json)     |
| `group_sum` | [`docs/schemas/group_sum.schema.json`](schemas/group_sum.schema.json) |

El validador central se encuentra en [`backend/app/engine/validator.py`](../backend/app/engine/validator.py).

---

## Cookbook: Añadir un Nuevo Skill

### Paso 1 — Crear la clase de la regla

```
backend/app/engine/rules/my_skill.py
```

```python
from app.engine.rules.base import Rule
from app.engine.context import ExecutionContext


class MySkill(Rule):
    """Descripción clara de lo que hace este skill."""

    def execute(self, context: ExecutionContext, params: dict):
        # 1. Leer parámetros
        column = params.get("column")
        if not column:
            raise ValueError("'column' is required for my_skill")

        # 2. Operar sobre context.current_df
        df = context.current_df
        # ... lógica de transformación ...

        # 3. Actualizar el contexto
        context.current_df = df_transformed          # si modifica el DF activo
        context.outputs["my_output"] = df_result     # si produce una hoja de salida

        # 4. Registrar la acción (OBLIGATORIO para auditoría)
        context.log("my_skill", f"Procesadas {len(df_result)} filas", len(df_result))
```

### Paso 2 — Registrar en la factory

```
backend/app/engine/rules/factory.py
```

```python
from app.engine.rules.my_skill import MySkill

RULE_REGISTRY = {
    "filter":    FilterRule,
    "move":      MoveRule,
    "group_sum": GroupSumRule,
    "my_skill":  MySkill,      # ← añadir aquí
}
```

### Paso 3 — Añadir el JSON Schema

```
docs/schemas/my_skill.schema.json
```

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "MySkill Step",
  "type": "object",
  "required": ["type", "column"],
  "properties": {
    "type":   { "type": "string", "const": "my_skill" },
    "column": { "type": "string", "minLength": 1 }
  },
  "additionalProperties": false
}
```

Referenciar el schema en este documento en la sección **JSON Schemas de Validación**.

### Paso 4 — Escribir tests unitarios

```
tests/test_my_skill.py
```

```python
import pandas as pd
import pytest
from app.engine.context import ExecutionContext
from app.engine.rules.my_skill import MySkill

def test_my_skill_basic():
    df = pd.DataFrame({"column": ["a", "b"], "value": [10, 20]})
    ctx = ExecutionContext(df)
    MySkill().execute(ctx, {"column": "column"})
    assert len(ctx.logs) == 1
    assert ctx.logs[0]["step_type"] == "my_skill"

def test_my_skill_missing_param():
    ctx = ExecutionContext(pd.DataFrame())
    with pytest.raises(ValueError, match="'column' is required"):
        MySkill().execute(ctx, {})
```

---

## Buenas Prácticas

| Principio             | Guía                                                                                      |
|-----------------------|-------------------------------------------------------------------------------------------|
| **Atomicidad**        | Cada skill hace exactamente una cosa. Si necesita dos, crea dos skills.                   |
| **Idempotencia**      | Diseña skills que produzcan el mismo resultado al ejecutarse múltiples veces.             |
| **Logging obligatorio** | Siempre llama a `context.log()` al final del `execute()`.                               |
| **Validación temprana** | Valida los parámetros al inicio; lanza `ValueError` con mensajes descriptivos.          |
| **Nombres de hojas**  | Define `target_sheet` con nombres únicos; documenta la convención en tu equipo.           |
| **Versionado**        | Si cambias la firma de parámetros de forma incompatible, registra el skill como `my_skill_v2` en el registry. |
| **No acoplar skills** | Los skills no deben importarse entre sí; la composición la gestiona el `engine.py`.      |

---

## Política de Versionado de Skills

1. **Cambio compatible** (nuevo parámetro opcional) → mismo nombre, misma versión de registry.  
2. **Cambio incompatible** (renombrar parámetro requerido, cambiar semántica) → registrar como `<skill>_v2`. Las versiones anteriores de workflows siguen usando `<skill>` sin romper.  
3. Documentar en el CHANGELOG del proyecto qué versión de la app introdujo cada skill.

---

## Referencias

| Recurso                  | Ruta                                                       |
|--------------------------|------------------------------------------------------------|
| Clase base `Rule`        | [`backend/app/engine/rules/base.py`](../backend/app/engine/rules/base.py) |
| Factory / Registry       | [`backend/app/engine/rules/factory.py`](../backend/app/engine/rules/factory.py) |
| Contexto de ejecución    | [`backend/app/engine/context.py`](../backend/app/engine/context.py) |
| Motor principal          | [`backend/app/engine/engine.py`](../backend/app/engine/engine.py) |
| Validador de reglas      | [`backend/app/engine/validator.py`](../backend/app/engine/validator.py) |
| Schemas de validación    | [`docs/schemas/`](schemas/)                                |
| Arquitectura general     | [`docs/ARCHITECTURE.md`](ARCHITECTURE.md)                  |
