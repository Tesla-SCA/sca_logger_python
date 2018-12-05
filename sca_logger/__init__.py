import functools
import gzip
import io
import logging
import os
from logging.handlers import MemoryHandler

from sca_logger import utils

kinesis_client = utils.kinesis_client()
KINESIS_SCA_LOG_STREAM = os.environ['KINESIS_SCA_LOG_STREAM']
MEMORY_HANDLER_LOG_CAPACITY = int(os.getenv('MEMORY_HANDLER_LOG_CAPACITY', 40))

_log_group_name = None
_aws_request_id = None
_sca_logger = None


def logger():
    global _sca_logger, _log_group_name, _aws_request_id
    if _sca_logger is None:
        if _log_group_name is None or type(_log_group_name) is not str or len(
                _log_group_name) < 1:
            raise SCALoggerException('Invalid log_group_name')

        name = _aws_request_id if _aws_request_id else _log_group_name
        _sca_logger = logging.getLogger(name)
        _sca_logger.setLevel(logging.DEBUG)
        capacity = int(os.getenv('MEMORY_HANDLER_LOG_CAPACITY', 40))
        handler = SCAMemoryHandler(capacity=capacity,
                                   log_group_name=_log_group_name)
        # [INFO]	2018-11-29T20:00:31.828Z	11e8-ba3f-79a3ec964b93	This is info msg
        formatter = logging.Formatter('[%(levelname)s] - %(asctime)s - %(name)s - %(message)s')
        handler.setFormatter(formatter)
        _sca_logger.addHandler(handler)
        _sca_logger.setLevel(logging.DEBUG)
    return _sca_logger


def sca_log_decorator(func):
    logger_func = logger

    @functools.wraps(func)
    def handle_wrapper(event, context):
        global _log_group_name, _aws_request_id, _sca_logger
        lambda_execution_response = None
        if context.__class__.__name__ == 'LambdaContext':
            _log_group_name = context.log_group_name
            _aws_request_id = context.aws_request_id
            _logger = logger_func()
            lambda_execution_response = func(event, context)
            # the atexit hooks are tricky with aws lambda as they have an altered python
            # thread implementation. So force flush
            # atexit.register(logging.shutdown)
            _logger.handlers[0].flush()
            _sca_logger = None
        return lambda_execution_response

    return handle_wrapper


class SCAMemoryHandler(MemoryHandler):
    def __init__(self, capacity, log_group_name):
        self.log_group_name = log_group_name
        super().__init__(capacity=capacity, flushLevel=logging.ERROR)

    def clear_buffer(self):
        self.buffer = []

    def upload_to_kinesis(self, byte_stream):
        kinesis_client.put_record(Data=byte_stream.getvalue(),
                                  StreamName=KINESIS_SCA_LOG_STREAM,
                                  PartitionKey=self.log_group_name)

    def flush(self):
        self.acquire()
        try:
            byte_stream = io.BytesIO()
            with gzip.GzipFile(mode='wb', fileobj=byte_stream) as gz:
                for record in self.buffer:
                    gz.write(f"{self.format(record)} \n".encode('utf-8'))

            # TODO@vkara Remove once the library is tested and stabilized.
            # byte_stream.seek(0)
            # with gzip.GzipFile(mode='rb', fileobj=byte_stream) as reader:
            #     a = reader.readlines()
            #     for rec in a:
            #         print(rec.decode('utf-8'))

            self.upload_to_kinesis(byte_stream)
            self.clear_buffer()
        finally:
            self.release()


class SCALoggerException(Exception):
    pass
