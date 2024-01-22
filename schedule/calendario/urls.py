from django.urls import path
from . import views
from .views import calculator
from .views import calcular_expressao

app_name = 'calendario'

urlpatterns = [
    path('', views.home, name='home'),
    path('convertView/', views.convertView, name='convertView'),
    path('download_csv/<str:file_name>/', views.download_csv, name='download_csv'),
    path('download_json/<str:file_name>/', views.download_json, name='download_json'),
    path('informations/', views.get_informations, name='get_informations'),
    path('class_rooms/', views.class_rooms, name='class_rooms'),
    path('observeCalendar/', views.observeCalendar, name='observeCalendar'),
    path('get_events/', views.get_events, name='get_events'),
    path('calculator/', calculator, name='calculator'),
    path('calcular-expressao/', calcular_expressao, name='calcular_expressao'),
    path('heatmap/', views.heatmap_view, name='heatmap'),
    path('cordas/', views.cordas_view, name='cordas'),
]