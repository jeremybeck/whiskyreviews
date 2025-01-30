from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class Whiskey(BaseModel):
    year: Optional[int] = Field(None, description="The year the whiskey was bottled (if provided)")
    distillery: str = Field(..., description="The name of the distillery or bottler")
    distillery_region: Optional[str] = Field(None, description='The region the whiskey came from')
    whiskey_country_of_origin: Optional[str] = Field(None, description='The country the distillery is based in')
    whiskey_name: str = Field(..., description="The name of the whiskey without distiller or age")
    is_blend: Optional[str] = Field(None, description="Boolean (True/False) for whether the whiskey is a blended or single malt")
    age: Optional[int] = Field(None, description="The age of the whiskey, amount of time it was in a cask (in years)")
    whiskey_type: Optional[str] = Field(None, description="The type of whiskey (for example scotch, bourbon, irish, or rye")
    nose_tags: list[str] = Field(..., description='Keywords describing the nose/smell of the whiskey from the provided review')
    palette_tags: list[str] = Field(..., description='Keywords describing the nose/smell of the whiskey from the provided review')
    finish_tags: list[str] = Field(..., description="Keywords describing the finish of the whiskey")

class WhiskeyReview(Whiskey):
    uuid: str = Field(..., description='The review record UUID information came from for this record')
    rating: int = Field(..., description='The rating from the reddit review, expressed as an integer between 0-100')
    user: str = Field(..., description='The username for the person who posted the review')

