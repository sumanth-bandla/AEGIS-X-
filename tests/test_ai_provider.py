import os
from services.ai_provider import AIProvider


def test_unconfigured():
    # ensure no key
    os.environ.pop("NEBIUS_API_KEY", None)
    os.environ.pop("OPENAI_API_KEY", None)
    p = AIProvider()
    assert not p.is_configured()
    r = p.chat("sys", "user")
    assert not r.ok