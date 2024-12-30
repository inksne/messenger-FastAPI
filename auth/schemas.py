from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
from typing import Optional


class UserSchema(BaseModel):
    model_config = ConfigDict(strict=True, from_attributes=True)
    username: str
    password: str | bytes
    email: Optional[EmailStr] = None
    active: bool = True

    @classmethod
    def from_attributes(cls, obj):
        return cls(
            username=obj.username,
            password=obj.password,
            email=obj.email,
            active=obj.active
        )
    
    @field_validator('email', mode='before')
    def check_email(cls, v):
        if v in [None, '', 'null'] or '@.' not in v:
            return None
        return v