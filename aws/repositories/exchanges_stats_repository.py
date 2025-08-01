from datetime import datetime
from aws.dynamodb_connector import DynamoDBConnector
from aws.repositories.generic_repository import DynamoRepository
from aws.tables_schemas import ExchangesStats

from models.exchanges_stats import ExchangesStats as model_

class ExchangesStatsRepository(DynamoRepository):
    _connector = None
    
    def __init__(self):
        if ExchangesStatsRepository._connector is None:
            ExchangesStatsRepository._connector = DynamoDBConnector().initiate_connection()
        super().__init__(ExchangesStatsRepository._connector, ExchangesStats.table_name)

    def get_by_exchange_id(self, exchange_id: str) -> dict | None:
        items = self.query_by_attr('exchange_id', exchange_id)
        return items[0] if items else None
    
    def get_by_name(self, name: str) -> dict | None:
        items = self.query_by_attr('name', name)
        return items[0] if items else None

    def create_or_update(self, exchanges_stats: model_) -> dict:
        new_item = exchanges_stats.model_dump()

        existing_item = None
        if hasattr(exchanges_stats, 'exchange_id') and exchanges_stats.exchange_id:
            existing_item = self.get_by_exchange_id(str(exchanges_stats.exchange_id))
        
        if not existing_item and hasattr(exchanges_stats, 'name') and exchanges_stats.name:
            existing_item = self.get_by_name(exchanges_stats.name)

        if existing_item:
            update_expressions = []
            expression_attribute_values = {}
            expression_attribute_names = {}
            
            immutable_fields = {'id', 'created_at', 'updated_at'}
            
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
                    response = self.table.update_item(
                        Key={'id': existing_item['id']},
                        UpdateExpression=update_expression,
                        ExpressionAttributeNames=expression_attribute_names,
                        ExpressionAttributeValues=expression_attribute_values,
                        ReturnValues="ALL_NEW"
                    )
                    return response.get('Attributes', existing_item)
                except Exception as e:
                    print(f"Error updating exchange stats: {e}")
                    return existing_item
            else:
                return existing_item
        else:
            try:
                self.create(new_item)
                return new_item
            except Exception as e:
                print(f"Error creating exchange stats: {e}")
                return new_item

    def get_all(self) -> list[dict]:
        response = self.table.scan()
        return response.get('Items', [])