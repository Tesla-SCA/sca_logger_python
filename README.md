# SCA Logger

- A library used to collect all the AWS Lambda execution logs to AWS Kinesis
- This is ideal for sending logs to third party applications such as splunk rather than using the native less intutive cloudwatch

## Usage

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

#### Configuration

  - **MEMORY_HANDLER_LOG_CAPACITY** (defaults to 1)
     Size of the in memory buffer. The library flushes (puts a record in kinesis) if the capacity is hit
	 
  - **KINESIS_SCA_LOG_STREAM***
     Name of the AWS kinesis stream. The application using this library must provide this.


#### Tests

```shell
docker-compose build test
docker-compose up test
```

#### Implementation Details
>  Updating up shortly!
