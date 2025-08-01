class BaseTableSchema:
    attribute_definitions = [
        {"AttributeName": "id", "AttributeType": "S"},
    ]
    key_schema = [
        {"AttributeName": "id", "KeyType": "HASH"},
    ]
    provisioned_throughput = {
        'ReadCapacityUnits': 5,
        'WriteCapacityUnits': 5
    }


class Tokens(BaseTableSchema):
    table_name = 'LiberandumAggregationToken'


class TokenPlatform(BaseTableSchema):
    table_name = 'LiberandumAggregationTokenPlatform'


class TokenStats(BaseTableSchema):
    table_name = 'LiberandumAggregationTokenStats'


class Exchanges(BaseTableSchema):
    table_name = 'LiberandumAggregationExchanges'


class ExchangesStats(BaseTableSchema):
    table_name = 'LiberandumAggregationExchangesStats'


TABLE_SCHEMAS = [
    Tokens,
    TokenStats, 
    TokenPlatform,
    Exchanges,
    ExchangesStats
]