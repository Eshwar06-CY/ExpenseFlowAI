from typing import Optional
from pydantic import BaseModel, ConfigDict, field_validator

class CategoryBase(BaseModel):
    name: str
    type: str
    icon: Optional[str] = None
    color: Optional[str] = None

class CategoryCreate(CategoryBase):
    @field_validator("type")
    @classmethod
    def validate_type(cls, v: str) -> str:
        valid_types = {"income", "expense", "both"}
        if v.lower() not in valid_types:
            raise ValueError(f"Category type must be one of {valid_types}")
        return v.lower()

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None

    @field_validator("type")
    @classmethod
    def validate_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid_types = {"income", "expense", "both"}
            if v.lower() not in valid_types:
                raise ValueError(f"Category type must be one of {valid_types}")
            return v.lower()
        return v

class CategoryResponse(CategoryBase):
    id: int
    user_id: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)
