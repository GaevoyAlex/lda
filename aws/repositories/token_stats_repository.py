from datetime import datetime
from aws.dynamodb_connector import DynamoDBConnector
from aws.repositories.generic_repository import DynamoRepository
from aws.tables_schemas import TokenStats

from models.token_stats import TokenStats as model_

class TokenStatsRepository(DynamoRepository):
    _connector = None
    
    def __init__(self):
        if TokenStatsRepository._connector is None:
            TokenStatsRepository._connector = DynamoDBConnector().initiate_connection()
        super().__init__(TokenStatsRepository._connector, TokenStats.table_name)

    def get_by_symbol(self, symbol: str) -> dict | None:
        items = self.query_by_attr('symbol', symbol)
        return items[0] if items else None

    def create_or_update(self, token_stats: model_) -> dict:
        new_item = token_stats.model_dump()
        
        existing_item = self.get_by_symbol(token_stats.symbol)
        
        if existing_item:
            update_expressions = []
            expression_attribute_values = {}
            expression_attribute_names = {}
            
            immutable_fields = {'id', 'created_at', 'symbol', 'updated_at'}
            
            for field, value in new_item.items():
                if field not in immutable_fields and value is not None:
                    if existing_item.get(field) != value:
                        update_expressions.append(f"#{field} = :{field}")
                        expression_attribute_names[f"#{field}"] = field
                        expression_attribute_values[f":{field}"] = value
            
            if update_expressions:
                update_expressions.append("#updated_at = :updated_at")
                expression_attribute_names["#updated_at"] = "updated_at"
                expression_attribute_values[":updated_at"] = str(datetime.now())
                
                update_expression = "SET " + ", ".join(update_expressions)
                
                try:
                    self.table.update_item(
                        Key={'id': existing_item['id']},
                        UpdateExpression=update_expression,
                        ExpressionAttributeNames=expression_attribute_names,
                        ExpressionAttributeValues=expression_attribute_values,
                        ReturnValues="NONE"
                    )
                except Exception as e:
                    print(f"Error updating token stats for {token_stats.symbol}: {e}")
                    
                return existing_item
            else:
                return existing_item
        else:
            self.create(new_item)
            return new_item

    def get_all(self) -> list[dict]:
        response = self.table.scan()
        return response.get('Items', [])