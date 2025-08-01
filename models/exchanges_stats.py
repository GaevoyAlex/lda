from datetime import datetime
from decimal import Decimal
from typing import List, Union
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_serializer

class ExchangesStats(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    exchange_id: UUID
    
    name:str
    inflows_1m: List[Decimal] = Field(default=[])
    inflows_1w: List[Decimal] = Field(default=[])
    inflows_24h: List[Decimal] = Field(default=[])
    trading_volume_1m: Union[Decimal, str, None] = Field(default=None)
    trading_volume_1w: Union[Decimal, str, None] = Field(default=None)
    trading_volume_24h: Union[Decimal, str, None] = Field(default=None)
    visitors_30d: Union[int, str, None] = Field(default=None)
    reserves: Union[Decimal, str, None] = Field(default=None)
    list_supported: List[str] = Field(default=[])
    coins_count: int | None = Field(default=None)
    effective_liquidity_24h: Decimal | None = Field(default=None)
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_deleted: bool = Field(default=False)

    @field_serializer('id', 'exchange_id', 'created_at', 'updated_at')
    def serialize_id(self, value: UUID | datetime, _info):
        return str(value)