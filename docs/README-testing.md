# Ejecutar tests

Instrucciones rápidas para ejecutar los tests localmente.

Requisitos
- Python 3.10+ (o la versión usada por tu entorno)
- Dependencias del proyecto (ver `requirements.txt`).

Desde Windows PowerShell (en la raíz del repositorio `DataWeaver`):

```powershell
$env:PYTHONPATH = "backend"
pytest -q
```

Desde Linux / macOS (bash/zsh):

```bash
export PYTHONPATH=backend
pytest -q
```

Notas
- Los tests unitarios usan el paquete `app` ubicado en `backend/app` por eso ajustamos `PYTHONPATH`.
- Si usas un virtualenv, activa el entorno antes de instalar dependencias.
