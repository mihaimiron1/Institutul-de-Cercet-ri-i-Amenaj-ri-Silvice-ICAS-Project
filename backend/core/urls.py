# core/urls.py
from . import views
from django.contrib import admin
from django.urls import path, include
from core import views as core_views
from django.contrib.auth import views as auth_views

urlpatterns = [
    



    path('species/', views.species_list, name='species_list'),
    # Public additions hub
    path('adaugari/', views.adaugari_home, name='adaugari_home'),
    path('adaugari/plante/', views.add_plante, name='add_plante'),
    path('adaugari/rezervatii/', views.add_reserve_page, name='add_reserve'),
    path('adaugari/asociatii/', views.add_asociatii, name='add_asociatii'),
    path('adaugari/asociatii/forma/', views.add_association_page, name='add_association'),
    path('adaugari/situri/', views.add_situri, name='add_situri'),
    path('adaugari/situri/forma/', views.add_site_page, name='add_site'),
    path('adds/sites/', views.add_site_page, name='adds_sites'),
    path('adaugari/habitate/', views.add_habitate, name='add_habitate'),
    path('adaugari/habitate/forma/', views.add_habitat_page, name='add_habitat'),
    path('adds/habitats/', views.add_habitat_page, name='adds_habitats'),
    path('adaugari/plante-rezervatii/', views.add_occurrence_page, name='add_occurrence'),
    path('adds/plante-rezervatii/', views.add_occurrence_page, name='adds_plante_rezervatii'),
    path('adaugari/rezervatii-asociatii/', views.add_rezervatii_asociatii, name='add_rezervatii_asociatii'),
    path('adaugari/situri-habitate/', views.add_situri_habitate, name='add_situri_habitate'),
    #path('reserves/', views.reserve_list, name='reserve_list'),
    #path('occurrences/', views.occurrence_list, name='occurrence_list'),
    #path('occurrences/add/', views.occurrence_create, name='occurrence_create'),

    path('occurrences/filters/', views.occurrences_filters_page, name='occurrences_filters_page'),
    path('accounts/', include('django.contrib.auth.urls')),  # login/logout/password_change
    path("sitehab/filters/", views.sitehab_filters_page, name="sitehab_filters"),
    path("accounts/", include("django.contrib.auth.urls")),

    # auth (ai deja LoginView configurat prin template)
    path("accounts/login/", auth_views.LoginView.as_view(), name="login"),
        path("accounts/logout/", auth_views.LogoutView.as_view(next_page="login"), name="logout"),


    # home + pagini
    path("", core_views.home, name="home"),
    path("filtrari/", core_views.filtrari, name="filtrari"),
    

    path("filtrari/ocurente/", core_views.occurrences_filters_page, name="occurrences_filters"),
    path("filtrari/site-habitate/", core_views.sitehab_filters_page, name="sitehab_filters"),

    # New Filtrari specific wrappers
    path("filtrari/plante-rezervatii/", core_views.filters_plante_rezervatii, name="filters_plante_rezervatii"),
    path("filtrari/plante-rezervatii/export/", core_views.export_plante_rezervatii, name="export_plante_rezervatii"),
    path("filtrari/situri-habitat/", core_views.filters_situri_habitat, name="filters_situri_habitat"),

    # Associations filters (new)
    path("filters/associations/", core_views.filters_asociatii, name="filters_asociatii"),
    path("filters/associations/export/", core_views.export_asociatii, name="export_asociatii"),
    path("comparatii/", views.comparatii_home, name="comparatii_home"),


    path("vizualizari/", views.vizualizari_home, name="vizualizari_home"),
    path("vizualizari/specii/", views.viz_specii, name="viz_specii"),
    path("vizualizari/specii/<int:pk>/", views.viz_specii_detail, name="viz_specii_detail"),
    path("vizualizari/specii/<int:pk>/update-description/", views.update_species_description, name="update_species_description"),
    path("vizualizari/specii/<int:pk>/update-meta/", views.update_species_meta, name="update_species_meta"),
    path("vizualizari/rezervatii/", views.viz_rezervatii, name="viz_rez"),
    path("vizualizari/rezervatii/<int:pk>/", views.viz_rezervatii_detail, name="viz_rez_detail"),
    path("vizualizari/rezervatii/<int:pk>/update-description/", views.update_reserve_description, name="update_reserve_description"),
    path("vizualizari/rezervatii/<int:pk>/update-meta/", views.update_reserve_meta, name="update_reserve_meta"),
    path("vizualizari/asociatii/", views.viz_asociatii, name="viz_asoc"),
    path("vizualizari/asociatii/<int:pk>/", views.viz_asociatii_detail, name="viz_asoc_detail"),
    path("vizualizari/asociatii/<int:pk>/update-meta/", views.update_association_meta, name="update_association_meta"),
    path("vizualizari/situri/", views.viz_situri, name="viz_situri"),
    path("vizualizari/situri/<int:pk>/", views.viz_situri_detail, name="viz_sit_detail"),
    path("vizualizari/situri/<int:pk>/update-meta/", views.update_site_meta, name="update_site_meta"),
    path("vizualizari/habitate/", views.viz_habitate, name="viz_habitate"),
    path("vizualizari/habitate/<int:pk>/", views.viz_habitate_detail, name="viz_habitate_detail"),
    path("vizualizari/habitate/<int:pk>/update-meta/", views.update_habitat_meta, name="update_habitat_meta"),

    # Comparatii – plante
    path("comparatii/plante/", views.comparatii_plante_list, name="comparatii_plante_list"),
    path("comparatii/plante/<int:pk>/", views.comparatii_plante_detail, name="comparatii_plante_detail"),
    path("comparatii/plante/data/", views.comparatii_plante_data, name="comparatii_plante_data"),
    path("comparatii/plante/export/", views.comparatii_plante_export, name="comparatii_plante_export"),
    path("comparatii/plante/years/", views.comparatii_plante_years, name="comparatii_plante_years"),




]
