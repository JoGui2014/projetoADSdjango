from django.urls import path
from . import views

app_name = 'calendario'

urlpatterns = [
    path('', views.home, name='home'),
    path('convertView/', views.convertView, name='convertView'),
]