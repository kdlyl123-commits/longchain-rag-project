"""Celery 异步任务（仅在 Redis 可用时启用）"""

from app.config import get_settings

settings = get_settings()
celery_app = None

if settings.redis_url:
    try:
        from celery import Celery

        celery_app = Celery(
            "rag_ecommerce",
            broker=settings.redis_url,
            backend=settings.redis_url,
            include=["app.tasks.document_tasks"],
        )

        celery_app.conf.update(
            task_serializer="json",
            accept_content=["json"],
            result_serializer="json",
            timezone="Asia/Shanghai",
            enable_utc=True,
            task_track_started=True,
            task_acks_late=True,
            worker_prefetch_multiplier=1,
        )
    except Exception:
        celery_app = None
