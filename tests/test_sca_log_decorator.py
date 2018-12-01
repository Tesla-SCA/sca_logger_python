import os
from unittest import mock

import sca_logger
from sca_logger import SCALoggerException, SCAMemoryHandler, sca_log_decorator
from tests.test_base import BaseSCATest


class LambdaContext:
    log_group_name = 'test_log_group_name'
    aws_request_id = '11e8-ba3f-79a3ec964b93'


class TestSCALogDecorator0(BaseSCATest):
    @staticmethod
    @sca_log_decorator
    def some_handler(event, context):
        try:
            log = sca_logger.logger()
            log.info("This is info message")
            log.debug("This is debug message")
            return True
        except SCALoggerException as e:
            print(e)
            return False

    @mock.patch.dict(os.environ, {'MEMORY_HANDLER_LOG_CAPACITY': '1'})
    @mock.patch.object(SCAMemoryHandler, 'upload_to_kinesis')
    def test_decorator(self, kinesis):
        event = {}
        context = LambdaContext()
        response = self.some_handler(event, context)
        self.assertTrue(response)
        self.assertTrue(kinesis.called)
