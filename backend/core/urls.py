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
        path("accounts/logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),


    # home + pagini
    path("", core_views.home, name="home"),
    

    path("filtrari/asociatii/", core_views.associations_filters_page, name="associations_filters"),
    path("filtrari/ocurente/", core_views.occurrences_filters_page, name="occurrences_filters"),
    path("filtrari/site-habitate/", core_views.sitehab_filters_page, name="sitehab_filters"),
    path("comparatii/", views.comparatii_home, name="comparatii_home"),


    path("vizualizari/", views.vizualizari_home, name="vizualizari_home"),
    path("vizualizari/specii/", views.viz_specii, name="viz_specii"),
    path("vizualizari/specii/<int:pk>/", views.viz_specii_detail, name="viz_specii_detail"),
    path("vizualizari/specii/<int:pk>/update-description/", views.update_species_description, name="update_species_description"),
    path("vizualizari/rezervatii/", views.viz_rezervatii, name="viz_rez"),
    path("vizualizari/rezervatii/<int:pk>/", views.viz_rezervatii_detail, name="viz_rez_detail"),
    path("vizualizari/rezervatii/<int:pk>/update-description/", views.update_reserve_description, name="update_reserve_description"),
    path("vizualizari/asociatii/", views.viz_asociatii, name="viz_asoc"),
    path("vizualizari/situri/", views.viz_situri, name="viz_situri"),
    path("vizualizari/habitate/", views.viz_habitate, name="viz_habitate"),




]
