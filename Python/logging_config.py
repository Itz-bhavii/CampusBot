import sys

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(module)s %(lineno)d %(message)s'
        },
    },
    'handlers': {
        'stdout': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'json',
        },
    },
    'loggers': {
        'campus-bot': {
            'handlers': ['stdout'],
            'level': 'INFO',
            'propagate': False,
        }
    },
    'root': {
        'handlers': ['stdout'],
        'level': 'WARNING',
    },
}