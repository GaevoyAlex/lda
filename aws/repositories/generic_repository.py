from boto3.dynamodb.conditions import Key, Attr
from typing import Optional

class DynamoRepository:
    def __init__(self, conn, table_name: str):
        self.table = conn.resource.Table(table_name)

    def create(self, item: dict) -> None:
        self.table.put_item(Item=item)

    def get_by_id(self, item_id: str) -> Optional[dict]:
        response = self.table.get_item(Key={'id': item_id})
        return response.get('Item')

    def query_by_attr(self, attr_name: str, value: str) -> list[dict]:
        response = self.table.scan(
            FilterExpression=Attr(attr_name).eq(value)
        )
        return response.get('Items', [])