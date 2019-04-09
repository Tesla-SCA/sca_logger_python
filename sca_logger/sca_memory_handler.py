import gzip
import io
import json
import logging
import os
from io import BytesIO
from logging.handlers import MemoryHandler

from sca_logger import utils

kinesis_client = utils.kinesis_client()
KINESIS_SCA_LOG_STREAM = os.environ['KINESIS_SCA_LOG_STREAM']
MEMORY_HANDLER_LOG_CAPACITY = int(os.getenv('MEMORY_HANDLER_LOG_CAPACITY', 1))


class SCAMemoryHandler(MemoryHandler):
    def __init__(self, capacity: int, log_group_name: str):
        self.log_group_name = log_group_name
        logging.Handler.__init__(self)
        super().__init__(capacity=capacity)

    def upload_to_kinesis(self, byte_stream: BytesIO) -> None:
        kinesis_client.put_record(Data=byte_stream.getvalue(),
                                  StreamName=KINESIS_SCA_LOG_STREAM,
                                  PartitionKey=self.log_group_name)

    def flush(self):
        self.acquire()
        try:
            if len(self.buffer) != 0:
                formatted_records = list()
                byte_stream = io.BytesIO()
                with gzip.GzipFile(mode='wb', fileobj=byte_stream) as gz:
                    for record in self.buffer:
                        formatted_records.append(self.format(record))
                    serialized_records = json.dumps(formatted_records, sort_keys=True, indent=4,
                                                    default=str)
                    gz.write(serialized_records.encode("utf-8"))
                self.upload_to_kinesis(byte_stream)
                byte_stream.close()
                self.buffer = []
        finally:
            self.release()
