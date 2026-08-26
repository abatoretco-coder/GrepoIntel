from datetime import UTC, datetime
import pytest
from pydantic import ValidationError
from app.schemas.personal_state import PersonalStateImport

def snapshot(city: dict):
    return {"schema":"grepointel-personal-state","version":1,"world":"FR183","player":"Abator","captured_at":datetime.now(UTC),"cities":[city]}

def test_personal_snapshot_requires_city_identity():
    with pytest.raises(ValidationError):
        PersonalStateImport.model_validate(snapshot({"resources":{"wood":10}}))

def test_personal_snapshot_accepts_optional_unknown_fields():
    payload=PersonalStateImport.model_validate(snapshot({"external_city_id":"42","resources":{"wood":None},"units":{"home":{"bireme":180}}}))
    assert payload.cities[0].resources["wood"] is None
    assert payload.cities[0].units["home"]["bireme"] == 180
