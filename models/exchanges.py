from typing import List
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, field_serializer

from datetime import datetime

class Exchange(BaseModel):
    id: UUID = Field(default_factory=uuid4)

    name:                   str | None = Field(default=None)
    description:            str | None = Field(default=None)      
    islamic_account:        str | None = Field(default=None)          
    facebook:               str | None = Field(default=None)   
    youtube:                str | None = Field(default=None)  
    instagram:              str | None = Field(default=None)    
    medium:                 str | None = Field(default=None) 
    discord:                str | None = Field(default=None)  
    website:                str | None = Field(default=None)  
    twitter:                str | None = Field(default=None)  
    reddit:                 str | None = Field(default=None) 
    repo_link:              str | None = Field(default=None)    
    avatar_image:           str | None = Field(default=None)       
    native_token_symbol:    str | None = Field(default=None)              

    trading_pairs_count:    int | None = Field(default=None)

    security_audits:        List[UUID] = Field(default=[])
    related_people:         List[UUID]  = Field(default=[])

    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    is_deleted: bool = Field(default=False)

    @field_serializer('id', 'created_at', 'updated_at')
    def serialize_id(self, id: UUID, _info):
        return str(id)
