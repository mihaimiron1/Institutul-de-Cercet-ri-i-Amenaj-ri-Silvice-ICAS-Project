from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q
from .models import Species
from .models import Reserve
from .models import Association
from .models import Site
from .models import Habitat
from .models import Occurrence


CARTEA_ROSIE_CHOICES = (
    ("", "— selectează —"),
    ("CR", "CR – Critic în pericol"),
    ("EN", "EN – În pericol"),
    ("VU", "VU – Vulnerabil"),
    ("NT", "NT – Aproape amenințat"),
    ("LC", "LC – Neîngrijorător"),
    ("DD", "DD – Date insuficiente"),
    ("EX", "EX – Dispărut"),
    ("EW", "EW – Dispărut în sălbăticie"),
)


class SpeciesForm(forms.ModelForm):
    denumire_stiintifica = forms.CharField(
        label="Denumire științifică",
        max_length=255,
        help_text="Genul cu majusculă (ex.: Rosa canina)",
        widget=forms.TextInput(attrs={"placeholder": "Ex.: Rosa canina"}),
    )
    denumire_populara = forms.CharField(
        label="Denumire populară",
        max_length=255,
        required=False,
    )
    clasa = forms.CharField(label="Clasa", max_length=120, required=False)
    familia = forms.CharField(label="Familia", max_length=120, required=False)
    habitat = forms.CharField(label="Habitat", max_length=120, required=False)
    localitatea = forms.CharField(label="Localitatea", max_length=255, required=False)

    silvice = forms.BooleanField(label="Silvice", required=False)
    pajisti_sau_stepice = forms.BooleanField(label="Pajiști/stepice", required=False)
    stancarii = forms.BooleanField(label="Stâncării", required=False)
    palustre_si_acvatice = forms.BooleanField(label="Palustre/Acvatice", required=False)

    is_rare = forms.BooleanField(label="Specie rară", required=False)

    conventia_berna = forms.BooleanField(label="Convenția de la Berna", required=False)
    directiva_habitate = forms.BooleanField(label="Directiva Habitate", required=False)

    cartea_rosie = forms.IntegerField(
        label="Cartea Roșie – An",
        required=False,
        min_value=1800,
        max_value=2100,
        help_text="Anul ediției (ex.: 2015)",
        widget=forms.NumberInput(attrs={
            "placeholder": "ex. 2015",
            "pattern": "\\d{4}",
            "inputmode": "numeric",
        }),
    )
    cartea_rosie_cat = forms.ChoiceField(
        label="Cartea Roșie – Categoria",
        required=False,
        choices=CARTEA_ROSIE_CHOICES,
    )

    frecventa = forms.CharField(label="Frecvența", max_length=50, required=False)
    notes = forms.CharField(label="Note", required=False, widget=forms.Textarea(attrs={"rows": 3}))

    class Meta:
        model = Species
        fields = [
            "denumire_stiintifica",
            "denumire_populara",
            "clasa",
            "familia",
            "habitat",
            "localitatea",
            "silvice",
            "pajisti_sau_stepice",
            "stancarii",
            "palustre_si_acvatice",
            "is_rare",
            "conventia_berna",
            "directiva_habitate",
            "cartea_rosie",
            "cartea_rosie_cat",
            "frecventa",
            "notes",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Associate helper text for accessibility
        self.fields["denumire_stiintifica"].widget.attrs.update({
            "aria-describedby": "help_sci"
        })
        # Consistent placeholders
        self.fields["frecventa"].widget.attrs.setdefault("placeholder", "Ex.: Rară / Comună / etc.")
        # Ensure selects/inputs have no unexpected sizes
        self.fields["cartea_rosie_cat"].widget.attrs.setdefault("style", "max-width: 22rem;")

    def clean_denumire_stiintifica(self):
        raw = self.cleaned_data.get("denumire_stiintifica") or ""
        normalized = " ".join(raw.split())
        if normalized:
            parts = normalized.split(" ")
            if parts:
                parts[0] = parts[0][:1].upper() + parts[0][1:].lower()
            normalized = " ".join(parts)
        if not (3 <= len(normalized) <= 200):
            raise ValidationError("Lungimea trebuie să fie între 3 și 200 de caractere.")
        # case-insensitive uniqueness
        exists = Species.objects.filter(denumire_stiintifica__iexact=normalized)
        if self.instance and self.instance.pk:
            exists = exists.exclude(pk=self.instance.pk)
        if exists.exists():
            raise ValidationError("Această denumire științifică există deja.")
        return normalized

    def clean(self):
        cleaned = super().clean()
        cat = cleaned.get("cartea_rosie_cat") or ""
        year = cleaned.get("cartea_rosie")
        # Optional convention from imports: if category provided but year missing, default to 2015
        if cat and not year:
            cleaned["cartea_rosie"] = 2015
        return cleaned


class ReserveForm(forms.ModelForm):
    name = forms.CharField(label="Nume", max_length=255)
    raion = forms.CharField(label="Raion", max_length=255)
    amplasare = forms.CharField(label="Amplasare", required=False, widget=forms.Textarea(attrs={"rows": 2}))
    proprietar = forms.CharField(label="Proprietar", max_length=255, required=False)
    suprafata_ha = forms.DecimalField(label="Suprafață (ha)", required=False, min_value=0, decimal_places=2, max_digits=12)
    category = forms.CharField(label="Categorie", max_length=120, required=False)
    subcategory = forms.CharField(label="Subcategorie", max_length=120, required=False)
    description = forms.CharField(label="Descriere", required=False, widget=forms.Textarea(attrs={"rows": 3}))
    diversitatea_fitocenotica = forms.CharField(label="Diversitatea fitocenotică", required=False, widget=forms.Textarea(attrs={"rows": 3}))
    latitude = forms.DecimalField(label="Latitudine", required=False, max_digits=9, decimal_places=6)
    longitude = forms.DecimalField(label="Longitudine", required=False, max_digits=9, decimal_places=6)
    notes = forms.CharField(label="Notițe", required=False, widget=forms.Textarea(attrs={"rows": 3}))

    class Meta:
        model = Reserve
        fields = [
            "name", "raion", "amplasare", "proprietar", "suprafata_ha",
            "category", "subcategory", "description", "diversitatea_fitocenotica",
            "latitude", "longitude", "notes"
        ]

    def clean_name(self):
        val = (self.cleaned_data.get("name") or "").strip()
        if len(val) < 2:
            raise ValidationError("Numele este prea scurt.")
        # unique by model constraint
        qs = Reserve.objects.filter(name__iexact=val)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Există deja o rezervație cu acest nume.")
        return val

    def clean_raion(self):
        val = (self.cleaned_data.get("raion") or "").strip()
        if not val:
            raise ValidationError("Raionul este obligatoriu.")
        return val

    def clean(self):
        cleaned = super().clean()
        lat = cleaned.get("latitude")
        lon = cleaned.get("longitude")
        if lat is not None and not (-90 <= float(lat) <= 90):
            self.add_error("latitude", "Latitudinea trebuie să fie între -90 și 90.")
        if lon is not None and not (-180 <= float(lon) <= 180):
            self.add_error("longitude", "Longitudinea trebuie să fie între -180 și 180.")
        return cleaned

class HabitatForm(forms.ModelForm):
    name_romanian = forms.CharField(label="Denumire (română)", max_length=255)
    name_english = forms.CharField(label="Denumire (engleză)", max_length=255)
    code = forms.CharField(label="Cod habitat", max_length=64, required=False)
    notes = forms.CharField(label="Notițe", required=False, widget=forms.Textarea(attrs={"rows": 3}))

    class Meta:
        model = Habitat
        fields = ["name_romanian", "name_english", "code", "notes"]

    def clean_name_romanian(self):
        val = (self.cleaned_data.get("name_romanian") or "").strip()
        if len(val) < 2:
            raise ValidationError("Denumirea în română este prea scurtă.")
        qs = Habitat.objects.filter(name_romanian__iexact=val)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Există deja un habitat cu această denumire (RO).")
        return val

    def clean_name_english(self):
        val = (self.cleaned_data.get("name_english") or "").strip()
        if len(val) < 2:
            raise ValidationError("Denumirea în engleză este prea scurtă.")
        qs = Habitat.objects.filter(name_english__iexact=val)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Există deja un habitat cu această denumire (EN).")
        return val

class AssociationForm(forms.ModelForm):
    name = forms.CharField(label="Nume", max_length=255)
    notes = forms.CharField(label="Notițe", required=False, widget=forms.Textarea(attrs={"rows": 3}))

    class Meta:
        model = Association
        fields = ["name", "notes"]

    def clean_name(self):
        val = (self.cleaned_data.get("name") or "").strip()
        if len(val) < 2:
            raise ValidationError("Numele este prea scurt.")
        qs = Association.objects.filter(name__iexact=val)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Există deja o asociație cu acest nume.")
        return val

class SiteForm(forms.ModelForm):
    code = forms.CharField(label="Codul sitului", max_length=32)
    name = forms.CharField(label="Denumirea", max_length=255)
    surface_ha = forms.DecimalField(label="Suprafață (ha)", max_digits=12, decimal_places=2)
    bird_species_count = forms.IntegerField(label="Număr specii păsări", min_value=0)
    other_species_count = forms.IntegerField(label="Alte specii (număr)", min_value=0)
    habitats_count = forms.IntegerField(label="Habitate (număr)", min_value=0, required=False)
    longitude = forms.DecimalField(label="Longitudine", max_digits=9, decimal_places=6, required=False)
    latitude = forms.DecimalField(label="Latitudine", max_digits=9, decimal_places=6, required=False)
    ste = forms.BooleanField(label="STE", required=False)
    conj = forms.BooleanField(label="CONJ", required=False)
    notes = forms.CharField(label="Notițe", required=False, widget=forms.Textarea(attrs={"rows": 3}))
    other_species = forms.CharField(label="Alte specii (text)", required=False, widget=forms.Textarea(attrs={"rows": 3}))

    class Meta:
        model = Site
        fields = [
            "code", "name", "surface_ha", "bird_species_count", "other_species_count",
            "habitats_count", "longitude", "latitude", "ste", "conj", "notes", "other_species"
        ]

    def clean_code(self):
        val = (self.cleaned_data.get("code") or "").strip()
        if not val:
            raise ValidationError("Codul este obligatoriu.")
        qs = Site.objects.filter(code__iexact=val)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Există deja un site cu acest cod.")
        return val

    def clean_name(self):
        val = (self.cleaned_data.get("name") or "").strip()
        if len(val) < 2:
            raise ValidationError("Denumirea este prea scurtă.")
        qs = Site.objects.filter(name__iexact=val)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Există deja un site cu această denumire.")
        return val

    def clean(self):
        cleaned = super().clean()
        lat = cleaned.get("latitude")
        lon = cleaned.get("longitude")
        if lat is not None and not (-90 <= float(lat) <= 90):
            self.add_error("latitude", "Latitudinea trebuie să fie între -90 și 90.")
        if lon is not None and not (-180 <= float(lon) <= 180):
            self.add_error("longitude", "Longitudinea trebuie să fie între -180 și 180.")
        return cleaned

class OccurrenceForm(forms.ModelForm):
    species_name = forms.CharField(label="Specie (căutare)", required=True)
    reserve_name = forms.CharField(label="Rezervație (căutare)", required=True)
    year = forms.IntegerField(label="An", min_value=1800, max_value=2100, widget=forms.NumberInput(attrs={"placeholder": "ex. 2019", "pattern": "\\d{4}", "inputmode": "numeric"}))
    is_rare = forms.BooleanField(label="Specie rară", required=False)
    latitude = forms.DecimalField(label="Latitudine", required=False, max_digits=9, decimal_places=6)
    longitude = forms.DecimalField(label="Longitudine", required=False, max_digits=9, decimal_places=6)
    source = forms.CharField(label="Sursa", max_length=50, required=False)
    observer = forms.CharField(label="Observator", max_length=255, required=False)
    notes = forms.CharField(label="Notițe", required=False, widget=forms.Textarea(attrs={"rows": 3}))

    class Meta:
        model = Occurrence
        fields = ["year", "is_rare", "latitude", "longitude", "source", "observer", "notes"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set placeholders for search fields
        self.fields["species_name"].widget.attrs.update({"placeholder": "Caută specie..."})
        self.fields["reserve_name"].widget.attrs.update({"placeholder": "Caută rezervație..."})

    def clean_species_name(self):
        val = (self.cleaned_data.get("species_name") or "").strip()
        if not val:
            raise ValidationError("Selectează o specie.")
        species = Species.objects.filter(denumire_stiintifica__iexact=val).first()
        if not species:
            raise ValidationError("Specie inexistentă.")
        self.species_obj = species
        return val

    def clean_reserve_name(self):
        val = (self.cleaned_data.get("reserve_name") or "").strip()
        if not val:
            raise ValidationError("Selectează o rezervație.")
        reserve = Reserve.objects.filter(name__iexact=val).first()
        if not reserve:
            raise ValidationError("Rezervație inexistentă.")
        self.reserve_obj = reserve
        return val

    def clean(self):
        cleaned = super().clean()
        # Set foreign keys
        if hasattr(self, 'species_obj') and hasattr(self, 'reserve_obj'):
            self.instance.species = self.species_obj
            self.instance.reserve = self.reserve_obj

        # Check for duplicate occurrence
        if hasattr(self, 'species_obj') and hasattr(self, 'reserve_obj'):
            year = cleaned.get("year")
            if year:
                existing = Occurrence.objects.filter(
                    species=self.species_obj,
                    reserve=self.reserve_obj,
                    year=year
                )
                if self.instance and self.instance.pk:
                    existing = existing.exclude(pk=self.instance.pk)
                if existing.exists():
                    raise ValidationError("Există deja o înregistrare pentru această specie, rezervație și an.")

        # Validate coordinates
        lat = cleaned.get("latitude")
        lon = cleaned.get("longitude")
        if lat is not None and not (-90 <= float(lat) <= 90):
            self.add_error("latitude", "Latitudinea trebuie să fie între -90 și 90.")
        if lon is not None and not (-180 <= float(lon) <= 180):
            self.add_error("longitude", "Longitudinea trebuie să fie între -180 și 180.")

        return cleaned
