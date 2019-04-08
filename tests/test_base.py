import inspect
import logging
import os
import time
import unittest

from nose import tools

from sca_logger import KINESIS_SCA_LOG_STREAM, SCAMemoryHandler, sca_log_decorator, utils


@tools.nottest
class BaseSCATest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.kinesis_client = utils.kinesis_client()
        streams = cls.kinesis_client.list_streams()
        if not ('StreamNames' in streams and KINESIS_SCA_LOG_STREAM in streams['StreamNames']):
            cls.kinesis_client.create_stream(StreamName=KINESIS_SCA_LOG_STREAM, ShardCount=1)
        time.sleep(0.5)

    @classmethod
    def tearDownClass(cls):
        streams = cls.kinesis_client.list_streams()
        if 'StreamNames' in streams and KINESIS_SCA_LOG_STREAM in streams['StreamNames']:
            cls.kinesis_client.delete_stream(StreamName=KINESIS_SCA_LOG_STREAM)
        time.sleep(0.5)

    @staticmethod
    def mocked_mem_handler_class(capacity):
        caller = inspect.stack()[1][3]
        return SCAMemoryHandler(capacity=capacity, log_group_name=caller)

    @staticmethod
    @sca_log_decorator
    def lambda_function_simulator_log_till_warn(event, context):
        """
            Function simulating the aws lambda's handler. It invokes logger as if a typical
            application is trying to log.
            The below helper tries to log 4 times.
        """
        my_logger = logging.getLogger()
        if os.getenv('SCA_LOG_LEVEL') is not None:
            my_logger.setLevel(int(os.getenv('SCA_LOG_LEVEL')))
        my_logger.debug('This is an debug message')
        my_logger.info('This is an info message')
        my_logger.warning('This is an warn message')
        my_logger.info('This is yet another info message')

    @staticmethod
    @sca_log_decorator
    def lambda_function_simulator_log_while_exception(event, context):
        """
            Function simulating the aws lambda's handler. It invokes logger as if a typical
            application is trying to log.
            The below helper tries to log 4 times.
        """
        BaseSCATest.lambda_function_simulator_log_till_warn(event, context)
        raise Exception("Test exception logging")

    @staticmethod
    @sca_log_decorator
    def lambda_function_simulator_log_all_levels(event, context):
        """
            Function simulating the aws lambda's handler. It invokes logger as if a typical
            application is trying to log.
            The below helper tries to log 4 times.
        """
        my_logger = logging.getLogger()
        if os.getenv('SCA_LOG_LEVEL') is not None:
            my_logger.setLevel(int(os.getenv('SCA_LOG_LEVEL')))
        my_logger.debug('This is an debug message')
        my_logger.info('This is an info message')
        my_logger.warning('This is an warn message')
        my_logger.error('This is an error message')
        my_logger.critical('This is an critical message')


@tools.nottest
class BaseSCATestKinesis(BaseSCATest):
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.kinesis_client = utils.kinesis_client()
        streams = self.kinesis_client.list_streams()
        if not ('StreamNames' in streams and KINESIS_SCA_LOG_STREAM in streams['StreamNames']):
            self.kinesis_client.create_stream(StreamName=KINESIS_SCA_LOG_STREAM, ShardCount=1)
        time.sleep(0.5)

    def tearDown(self):
        streams = self.kinesis_client.list_streams()
        if 'StreamNames' in streams and KINESIS_SCA_LOG_STREAM in streams['StreamNames']:
            self.kinesis_client.delete_stream(StreamName=KINESIS_SCA_LOG_STREAM)
        time.sleep(0.5)
