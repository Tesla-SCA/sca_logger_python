import datetime
import logging

JSON_LOG_KEYS = ['aws_request_id', 'asctime', 'filename', 'funcName', 'levelname', 'message',
                 'exc_info']


class SCAFormatter(logging.Formatter):
    def __init__(self, config_params: dict, frmt: str):
        super(SCAFormatter, self).__init__(frmt)
        self.config_params = config_params

    def formatTime(self, record: logging.LogRecord, datefmt=None) -> str:
        timestamp = record.created
        py_datetime = datetime.datetime.fromtimestamp(timestamp)
        return py_datetime.isoformat()

    def format(self, record: logging.LogRecord) -> str or dict:
        message = super(SCAFormatter, self).format(record)
        if self.config_params['marshal_as_json']:
            try:
                response = dict()
                for _key in JSON_LOG_KEYS:
                    if getattr(record, _key, None):
                        response[_key] = getattr(record, _key)
                response['event'] = getattr(record, 'event', None)
                response['message'] = message
                return response
            except Exception:
                return message
        else:
            return message
