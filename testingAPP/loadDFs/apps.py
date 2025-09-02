from django.apps import AppConfig
import os


class LoaddfsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'loadDFs'
    
    def ready(self):
        from django.conf import settings
        os.makedirs(settings.TEMP_DIR, exist_ok=True)
        os.makedirs(settings.IMAGES_DIR, exist_ok=True)