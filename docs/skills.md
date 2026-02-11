# Skills (Catálogo de reglas)

Resumen
-------
En este proyecto un `skill` se mapea directamente a la abstracción existente `rule`. Cada skill define un comportamiento atómico que el motor ejecuta sobre un `DataFrame` dentro de un `ExecutionContext`.

Contrato / forma canónica
-------------------------
Un `skill` se representa en el workflow JSON como un `step` con al menos las claves:

- `type`: identificador del skill (ej.: `filter`, `move`, `group_sum`).
- otros parámetros específicos del tipo (ej.: `column`, `operator`, `value`).

Ejemplo de `steps`:

[
  {"type": "filter", "column": "Status", "operator": "=", "value": "OK"},
  {"type": "group_sum", "group_by": "Category", "field": "Amount", "target_sheet": "sums"},
  {"type": "move", "target_sheet": "final"}
]

Esquemas JSON
-------------
Se incluyen esquemas JSON por tipo en `docs/schemas/` para validación automática en la API/UI:

- `docs/schemas/filter.schema.json`
- `docs/schemas/move.schema.json`
- `docs/schemas/group_sum.schema.json`

Los esquemas definen campos requeridos, tipos y valores permitidos (p. ej. operadores permitidos en `filter`).

Cómo añadir un nuevo skill (cookbook)
-----------------------------------
1. Crear el archivo `app/engine/rules/my_skill.py` siguiendo la plantilla:

```py
from app.engine.rules.base import Rule

class MySkill(Rule):
    def execute(self, context, params):
        # implementar la lógica que modifica context.current_df o escribe en context.outputs
        pass
```

2. Registrar la clase en `RULE_REGISTRY` en `app/engine/rules/factory.py`:

```py
RULE_REGISTRY = {
    "filter": FilterRule,
    "move": MoveRule,
    "group_sum": GroupSumRule,
    "my_skill": MySkill,
}
```

3. Añadir un `JSON Schema` para el skill en `docs/schemas/` y referenciarlo en `docs/skills.md`.

4. Escribir tests unitarios en `tests/` que creen un `ExecutionContext` con un `pandas.DataFrame` de ejemplo, llamen a `MySkill().execute(context, params)` y verifiquen `context.outputs` y `context.logs`.

Buenas prácticas
---------------
- Diseñar skills pequeños y idempotentes cuando sea posible.
- Registrar mensajes claros en `context.log(step_type, message, affected_rows)` para auditoría.
- Definir `target_sheet` de salida para evitar colisiones de nombres; documentar convención de nombres en la organización.
- Versionar cambios en parámetros del skill (ej.: `my_skill:v2`) si se rompe compatibilidad.

Ejemplos de parámetros por tipo
------------------------------
- `filter`: requiere `column`, `operator`, `value`.
- `move`: requiere `target_sheet`.
- `group_sum`: requiere `group_by`, `field`, `target_sheet`.

Referencias
----------
- Implementación de reglas: [backend/app/engine/rules](backend/app/engine/rules)
- Factory: [backend/app/engine/rules/factory.py](backend/app/engine/rules/factory.py)
- Validador: [backend/app/engine/validator.py](backend/app/engine/validator.py)
