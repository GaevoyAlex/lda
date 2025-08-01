from aws.dynamodb_connector import DynamoDBConnector
from aws.repositories.generic_repository import DynamoRepository
from aws.tables_schemas import TokenPlatform

from models.platform import Platform as model_

class PlatformRepository(DynamoRepository):
    _connector = None
    
    def __init__(self):
        if PlatformRepository._connector is None:
            PlatformRepository._connector = DynamoDBConnector().initiate_connection()
        super().__init__(PlatformRepository._connector, TokenPlatform.table_name)

    def get_by_address(self, address: str) -> dict | None:
        items = self.query_by_attr('token_address', address)
        return items[0] if items else None

    def create_if_not_exists(self, platform: model_) -> dict:
        item = self.get_by_address(str(platform.token_address))
        if item:
            return item
        
        new_item = platform.model_dump()
        self.create(new_item)
        return new_item