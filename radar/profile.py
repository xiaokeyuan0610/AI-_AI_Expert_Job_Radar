"""Load minimal matching facts without putting private profiles in source control."""
import json
import os
from pathlib import Path

FIELDS = {"interests", "confirmed_qualifications", "unknown", "instruction", "education",
          "experience", "skills", "boundaries", "priorities"}


def load_profile(directory=Path("config")):
    secret = os.environ.get("USER_PROFILE_JSON", "").strip()
    private = directory / "profile.private.json"
    if secret:
        profile = json.loads(secret)
    else:
        source = private if private.exists() else directory / "profile.json"
        profile = json.loads(source.read_text(encoding="utf-8"))
    if not isinstance(profile, dict):
        raise ValueError("Matching profile must be an object")
    # Unrecognized fields (name, contact details, raw resume, etc.) are excluded.
    return {key: value for key, value in profile.items() if key in FIELDS}
