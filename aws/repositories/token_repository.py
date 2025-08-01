from aws.dynamodb_connector import DynamoDBConnector
from aws.repositories.generic_repository import DynamoRepository
from aws.tables_schemas import Tokens

from models.tokens import Token as model_

class TokensRepository(DynamoRepository):
    _connector = None
    
    def __init__(self):
        if TokensRepository._connector is None:
            TokensRepository._connector = DynamoDBConnector().initiate_connection()
        super().__init__(TokensRepository._connector, Tokens.table_name)

    def get_by_symbol(self, symbol: str) -> dict | None:
        items = self.query_by_attr('symbol', symbol)
        return items[0] if items else None

    def get_by_coingecko_id(self, coingecko_id: str) -> dict | None:
        items = self.query_by_attr('coingecko_id', coingecko_id)
        return items[0] if items else None

    def create_if_not_exists(self, token: model_) -> dict:
        existing_item = None
        
        if token.coingecko_id:
            existing_item = self.get_by_coingecko_id(token.coingecko_id)
        
        if not existing_item and token.symbol:
            existing_item = self.get_by_symbol(token.symbol)
        
        if existing_item:
            return existing_item
    
        new_item = token.model_dump()
        self.create(new_item)
        return new_item

    def get_all(self) -> list[dict]:
        response = self.table.scan()
        return response.get('Items', [])