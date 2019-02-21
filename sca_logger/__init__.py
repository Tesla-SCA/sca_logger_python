import functools
import gzip
import io
import logging
import os
from logging.handlers import MemoryHandler

from sca_logger import utils

kinesis_client = utils.kinesis_client()
KINESIS_SCA_LOG_STREAM = os.environ['KINESIS_SCA_LOG_STREAM']
MEMORY_HANDLER_LOG_CAPACITY = int(os.getenv('MEMORY_HANDLER_LOG_CAPACITY', 1))


def logger(aws_request_id, _log_group_name):
    _sca_logger = logging.getLogger()
    _sca_logger.setLevel(logging.DEBUG)
    capacity = int(os.getenv('MEMORY_HANDLER_LOG_CAPACITY', 40))
    handler = SCAMemoryHandler(capacity=capacity,
                               log_group_name=_log_group_name)
    # [INFO]	2018-11-29T20:00:31.828Z	11e8-ba3f-79a3ec964b93	This is info msg
    formatter = logging.Formatter('[%(levelname)s]\t%(asctime)s.%(msecs)sZ\t%(aws_request_id)s\t%(message)s\n', '%Y-%m-%dT%H:%M:%S')
    handler.setFormatter(formatter)
    handler.addFilter(LambdaLoggerFilter(aws_request_id))
    for _handler in _sca_logger.handlers:
        _sca_logger.removeHandler(_handler)
    _sca_logger.addHandler(handler)
    return _sca_logger


class LambdaLoggerFilter(logging.Filter):
    def __init__(self, aws_request_id):
        super(LambdaLoggerFilter, self).__init__()
        self.aws_request_id = aws_request_id

    def filter(self, record):
        record.aws_request_id = self.aws_request_id
        return record.name == 'root'


def sca_log_decorator(func):
    logger_func = logger

    @functools.wraps(func)
    def handle_wrapper(event, context):
        lambda_execution_response = None
        if context.__class__.__name__ == 'LambdaContext':
            _log_group_name = context.log_group_name
            _aws_request_id = context.aws_request_id
            _logger = logger_func(_aws_request_id, _log_group_name)
            lambda_execution_response = func(event, context)
            # the atexit hooks are tricky with aws lambda as they have an altered python
            # thread implementation. So force flush to simulate atexit.register(logging.shutdown)
            _logger.handlers[0].flush()
        return lambda_execution_response

    return handle_wrapper


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

                # TODO@vkara Remove once the library is tested and stabilized.
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
