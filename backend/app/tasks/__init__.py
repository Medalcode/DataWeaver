from app.core.config import settings

try:
    from celery import Celery
    from celery.schedules import crontab

    celery_app = Celery(
        "dataweaver", broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_RESULT_BACKEND
    )

    celery_app.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        enable_utc=True,
        imports=["app.tasks.workflow_execution", "app.tasks.maintenance"],
    )

    celery_app.conf.beat_schedule = {
        "cleanup-expired-files-every-hour": {
            "task": "cleanup_expired_files",
            "schedule": crontab(minute=0),
        },
    }
except (ImportError, ModuleNotFoundError):  # pragma: no cover
    # Fallback mock for local unit tests without Celery installed
    class DummyTask:
        def __init__(self, fn):
            self.fn = fn
            self.delay = fn
            self.apply_async = fn

        def __call__(self, *args, **kwargs):
            return self.fn(*args, **kwargs)

    class DummyCelery:
        def task(self, *args, **kwargs):
            def decorator(fn):
                return DummyTask(fn)
            return decorator

        conf = type("conf", (), {"update": lambda self, **kw: None, "beat_schedule": {}})()

    celery_app = DummyCelery()
    def crontab(*args, **kwargs):
        return None
