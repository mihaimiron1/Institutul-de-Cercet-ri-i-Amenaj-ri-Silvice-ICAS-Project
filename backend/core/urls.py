# core/urls.py
from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('species/', views.species_list, name='species_list'),
    #path('reserves/', views.reserve_list, name='reserve_list'),
    #path('occurrences/', views.occurrence_list, name='occurrence_list'),
    #path('occurrences/add/', views.occurrence_create, name='occurrence_create'),
    path('associations/filters/', views.associations_filters_page, name='associations_filters_page'),
    path('occurrences/filters/', views.occurrences_filters_page, name='occurrences_filters_page'),
    path('accounts/', include('django.contrib.auth.urls')),  # login/logout/password_change
    path("sitehab/filters/", views.sitehab_filters_page, name="sitehab_filters"),

    



]
