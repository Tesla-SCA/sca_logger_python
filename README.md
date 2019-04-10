

# SCA Logger [![PyPI version](https://badge.fury.io/py/sca_logger_python.svg)](https://badge.fury.io/py/sca_logger_python)
 
- A library used to collect all the AWS Lambda execution logs to AWS Kinesis
- This is ideal for sending logs to third party applications such as splunk rather than using the native less intuitive cloudwatch

#### Supported Log structures
   - String
   `[DEBUG] - 2018-12-01 02:27:29,489 - eb4d0cdd-f50f-11e8-8feb-6fda225bd190 - This is end of handle`
   
   - JSON
   ```json
   {
	   "asctime":"2019-04-09T22:32:49.250056",
	   "aws_request_id":"9711b10a-e4b6-4be3-b5ed-0849fcd087ec",
	   "event":{
	      "key1":"value1",
	      "key2":"value2",
	      "key3":"value3"
	   },
	   "filename":"handler.py",
	   "funcName":"handle",
	   "levelname":"DEBUG",
	   "message":"[DEBUG]\t2019-04-09T22:32:49.250056Z\t9711b10a-e4b6-4be3-b5ed-0849fcd087ec\tThis is end of handle\n"
   }
   ```
   

#### Log packaging in kinesis
<img src="https://github.com/Tesla-SCA/sca_logger_python/blob/master/image.png" width="500" height="450">

## Usage
- Application trying to log

```python
import logging
from sca_logger import sca_log_decorator
 
@sca_log_decorator(log_as_json=True, log_event=False)
def handle(event, context):
	log = logging.getLogger()
	log.info("This is info message")
	log.debug("This is start of handle")
		# application logic
	log.debug("This is end of handle")
```

- Application consuming the log from kinesis

```python
import base64
import gzip
import io
import json

def reader(kinesis_event):
    data = kinesis_event['Records'][0]['Data']
    gzipped_bytes = base64.b64decode(data)
    bio = io.BytesIO()
    bio.write(gzipped_bytes)
    bio.seek(0)
    with gzip.GzipFile(mode='rb', fileobj=bio) as gz_reader:
        byte_data = gz_reader.read()
    records = json.loads(byte_data.decode("utf-8"))
    for record in records:
        print(record)
```

## Configuration

  - **MEMORY_HANDLER_LOG_CAPACITY** (defaults to 40)
     Size of the in memory buffer. The library flushes (puts a record in kinesis) if the capacity is hit
	 
  - **KINESIS_SCA_LOG_STREAM***
     Name of the AWS kinesis stream. The application using this library must provide this.
     
  - **JSON Logging***
     The ```python @sca_log_decorator``` accepts the following arguments.
     - ```python log_as_json: bool ``` True logs as json. False logs as str. Default is set to True
     - ```python log_event: bool ``` True logs the complete event. False does not log anything in event. Default is set to True


## Tests

```shell
docker-compose build test
docker-compose up test
```

## Package on Pypi
change the version in setup.py
```shell
python setup.py sdist upload -r pypi
```
 

## Implementation Details
>  Updating shortly!
