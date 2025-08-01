import boto3
from botocore.exceptions import ClientError
from typing import Self

from configs.config import settings
from aws.tables_schemas import TABLE_SCHEMAS


class DynamoDBConnector:
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._init_connection()
            self._table_check_done = False
            DynamoDBConnector._initialized = True

    def _init_connection(self):
        self.resource = boto3.resource(
            'dynamodb',
            aws_access_key_id=settings.AWS.DYNAMO_ACCESS_KEY,
            aws_secret_access_key=settings.AWS.DYNAMO_SECRET_ACCESS_KEY,
            region_name=settings.AWS.DYNAMO_REGION_NAME
        )
        self.client = self.resource.meta.client

    def initiate_connection(self) -> Self:
        if not self._table_check_done:
            self._ensure_tables_exist()
            self._table_check_done = True
        return self

    def _ensure_tables_exist(self):
        for table_schema in TABLE_SCHEMAS:
            self._create_table_if_not_exists(table_schema)

    def _create_table_if_not_exists(self, table_schema):
        try:
            self.client.describe_table(TableName=table_schema.table_name)
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                self._create_table(table_schema)

    def _create_table(self, table_schema):
        self.client.create_table(
            TableName=table_schema.table_name,
            KeySchema=table_schema.key_schema,
            AttributeDefinitions=table_schema.attribute_definitions,
            ProvisionedThroughput=table_schema.provisioned_throughput
        )