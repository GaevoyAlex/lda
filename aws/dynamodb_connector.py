import boto3
from botocore.exceptions import ClientError
from configs.config import settings
from aws.tables_schemas import Tokens, TokenStats, TokenPlatform, Exchanges, ExchangesStats

from typing import Self

class DynamoDBConnector:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self.resource = boto3.resource(
                'dynamodb',
                aws_access_key_id=settings.AWS.DYNAMO_ACCESS_KEY,
                aws_secret_access_key=settings.AWS.DYNAMO_SECRET_ACCESS_KEY,
                region_name=settings.AWS.DYNAMO_REGION_NAME
            )
            self.client = self.resource.meta.client
            self._table_check_done = False
            DynamoDBConnector._initialized = True

    def initiate_connection(self) -> Self:
        if not self._table_check_done:
            schemas = [Tokens, TokenStats, TokenPlatform, Exchanges, ExchangesStats]

            for table in schemas:
                try:
                    self.client.describe_table(TableName=table.table_name)
                except ClientError as e:
                    if e.response['Error']['Code'] == 'ResourceNotFoundException':
                        self.client.create_table(
                            TableName=table.table_name,
                            KeySchema=table.key_schema,
                            AttributeDefinitions=table.attribute_definitions,
                            ProvisionedThroughput=table.provisioned_throughput
                        )
            
            self._table_check_done = True
        return self