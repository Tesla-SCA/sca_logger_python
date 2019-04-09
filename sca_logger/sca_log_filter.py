import logging


class LambdaLoggerFilter(logging.Filter):
    def __init__(self, aws_request_id: str, event: dict, config_args=None):
        if config_args is None:
            config_args = {}
        super(LambdaLoggerFilter, self).__init__()
        self.aws_request_id = aws_request_id
        self.event = event
        self.config_args = config_args

    def filter(self, record: logging.LogRecord) -> bool:
        record.aws_request_id = self.aws_request_id
        if self.config_args['log_event']:
            record.event = self.event
        return record.name == 'root'
