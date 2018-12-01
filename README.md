# SCA Logger

- A library used to collect all the AWS Lambda execution logs to AWS Kinesis
- This is ideal for sending logs to third party applications such as splunk rather than using the native less intutive cloudwatch

#### Log structure
*[DEBUG] - 2018-12-01 02:27:29,489 - eb4d0cdd-f50f-11e8-8feb-6fda225bd190 - This is end of handle*

#### Log packaging in kinesis
<img src="https://github.com/Tesla-SCA/sca_logger_python/blob/master/logger.png" width="500" height="450">

## Usage
- Application trying to log

```python
import sca_logger
from sca_logger import sca_log_decorator

@sca_log_decorator
def handle(event, context):
	log = sca_logger.logger()
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

def reader(kinesis_event):
	data = kinesis_event['Records'][0]['Data']
	gzipped_bytes = base64.b64decode(data)
	bio = io.BytesIO()
	bio.write(gzipped_bytes)
	bio.seek(0)
	with gzip.GzipFile(mode='rb', fileobj=bio) as reader:
		a = reader.readlines()
		for rec in a:
		print(rec.decode('utf-8'))
```

## Configuration

  - **MEMORY_HANDLER_LOG_CAPACITY** (defaults to 1)
     Size of the in memory buffer. The library flushes (puts a record in kinesis) if the capacity is hit
	 
  - **KINESIS_SCA_LOG_STREAM***
     Name of the AWS kinesis stream. The application using this library must provide this.


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
>  Updating up shortly!
