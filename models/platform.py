from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_serializer

from datetime import datetime

class Platform(BaseModel):
    id: UUID = Field(default_factory=uuid4)

    token_id: UUID
    
    name: str
    token_address: str

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_deleted: bool = Field(default=False)

    @field_serializer('id', 'created_at', 'updated_at', 'token_id')
    def serialize_id(self, id: UUID, _info):
        return str(id)