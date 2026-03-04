"""
Task queue configuration for Clipsmith.

Uses Redis-backed RQ queues for production, with graceful fallback
to synchronous execution when Redis is unavailable in development.
"""

import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class _SyncJob:
    """Minimal job-like object returned by the synchronous fallback queue."""

    def __init__(self, func, *args, **kwargs):
        self.id = f"sync-{id(self)}"
        self._func = func
        self._args = args
        self._kwargs = kwargs
        self._result = None

    def get_status(self):
        return "finished"


class _SyncQueue:
    """Synchronous fallback queue that executes tasks immediately.
    Used in development when Redis is not available."""

    def __init__(self, name: str = "default"):
        self.name = name
        logger.info(f"SyncQueue '{name}' created (tasks will run synchronously)")

    def enqueue(self, func, *args, **kwargs):
        logger.info(f"SyncQueue '{self.name}': executing {func.__name__} synchronously")
        job = _SyncJob(func, *args, **kwargs)
        try:
            job._result = func(*args, **kwargs)
        except Exception as e:
            logger.error(f"SyncQueue '{self.name}': task {func.__name__} failed: {e}")
        return job


def _create_queues():
    """Create Redis-backed RQ queues, or fall back to synchronous queues."""
    environment = os.getenv("ENVIRONMENT", "development")

    try:
        from .redis_config import get_redis_client
        import redis as redis_lib
        from rq import Queue

        client = get_redis_client()

        # If the client is our InMemoryCache fallback, use sync queues
        # because RQ requires a real Redis connection
        if not isinstance(client, redis_lib.Redis):
            raise ConnectionError("Redis not available, using sync fallback")

        video_q = Queue("video_processing", connection=client)
        default_q = Queue("default", connection=client)
        logger.info("RQ queues initialized with Redis connection")
        return video_q, default_q

    except Exception as e:
        if environment == "production":
            logger.error(f"Failed to create Redis queues in production: {e}")
            raise

        logger.warning(
            f"Redis queues unavailable ({e}). Using synchronous fallback for development."
        )
        return _SyncQueue("video_processing"), _SyncQueue("default")


video_queue, default_queue = _create_queues()


def get_video_queue():
    return video_queue


def get_default_queue():
    return default_queue
