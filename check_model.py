import sys
import json
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path("backend").resolve()))

from onroad.api import model

m = model("mahindra", "scorpio-n", "Hyderabad")
print("NAME:", m.get("name"))
print("IMAGE_URL:", m.get("image_url"))
print("GALLERY:", m.get("gallery"))
print("VARIANTS COUNT:", len(m.get("variants", [])))
print("FIRST VARIANT:", m.get("variants", [])[0] if m.get("variants") else None)
