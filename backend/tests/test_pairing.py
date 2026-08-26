from app.services.pairing import _digest

def test_pairing_digest_is_deterministic_and_never_returns_raw_token():
    token="local-pairing-only"
    assert _digest(token)==_digest(token)
    assert token not in _digest(token)
