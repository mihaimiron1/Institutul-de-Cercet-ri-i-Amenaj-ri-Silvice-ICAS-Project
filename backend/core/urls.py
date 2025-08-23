# core/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('species/', views.species_list, name='species_list'),
    #path('reserves/', views.reserve_list, name='reserve_list'),
    #path('occurrences/', views.occurrence_list, name='occurrence_list'),
    #path('occurrences/add/', views.occurrence_create, name='occurrence_create'),
    path('associations/filters/', views.associations_filters_page, name='associations_filters_page'),

]
