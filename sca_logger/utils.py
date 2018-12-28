import os

import boto3


def kinesis_client():
    # This env variable must be set only in testing to reference local kinesis
    # This will match the docker compose task definition of kinesis
    use_local = os.getenv('USE_LOCALSTACK', False) == 'True'
    if use_local:
        host = os.getenv('LOCALSTACK_KINESIS_HOST', 'localhost')
        port = os.getenv('LOCALSTACK_KINESIS_PORT', 5000)
        return boto3.client('kinesis', endpoint_url=f'http://{host}:{port}')
    else:
        return boto3.client('kinesis')
