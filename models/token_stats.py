from datetime import datetime
from decimal import Decimal
from typing import Union
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_serializer

class TokenStats(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    symbol: str
    
    coin_name: str
    coingecko_id: str
    market_cap: Union[Decimal, str, None] = Field(default=None)
    trading_volume_24h: Union[Decimal, str, None] = Field(default=None)
    token_max_supply: Union[int, str, None] = Field(default=None)
    token_total_supply: Union[int, str, None] = Field(default=None)
    transactions_count_30d: Union[int, str, None] = Field(default=None)
    volume_1m_change_1m: Union[int, str, None] = Field(default=None)
    volume_24h_change_24h: Union[Decimal, str, None] = Field(default=None)
    price: Union[Decimal, str, None] = Field(default=None)
    ath: Union[Decimal, str, None] = Field(default=None)
    atl: Union[Decimal, str, None] = Field(default=None)
    liquidity_score: Union[Decimal, str, None] = Field(default=None)
    tvl: Union[Decimal, str, None] = Field(default=None)
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_deleted: bool = Field(default=False)

    @field_serializer('id', 'created_at', 'updated_at')
    def serialize_id(self, value: UUID | datetime, _info):
        return str(value)