import functools
import logging
import os

from sca_logger import utils
from sca_logger.sca_formatter import SCAFormatter
from sca_logger.sca_log_filter import LambdaLoggerFilter
from sca_logger.sca_memory_handler import SCAMemoryHandler


def logger(aws_request_id: str, _log_group_name: str, event: dict,
           config_args=None) -> logging.Logger:
    if config_args is None:
        config_args = {}
    _sca_logger = logging.getLogger()
    _sca_logger.setLevel(logging.DEBUG)
    capacity = int(os.getenv('MEMORY_HANDLER_LOG_CAPACITY', 40))
    handler = SCAMemoryHandler(capacity=capacity, log_group_name=_log_group_name)
    if config_args['marshal_as_json']:
        # [INFO]	2019-02-21T12:07:13.499506Z    This is an info message
        formatter = SCAFormatter(config_args, frmt='[%(levelname)s]\t%(asctime)sZ\t%(message)s\n')
    else:
        # [INFO]	2019-02-21T12:07:13.499506Z	11e8-ba3f-79a3ec964b93	This is an info message
        formatter = SCAFormatter(config_args,
                                 frmt='[%(levelname)s]\t%(asctime)sZ\t%(aws_request_id)s\t%(message)s\n')
    handler.setFormatter(formatter)
    handler.addFilter(LambdaLoggerFilter(aws_request_id, event, config_args))
    for _handler in _sca_logger.handlers:
        _sca_logger.removeHandler(_handler)
    _sca_logger.addHandler(handler)
    return _sca_logger


def sca_log_decorator(*args, **kwargs):
    _func = None
    if len(args) == 1 and callable(args[0]):
        _func = args[0]

    config_args = {
        'marshal_as_json': kwargs.get('log_as_json', True),
        'log_event': kwargs.get('log_event', True)
    }
    logger_func = logger

    def args_wrapper(func):
        @functools.wraps(func)
        def handle_wrapper(event, context):
            if context.__class__.__name__ == 'LambdaContext':
                _log_group_name = context.log_group_name
                _aws_request_id = context.aws_request_id
                _logger = logger_func(_aws_request_id, _log_group_name, event,
                                      config_args=config_args)
                try:
                    lambda_execution_response = func(event, context)
                except Exception as e:
                    logging.getLogger().exception(e)
                    raise e
                finally:
                    """
                        The atexit hooks are tricky with aws lambda as they have an altered thread
                        implementation. So force flush to simulate atexit.register(logging.shutdown)
                    """
                    _logger.handlers[0].flush()
            else:
                lambda_execution_response = func(event, context)
            return lambda_execution_response

        return handle_wrapper

    return args_wrapper(_func) if _func else args_wrapper


class SCALoggerException(Exception):
    pass
