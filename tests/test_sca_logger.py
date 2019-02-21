import base64
import gzip
import io
import logging
import os
import re
from unittest import mock

import datetime
from nose import tools

from sca_logger import KINESIS_SCA_LOG_STREAM, SCAMemoryHandler
from tests.test_base import BaseSCATest, BaseSCATestKinesis


class LambdaContext:
    log_group_name = 'test_log_group_name'
    aws_request_id = '11e8-ba3f-79a3ec964b93'


@tools.istest
class TestSCALoggerFlush(BaseSCATest):
    def test_logging_produces_no_errors(self):
        self.lambda_function_simulator_log_till_warn({}, LambdaContext())

    # *************** Test Flush from Handler *************** *************** ***************
    # The use of decorator is mandatory for using the sca_logger_python module. This takes care
    # executing the aws lambda handler function, apart from initializing the logger module and
    # a forced flush towards the end, which is the last flush call from a logger (usually triggered
    # by atexit)
    # The below unit tests are terminated before the final 'shutdown' on logger is invoked.
    # # *************** *************** *************** *************** ***************

    @mock.patch.object(SCAMemoryHandler, 'upload_to_kinesis')
    def test_logging_flush_at_2_mem_capacity_non_error(self, kinesis):
        """
            Logging: 4 non-error logs
            Mem handler will flush twice as buff size is 2 before it exists
        """
        sca_mem_handler = self.mocked_mem_handler_class(2)
        with mock.patch('sca_logger.SCAMemoryHandler', return_value=sca_mem_handler):
            with mock.patch.object(sca_mem_handler, 'flush', wraps=sca_mem_handler.flush) as log:
                self.lambda_function_simulator_log_till_warn({}, LambdaContext())
                self.assertEquals(log.call_count, 3)
        self.assertTrue(kinesis.called)

    def test_logging_flush_at_3_mem_capacity_non_error(self):
        """
            Logging: 4 non-error logs
            Mem handler will flush once before exit as buff size is 3 and also flush once
                before atexit
        """
        sca_mem_handler = self.mocked_mem_handler_class(3)
        with mock.patch('sca_logger.SCAMemoryHandler', return_value=sca_mem_handler):
            with mock.patch.object(sca_mem_handler, 'flush', wraps=sca_mem_handler.flush) as log:
                self.lambda_function_simulator_log_till_warn({}, LambdaContext())
                self.assertEquals(log.call_count, 2)

    def test_logging_flush_at_max_mem_capacity_non_error(self):
        """
            Logging: 4 non-error logs
            Mem handler will not flush before exit as buff size is bigger than logged content
                and will flush once before atexit
        """
        sca_mem_handler = self.mocked_mem_handler_class(10)
        with mock.patch('sca_logger.SCAMemoryHandler', return_value=sca_mem_handler):
            with mock.patch.object(sca_mem_handler, 'flush', wraps=sca_mem_handler.flush) as log:
                self.lambda_function_simulator_log_till_warn({}, LambdaContext())
                self.assertEquals(log.call_count, 1)

    def test_logging_flush_at_max_mem_capacity_error(self):
        """
            Logging: 5 logs including error and critical
            Mem handler will flush twice before exit as flush level is set to ERROR, Even
                though buff size is bigger than logged content. It will also flush once before
                atexit
        """
        sca_mem_handler = self.mocked_mem_handler_class(10)
        with mock.patch('sca_logger.SCAMemoryHandler', return_value=sca_mem_handler):
            with mock.patch.object(sca_mem_handler, 'flush', wraps=sca_mem_handler.flush) as log:
                self.lambda_function_simulator_log_all_levels({}, LambdaContext())
                self.assertEquals(log.call_count, 3)

    @mock.patch.dict(os.environ, {'SCA_LOG_LEVEL': str(logging.INFO)})
    def test_logging_info_at_unit_capacity(self):
        # Logging: 4 as log level is set to INFO (logs all except DEBUG)
        sca_mem_handler = self.mocked_mem_handler_class(1)
        with mock.patch('sca_logger.SCAMemoryHandler', return_value=sca_mem_handler):
            with mock.patch.object(sca_mem_handler, 'flush', wraps=sca_mem_handler.flush) as log:
                self.lambda_function_simulator_log_all_levels({}, LambdaContext())
                self.assertEquals(log.call_count, 5)

    @mock.patch.dict(os.environ, {'SCA_LOG_LEVEL': str(logging.ERROR)})
    def test_logging_error_at_unit_capacity(self):
        # Logging: 3 as log level is set to ERROR (only ERROR, CRITICAL)
        sca_mem_handler = self.mocked_mem_handler_class(1)
        with mock.patch('sca_logger.SCAMemoryHandler', return_value=sca_mem_handler):
            with mock.patch.object(sca_mem_handler, 'flush', wraps=sca_mem_handler.flush) as log:
                logging.getLogger().setLevel(logging.ERROR)
                self.lambda_function_simulator_log_all_levels({}, LambdaContext())
                self.assertEquals(log.call_count, 3)

    @mock.patch.dict(os.environ, {'SCA_LOG_LEVEL': str(logging.CRITICAL)})
    def test_logging_critical_at_unit_capacity(self):
        # Logging: 4 as log level is set to CRITICAL (only CRITICAL)
        sca_mem_handler = self.mocked_mem_handler_class(1)
        with mock.patch('sca_logger.SCAMemoryHandler', return_value=sca_mem_handler):
            with mock.patch.object(sca_mem_handler, 'flush', wraps=sca_mem_handler.flush) as log:
                logging.getLogger().setLevel(logging.ERROR)
                self.lambda_function_simulator_log_all_levels({}, LambdaContext())
                self.assertEquals(log.call_count, 2)


# # ***************** ************************** *****************
# # ***************** Test kinesis integration # *****************
# # ***************** ************************** *****************
@tools.istest
class TestSCALoggerKinesisIntegration(BaseSCATestKinesis):
    @mock.patch.dict(os.environ, {'MEMORY_HANDLER_LOG_CAPACITY': '1'})
    def test_payloads_are_in_kinesis_expecting_4_puts(self):
        """
            Logging: 4 non-error logs
            Since the buffer size is 1, it must flush each time.
        """
        self.lambda_function_simulator_log_till_warn({}, LambdaContext())
        stream = self.kinesis_client.describe_stream(StreamName=KINESIS_SCA_LOG_STREAM)
        shard_id = stream['StreamDescription']['Shards'][0]['ShardId']
        shard_iterator = self.kinesis_client.get_shard_iterator(StreamName=KINESIS_SCA_LOG_STREAM,
                                                                ShardId=shard_id,
                                                                ShardIteratorType='TRIM_HORIZON')
        shard_iterator = shard_iterator['ShardIterator']
        record_response = self.kinesis_client.get_records(ShardIterator=shard_iterator)
        self.assertEquals(len(record_response['Records']), 4)

    @mock.patch.dict(os.environ, {'MEMORY_HANDLER_LOG_CAPACITY': '2'})
    def test_payloads_are_in_kinesis_expecting_2_puts(self):
        """
            Logging: 4 non-error logs
            Since the buffer size is 2, it must flush twice before exit.
        """
        self.lambda_function_simulator_log_till_warn({}, LambdaContext())
        stream = self.kinesis_client.describe_stream(StreamName=KINESIS_SCA_LOG_STREAM)
        shard_id = stream['StreamDescription']['Shards'][0]['ShardId']
        shard_iterator = self.kinesis_client.get_shard_iterator(StreamName=KINESIS_SCA_LOG_STREAM,
                                                                ShardId=shard_id,
                                                                ShardIteratorType='TRIM_HORIZON')
        shard_iterator = shard_iterator['ShardIterator']
        record_response = self.kinesis_client.get_records(ShardIterator=shard_iterator)
        self.assertEquals(len(record_response['Records']), 2)

    @mock.patch.dict(os.environ, {'MEMORY_HANDLER_LOG_CAPACITY': '10'})
    def test_payloads_are_in_kinesis_expecting_0_puts(self):
        """
            Logging: 4 non-error logs
            Since the buffer size is 10, it must not flush before exit.
        """
        self.lambda_function_simulator_log_till_warn({}, LambdaContext())
        stream = self.kinesis_client.describe_stream(StreamName=KINESIS_SCA_LOG_STREAM)
        shard_id = stream['StreamDescription']['Shards'][0]['ShardId']
        shard_iterator = self.kinesis_client.get_shard_iterator(StreamName=KINESIS_SCA_LOG_STREAM,
                                                                ShardId=shard_id,
                                                                ShardIteratorType='TRIM_HORIZON')
        shard_iterator = shard_iterator['ShardIterator']
        record_response = self.kinesis_client.get_records(ShardIterator=shard_iterator)
        for record in record_response['Records']:
            reader(record['Data'])
        self.assertEquals(len(record_response['Records']), 1)

    @mock.patch.dict(os.environ, {'MEMORY_HANDLER_LOG_CAPACITY': '10'})
    def test_payloads_are_in_kinesis_expecting_2_puts_error_logs(self):
        """
            Logging: 5 logs including error and critical
            Since the buffer size is 10, it must not flush before exit.
        """
        self.lambda_function_simulator_log_all_levels({}, LambdaContext())
        stream = self.kinesis_client.describe_stream(StreamName=KINESIS_SCA_LOG_STREAM)
        shard_id = stream['StreamDescription']['Shards'][0]['ShardId']
        shard_iterator = self.kinesis_client.get_shard_iterator(StreamName=KINESIS_SCA_LOG_STREAM,
                                                                ShardId=shard_id,
                                                                ShardIteratorType='TRIM_HORIZON')
        shard_iterator = shard_iterator['ShardIterator']
        record_response = self.kinesis_client.get_records(ShardIterator=shard_iterator)
        # for record in record_response['Records']:
        #     reader(record['Data'])
        #     print(datetime.datetime.now().isoformat())
        self.assertEquals(len(record_response['Records']), 2)

#
# def reader(data):
#     gzipped_bytes = data
#     bio = io.BytesIO()
#     bio.write(gzipped_bytes)
#     bio.seek(0)
#     with gzip.GzipFile(mode='rb', fileobj=bio) as reader:
#         a = reader.readlines()
#         for rec in a:
#             print(rec.decode('utf-8'))
