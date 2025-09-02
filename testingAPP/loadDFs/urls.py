from django.urls import path
from .views import load, edit, clear_temp

urlpatterns = [
    path('loadDF/', load, name='load'),
    path('edit/', edit, name='edit'),
    path('clear/', clear_temp, name='clear'),
]