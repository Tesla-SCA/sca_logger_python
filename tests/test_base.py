import atexit
import inspect
import logging
import time
import unittest

from sca_logger import KINESIS_SCA_LOG_STREAM, SCAMemoryHandler, logger, utils


class BaseSCATest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.kinesis_client = utils.kinesis_client()
        atexit.unregister(logging.shutdown)
        atexit.register(cls._delete_kinesis_stream, cls.kinesis_client)
        atexit.register(logging.shutdown)
        if not cls._is_stream_present(cls.kinesis_client):
            cls.kinesis_client.create_stream(StreamName=KINESIS_SCA_LOG_STREAM, ShardCount=1)
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        time.sleep(0.5)

    @staticmethod
    def _delete_kinesis_stream(kinesis_client):
        if BaseSCATest._is_stream_present(kinesis_client):
            kinesis_client.delete_stream(StreamName=KINESIS_SCA_LOG_STREAM)

    @staticmethod
    def _is_stream_present(kinesis_client):
        streams = kinesis_client.list_streams()
        if 'StreamNames' in streams and KINESIS_SCA_LOG_STREAM in streams['StreamNames']:
            return True
        return False

    @staticmethod
    def mocked_mem_handler_class(capacity):
        caller = inspect.stack()[1][3]
        return SCAMemoryHandler(capacity=capacity, log_group_name=caller)

    def is_stream_present(self):
        streams = self.kinesis_client.list_streams()
        if 'StreamNames' in streams and KINESIS_SCA_LOG_STREAM in streams['StreamNames']:
            return True
        return False

    @staticmethod
    def log_until_warn_helper():
        my_logger = logger()
        my_logger.debug('This is an debug message')
        my_logger.info('This is an info message')
        my_logger.warning('This is an warn message')
        my_logger.info('This is yet another info message')

    @staticmethod
    def log_all_helper():
        my_logger = logger()
        my_logger.debug('This is an debug message')
        my_logger.info('This is an info message')
        my_logger.warning('This is an warn message')
        my_logger.error('This is an error message')
        my_logger.critical('This is an critical message')
