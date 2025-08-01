class Tokens:
    table_name = 'LiberandumAggregationToken'
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

class TokenPlatform:
    table_name = 'LiberandumAggregationTokenPlatform'
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

class TokenStats:
    table_name = 'LiberandumAggregationTokenStats'
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

class Exchanges:
    table_name = 'LiberandumAggregationExchanges'
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

class ExchangesStats:
    table_name = 'LiberandumAggregationExchangesStats'
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