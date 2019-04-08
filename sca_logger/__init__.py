import datetime
import functools
import gzip
import io
import json
import logging
import os
from logging.handlers import MemoryHandler

from sca_logger import utils

kinesis_client = utils.kinesis_client()
KINESIS_SCA_LOG_STREAM = os.environ['KINESIS_SCA_LOG_STREAM']
MEMORY_HANDLER_LOG_CAPACITY = int(os.getenv('MEMORY_HANDLER_LOG_CAPACITY', 1))
JSON_LOG_KEYS = ['aws_request_id', 'asctime', 'filename', 'funcName', 'levelname', 'message',
                 'exc_info']


def logger(aws_request_id, _log_group_name, event, config_args={}):
    _sca_logger = logging.getLogger()
    _sca_logger.setLevel(logging.DEBUG)
    capacity = int(os.getenv('MEMORY_HANDLER_LOG_CAPACITY', 40))
    handler = SCAMemoryHandler(capacity=capacity, log_group_name=_log_group_name)
    if config_args['marshal_as_json']:
        # [INFO]	2019-02-21T12:07:13.499506Z	11e8-ba3f-79a3ec964b93	This is an info message
        formatter = SCAFormatter('[%(levelname)s]\t%(asctime)sZ\t%(aws_request_id)s\t%(message)s\n')
    else:
        # [INFO]	This is an info message
        formatter = SCAFormatter(config_args, frmt='[%(levelname)s]\t%(message)s\n')
    handler.setFormatter(formatter)
    handler.addFilter(LambdaLoggerFilter(aws_request_id, event, config_args))
    for _handler in _sca_logger.handlers:
        _sca_logger.removeHandler(_handler)
    _sca_logger.addHandler(handler)
    return _sca_logger


class SCAFormatter(logging.Formatter):
    def __init__(self, config_params, frmt):
        super(SCAFormatter, self).__init__(frmt)
        self.config_params = config_params

    def formatTime(self, record, datefmt=None):
        timestamp = record.created
        py_datetime = datetime.datetime.fromtimestamp(timestamp)
        return py_datetime.isoformat()

    def format(self, record):
        message = super(SCAFormatter, self).format(record)
        if self.config_params['marshal_as_json']:
            try:
                response = dict()
                for _key in JSON_LOG_KEYS:
                    if getattr(record, _key, None):
                        response[_key] = getattr(record, _key)
                response['event'] = getattr(record, 'event', None)
                response['message'] = message
                return json.dumps(response, sort_keys=True, indent=4, default=str)
            except Exception:
                return message
        else:
            return message


class LambdaLoggerFilter(logging.Filter):
    def __init__(self, aws_request_id, event, config_args={}):
        super(LambdaLoggerFilter, self).__init__()
        self.aws_request_id = aws_request_id
        self.event = event
        self.config_args = config_args

    def filter(self, record):
        record.aws_request_id = self.aws_request_id
        if self.config_args['log_event']:
            record.event = self.event
        return record.name == 'root'


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


class SCAMemoryHandler(MemoryHandler):
    def __init__(self, capacity, log_group_name):
        self.log_group_name = log_group_name
        logging.Handler.__init__(self)
        super().__init__(capacity=capacity)

    def upload_to_kinesis(self, byte_stream):
        kinesis_client.put_record(Data=byte_stream.getvalue(),
                                  StreamName=KINESIS_SCA_LOG_STREAM,
                                  PartitionKey=self.log_group_name)

    def flush(self):
        self.acquire()
        try:
            if len(self.buffer) != 0:
                byte_stream = io.BytesIO()
                with gzip.GzipFile(mode='wb', fileobj=byte_stream) as gz:
                    for record in self.buffer:
                        gz.write(f"{self.format(record)}".encode('utf-8'))

                # # TODO@vkara Remove once the library is tested and stabilized.
                # byte_stream.seek(0)
                # with gzip.GzipFile(mode='rb', fileobj=byte_stream) as reader:
                #     a = reader.readlines()
                #     for rec in a:
                #         print(rec.decode('utf-8'))

                self.upload_to_kinesis(byte_stream)
                byte_stream.close()
                self.buffer = []
        finally:
            self.release()


class SCALoggerException(Exception):
    pass
