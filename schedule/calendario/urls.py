from django.urls import path
from . import views

app_name = 'calendario'

urlpatterns = [
    path('', views.home, name='home'),
    path('convertView/', views.convertView, name='convertView'),
    path('download_csv/<str:file_name>/', views.download_csv, name='download_csv'),
    path('download_json/<str:file_name>/', views.download_json, name='download_json'),
]