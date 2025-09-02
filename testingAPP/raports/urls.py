from django.urls import path
from .views import standard_raport

urlpatterns = [
    path('std_report/', standard_raport, name='standard'),
]

