from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class WhiskeyType(str, Enum):
    Rye = "Rye"
    Bourbon = "Bourbon"
    Scotch = "Scotch"
    Irish = "Irish"
    Japanese = "Japanese"
    Other = "Other"

class DistilleryRegion(str, Enum):
    # Scotland
    HIGHLANDS = "Highlands"
    LOWLANDS = "Lowlands"
    SPEYSIDE = "Speyside"
    ISLAY = "Islay"
    CAMPBELTOWN = "Campbeltown"
    # USA
    KENTUCKY = "Kentucky"  # Primary Bourbon region
    TENNESSEE = "Tennessee"  # Tennessee Whiskey (e.g., Jack Daniel's)
    OTHER_USA = "Other USA"  # Catch-all for craft distilleries in other states
    IRELAND = "Ireland"
    JAPAN = "Japan"
    CANADA = "Canada"
    INDIA = "India"
    AUSTRALIA = "Australia"
    WALES = "Wales"
    OTHER = "Other"

class DistilleryCountry(str, Enum):
    # Scotland (Scotch Whisky Regions)
    SCOTLAND = 'Scotland'
    UNITED_STATES = 'United States'
    IRELAND = "Ireland"
    JAPAN = "Japan"
    CANADA = "Canada"
    INDIA = "India"
    AUSTRALIA = "Australia"
    WALES = "Wales"
    OTHER = "Other"


class Whiskey(BaseModel):
    year: Optional[int] = Field(None, description="The year the whiskey was bottled (if provided)")
    whiskey_name: str = Field(..., description="The name of the whiskey without distiller or age")
    age: Optional[int] = Field(None, description="The age of the whiskey, amount of time it was in a cask (in years)")
    distillery: str = Field(..., description="The distillery or bottler who produced the whiskey")
    whiskey_country_of_origin: DistilleryCountry = Field(None, description='The country the distillery is based in')
    distillery_region: DistilleryRegion = Field(None, description='The region the whiskey came from')
    is_blend: bool = Field(None, description="Boolean (True/False) for whether the whiskey is a blended or single malt")
    whiskey_type: WhiskeyType = Field(None, description="The type of whiskey")
    nose_tags: list[str] = Field(..., description='Keywords describing the nose/smell of the whiskey from the provided review')
    palette_tags: list[str] = Field(..., description='Keywords describing the nose/smell of the whiskey from the provided review')
    finish_tags: list[str] = Field(..., description="Keywords describing the finish of the whiskey")


class WhiskeyReview(Whiskey):
    uuid: str = Field(..., description='The review record UUID information came from for this record')
    rating: int = Field(..., description='The rating from the reddit review, expressed as an integer between 0-100')
    user: str = Field(..., description='The username for the person who posted the review')

