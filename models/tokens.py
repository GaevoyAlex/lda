from datetime import datetime
import decimal
from typing import List
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_serializer

class Token(BaseModel):
    id: UUID = Field(default_factory=uuid4)

    coingecko_id: str | None = Field(default=None)

    exchanges: List[UUID]       = Field(default=[])
    security_audits: List[UUID] = Field(default=[])
    related_people: List[UUID]  = Field(default=[])

    name:            str | None = Field(default=None)
    symbol:          str | None = Field(default=None)
    description:     str | None = Field(default=None)
    instagram:       str | None = Field(default=None)
    discord:         str | None = Field(default=None)
    website:         str | None = Field(default=None)
    facebook:        str | None = Field(default=None)
    reddit:          str | None = Field(default=None)
    twitter:         str | None = Field(default=None)
    repo_link:       str | None = Field(default=None)
    whitelabel_link: str | None = Field(default=None)
    tvl: decimal.Decimal | None = Field(default=None)

    avatar_image: str | None = Field(default=None)

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_deleted: bool = Field(default=False)

    @field_serializer('id', 'created_at', 'updated_at')
    def serialize_id(self, id: UUID, _info):
        return str(id)