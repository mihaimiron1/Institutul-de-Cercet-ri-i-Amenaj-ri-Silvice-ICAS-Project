from django.contrib import admin
from django.urls import path                      # ← needed
from django.http import JsonResponse              # ← for the tiny JSON endpoint
from django.db.models import Q, F, Value
from django.db.models.functions import Lower
from django.contrib.postgres.search import TrigramSimilarity
from .models import Species, Reserve, Association, Occurrence, ReserveAssociationYear, Habitat, Site, SiteHabitat


@admin.register(Species)
class SpeciesAdmin(admin.ModelAdmin):
    search_fields = ["denumire_stiintifica", "denumire_populara"]
    ordering = ["denumire_stiintifica"]
    list_display = ["denumire_stiintifica", "familia", "is_rare"]
    list_filter = ["is_rare", "familia"]



@admin.register(Reserve)
class ReserveAdmin(admin.ModelAdmin):
    search_fields = ["name", "raion", "amplasare"]
    ordering = ["name"]


@admin.register(Association)
class AssociationAdmin(admin.ModelAdmin):
    search_fields = ["name"]
    ordering = ["name"]


@admin.register(Occurrence)
class OccurrenceAdmin(admin.ModelAdmin):
    autocomplete_fields = ["species", "reserve"]
    list_display = ["species", "reserve", "year", "is_rare"]
    list_filter = ["year", "is_rare"]

    def save_model(self, request, obj, form, change):
        # Dacă userul NU a atins câmpul is_rare, îl preluăm din specie
            if "is_rare" not in form.changed_data and obj.species_id:
                try:
                    obj.is_rare = bool(obj.species.is_rare)
                except Exception:
                    pass
            super().save_model(request, obj, form, change)

    def get_urls(self):
        urls = super().get_urls()

        def species_rare_status(request):
            species_id = request.GET.get("species")
            is_rare = False
            if species_id:
                try:
                    sp = Species.objects.only("is_rare").get(pk=species_id)
                    is_rare = bool(sp.is_rare)
                except Species.DoesNotExist:
                    pass
            return JsonResponse({"is_rare": is_rare})

        custom = [
            path(
                "species-rare-status/",
                self.admin_site.admin_view(species_rare_status),
                name="core_occurrence_species_rare_status",
            ),
        ]
        return custom + urls

    class Media:
        # fișierul JS pe care îl adăugăm la pasul 2
        js = ("core/js/occurrence_autofill.js",)
        


@admin.register(ReserveAssociationYear)
class ReserveAssociationYearAdmin(admin.ModelAdmin):
    autocomplete_fields = ["association", "reserve"]
    list_display = ["association", "reserve", "year"]
    list_filter = ["year"]


@admin.register(Habitat)
class HabitatAdmin(admin.ModelAdmin):
    list_display = ("name_romanian", "name_english", "code")
    search_fields = ("name_romanian", "name_english", "code")
    
    def get_search_results(self, request, queryset, search_term):
        if not search_term:
            return queryset, False
            
        # Normalize search term: lowercase and unaccent
        normalized_term = search_term.lower().strip()
        
        # Use raw SQL for unaccent + trigram similarity
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, 
                       GREATEST(
                           similarity(unaccent(lower(name_romanian)), %s),
                           similarity(unaccent(lower(name_english)), %s),
                           similarity(unaccent(lower(code)), %s)
                       ) as sim_score
                FROM core_habitat 
                WHERE unaccent(lower(name_romanian)) ILIKE %s 
                   OR unaccent(lower(name_english)) ILIKE %s
                   OR unaccent(lower(code)) ILIKE %s
                   OR similarity(unaccent(lower(name_romanian)), %s) > 0.25
                   OR similarity(unaccent(lower(name_english)), %s) > 0.25
                   OR similarity(unaccent(lower(code)), %s) > 0.25
                ORDER BY sim_score DESC, name_romanian
                LIMIT 20
            """, [
                normalized_term, normalized_term, normalized_term,  # similarity params
                f'%{normalized_term}%', f'%{normalized_term}%', f'%{normalized_term}%',  # ILIKE params
                normalized_term, normalized_term, normalized_term  # similarity threshold params
            ])
            
            habitat_ids = [row[0] for row in cursor.fetchall()]
        
        # Return filtered queryset
        return queryset.filter(id__in=habitat_ids), False

@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "surface_ha", "bird_species_count", "habitats_count", "ste", "conj")
    search_fields = ("name", "code")
    list_filter = ("ste", "conj")
    
    def get_search_results(self, request, queryset, search_term):
        if not search_term:
            return queryset, False
            
        # Normalize search term: lowercase and unaccent
        normalized_term = search_term.lower().strip()
        
        # Use raw SQL for unaccent + trigram similarity
        from django.db import connection
        
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, 
                       GREATEST(
                           similarity(unaccent(lower(name)), %s),
                           similarity(unaccent(lower(code)), %s)
                       ) as sim_score
                FROM core_site 
                WHERE unaccent(lower(name)) ILIKE %s 
                   OR unaccent(lower(code)) ILIKE %s
                   OR similarity(unaccent(lower(name)), %s) > 0.25
                   OR similarity(unaccent(lower(code)), %s) > 0.25
                ORDER BY sim_score DESC, name
                LIMIT 20
            """, [
                normalized_term, normalized_term,  # similarity params
                f'%{normalized_term}%', f'%{normalized_term}%',  # ILIKE params
                normalized_term, normalized_term  # similarity threshold params
            ])
            
            site_ids = [row[0] for row in cursor.fetchall()]
        
        # Return filtered queryset
        return queryset.filter(id__in=site_ids), False

@admin.register(SiteHabitat)
class SiteHabitatAdmin(admin.ModelAdmin):
    autocomplete_fields = ['site', 'habitat']
    list_display = ("site", "habitat", "year", "surface")
    list_filter = ("year",)
    list_select_related = ('site', 'habitat')
    search_fields = ("site__name", "habitat__name_romanian", "habitat__name_english")