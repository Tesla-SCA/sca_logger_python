import base64
import gzip
import io
import logging
import os
import unittest
from unittest import mock

from nose import tools

from sca_logger import SCALoggerException, SCAMemoryHandler, sca_log_decorator
from tests.test_base import BaseSCATest


class LambdaContext:
    log_group_name = 'test_log_group_name'
    aws_request_id = '11e8-ba3f-79a3ec964b93'


@tools.istest
class TestReadFromKinesis(unittest.TestCase):
    def test_reading_sca_logger_content_from_kinesis(self):
        data = 'H4sIAOZOCFwC/4t2cXUKdY/lNDIwtNA1NNI1MA0xMrIytLQytNAzNzKO4kxONU9NNkxJ0k2zABKGhqkWuknmBpa6iaYpJkbGZmZGKakmnCEZmcUKQJSal6KQn6aQkZiXkpPKBQBy0FVQXAAAAA=="'
        foo = base64.b64decode(data)
        bio = io.BytesIO()
        bio.write(foo)
        bio.seek(0)
        with gzip.GzipFile(mode='rb', fileobj=bio) as reader:
            a = reader.readlines()
            for rec in a:
                result = rec.decode('utf-8')
                self.assertTrue('This is end of handle' in result)


@tools.istest
class TestSCALogDecoratorForLambda(BaseSCATest):
    @staticmethod
    @sca_log_decorator
    def some_handler(event, context):
        try:
            log = logging.getLogger()
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
