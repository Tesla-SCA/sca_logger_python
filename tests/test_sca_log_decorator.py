import base64
import gzip
import io
import os
import unittest
from unittest import mock

import sca_logger
from sca_logger import SCALoggerException, SCAMemoryHandler, sca_log_decorator
from tests.test_base import BaseSCATest


class LambdaContext:
    log_group_name = 'test_log_group_name'
    aws_request_id = '11e8-ba3f-79a3ec964b93'


class TestVkara(unittest.TestCase):
    def test_demo(self):
        data = 'H4sIAJHxAVwC/w3KOwqAQAwA0d5T5AAGkuBn11IUL6CVWLgmQUG08P7gwnRv1mHsl2kDBCEOyILEQNJJ20ksqxCzWKqUDlX0mhyZLWBwS9i47iJ1Uo6Ut/m8PsjZo/A6nPujt0HxA6CkzEZiAAAA'
        foo = base64.b64decode(data)
        bio = io.BytesIO()
        bio.write(foo)
        bio.seek(0)
        with gzip.GzipFile(mode='rb', fileobj=bio) as reader:
            a = reader.readlines()
            for rec in a:
                print(rec.decode('utf-8'))
        print("v")


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
