import multiprocessing
import os

bind = "0.0.0.0:8000"
workers = int(os.getenv("GUNICORN_WORKERS", max(2, multiprocessing.cpu_count())))
worker_class = "gevent"
worker_connections = 1000
timeout = 120
graceful_timeout = 30
keepalive = 5
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")
preload_app = False


def _silence_logging_on_teardown() -> None:
    """Gevent workers + stdlib logging can raise during container stop; ignore it."""
    import logging

    logging.raiseExceptions = False
    try:
        logging.shutdown()
    except Exception:
        pass


def on_exit(server) -> None:
    _silence_logging_on_teardown()


def worker_exit(server, worker) -> None:
    _silence_logging_on_teardown()
