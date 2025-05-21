from logging.config import dictConfig
import logging


def logger_settings(service_name, log_level):
    return {
        "version": 1,
        "disable_existing_loggers": False,
        'filters': {
            'correlation_id': {
                '()': 'asgi_correlation_id.CorrelationIdFilter',
                'uuid_length': 32,
                'default_value': '-',
            },
        },
        "formatters": {
            "default": {
                "()": "uvicorn.logging.DefaultFormatter",
                "fmt": f'[%(asctime)s ] [%(levelprefix)s] /{service_name} %(pathname)s %(name)s:%(funcName)s:%(lineno)d] - %(message)s',
                "datefmt": "%Y-%m-%d %H:%M:%S",
                "use_colors": True
            },
            "access": {
                "()": "uvicorn.logging.AccessFormatter",
                "fmt": f'[%(asctime)s %(levelprefix)s /{service_name}] '
                       f'- "%(request_line)s" %(status_code)s',
                "datefmt": "%Y-%m-%d %H:%M:%S",
                "use_colors": True
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
                'filters': ['correlation_id'],
            },
            "access": {
                "formatter": "access",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "logger": {
                "handlers": ["default"],
                "level": f"{log_level}"
            },
            "uvicorn.access": {
                "handlers": ["access"],
                "level": f"{log_level}",
                "propagate": False
            },
        },
    }


log_settings = logger_settings('BILLING_SERVICE', 'DEBUG')
dictConfig(log_settings)
logger = logging.getLogger('logger')
