from pathlib import Path
from fastapi.templating import Jinja2Templates

# Get the absolute path of the directory containing this file (app/core)
CORE_DIR = Path(__file__).resolve().parent

# Step up to the main 'app' directory root
APP_ROOT = CORE_DIR.parent

# Force explicit absolute paths for Jinja2 search directories
SHARED_TEMPLATES = str(APP_ROOT / "shared_templates")
MODULES_TEMPLATES = str(APP_ROOT / "modules")

# Initialize templates with guaranteed absolute paths
templates = Jinja2Templates(directory=[
    SHARED_TEMPLATES,
    MODULES_TEMPLATES,
])
