from aws.dynamodb_connector import DynamoDBConnector
from aws.repositories.generic_repository import DynamoRepository
from aws.tables_schemas import Exchanges

from models.exchanges import Exchange as model_

class ExchangeRepository(DynamoRepository):
    _connector = None
    
    def __init__(self):
        if ExchangeRepository._connector is None:
            ExchangeRepository._connector = DynamoDBConnector().initiate_connection()
        super().__init__(ExchangeRepository._connector, Exchanges.table_name)

    def get_by_name(self, name: str) -> dict | None:
        items = self.query_by_attr('name', name)
        return items[0] if items else None

    def create_if_not_exists(self, exchange: model_) -> dict:
        existing_item = self.get_by_name(exchange.name)
        if existing_item:
            return existing_item
    
        new_item = exchange.model_dump()
        self.create(new_item)
        return new_item

    def get_all(self) -> list[dict]:
        response = self.table.scan()
        return response.get('Items', [])