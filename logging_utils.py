import contextvars
import logging
import os
import uuid


_REQUEST_ID = contextvars.ContextVar("request_id", default="-")
_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | rid=%(request_id)s | %(message)s"


def _as_bool(value):
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


_DEBUG_ENABLED = _as_bool(os.getenv("RAG_DEBUG_LOGS", "0"))


def _current_log_level():
    if _DEBUG_ENABLED:
        return logging.DEBUG
    return logging.INFO


class RequestIdFilter(logging.Filter):

    def filter(self, record):
        record.request_id = _REQUEST_ID.get()
        return True


def _configure_root_logging():
    root_logger = logging.getLogger()

    if not root_logger.handlers:
        logging.basicConfig(
            level=_current_log_level(),
            format=_LOG_FORMAT
        )

    root_logger.setLevel(_current_log_level())

    for handler in root_logger.handlers:
        if not any(
            isinstance(existing_filter, RequestIdFilter)
            for existing_filter in handler.filters
        ):
            handler.addFilter(RequestIdFilter())

        handler.setFormatter(logging.Formatter(_LOG_FORMAT))


def configure_logger(name):
    _configure_root_logging()

    module_logger = logging.getLogger(name)
    module_logger.setLevel(_current_log_level())

    return module_logger


def start_request_id(prefix=None):
    token = uuid.uuid4().hex[:8]

    if prefix:
        request_id = f"{prefix}-{token}"
    else:
        request_id = token

    _REQUEST_ID.set(request_id)

    return request_id


def set_request_id(request_id):
    _REQUEST_ID.set(request_id)


def get_request_id():
    return _REQUEST_ID.get()


def clear_request_id():
    _REQUEST_ID.set("-")


def set_debug_enabled(enabled):
    global _DEBUG_ENABLED

    _DEBUG_ENABLED = bool(enabled)

    target_level = _current_log_level()
    root_logger = logging.getLogger()
    root_logger.setLevel(target_level)

    for handler in root_logger.handlers:
        handler.setLevel(target_level)

    for existing_logger in logging.Logger.manager.loggerDict.values():
        if isinstance(existing_logger, logging.Logger):
            existing_logger.setLevel(target_level)


def is_debug_enabled():
    return _DEBUG_ENABLED
