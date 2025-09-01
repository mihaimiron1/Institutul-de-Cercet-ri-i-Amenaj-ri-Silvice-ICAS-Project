# core/urls.py
from . import views
from django.contrib import admin
from django.urls import path, include
from core import views as core_views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('species/', views.species_list, name='species_list'),
    #path('reserves/', views.reserve_list, name='reserve_list'),
    #path('occurrences/', views.occurrence_list, name='occurrence_list'),
    #path('occurrences/add/', views.occurrence_create, name='occurrence_create'),

    path('associations/filters/', views.associations_filters_page, name='associations_filters_page'),
    path('occurrences/filters/', views.occurrences_filters_page, name='occurrences_filters_page'),
    path('accounts/', include('django.contrib.auth.urls')),  # login/logout/password_change
    path("sitehab/filters/", views.sitehab_filters_page, name="sitehab_filters"),
    path("accounts/", include("django.contrib.auth.urls")),

    # auth (ai deja LoginView configurat prin template)
    path("accounts/login/", auth_views.LoginView.as_view(), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),

    # home + pagini
    path("", core_views.home, name="home"),
    path("vizualizari/", core_views.vizualizari_home, name="vizualizari_home"),

    path("filtrari/asociatii/", core_views.associations_filters_page, name="associations_filters"),
    path("filtrari/ocurente/", core_views.occurrences_filters_page, name="occurrences_filters"),
    path("filtrari/site-habitate/", core_views.sitehab_filters_page, name="sitehab_filters"),
    path("comparatii/", views.comparatii_home, name="comparatii_home"),
    

    



]
