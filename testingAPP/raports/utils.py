import os
from django.conf import settings


# Is it even needed?
def get_files():
    files = list(set(os.path.splitext(f)[0] for f in os.listdir(settings.TEMP_DIR)))
    return files