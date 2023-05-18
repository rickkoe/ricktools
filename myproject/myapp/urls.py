# myapp/urls.py

from django.urls import path
from myapp import views

app_name = 'myapp'

urlpatterns = [
    path('import/', views.import_csv, name='import'),
]
