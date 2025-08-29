from django.contrib import admin
from django.urls import path                      # ← needed
from django.http import JsonResponse              # ← for the tiny JSON endpoint
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

@admin.register(Site)
class SiteAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "surface_ha", "bird_species_count", "habitats_count", "ste", "conj")
    search_fields = ("name", "code")
    list_filter = ("ste", "conj")

@admin.register(SiteHabitat)
class SiteHabitatAdmin(admin.ModelAdmin):
    list_display = ("site", "habitat", "year", "surface")
    list_filter = ("year",)
    search_fields = ("site__name", "habitat__name_romanian", "habitat__name_english")