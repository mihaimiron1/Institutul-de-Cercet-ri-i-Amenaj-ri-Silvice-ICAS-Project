from django.db import models
from django.core.validators import MinValueValidator


class Reserve(models.Model):
    name = models.CharField(max_length=255, unique=True)
    raion = models.CharField(max_length=255, blank=True, null=True)
    amplasare = models.TextField(blank=True, null=True)
    proprietar = models.CharField(max_length=255, blank=True, null=True)
    suprafata_ha = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    category = models.CharField(max_length=120, blank=True, null=True)
    subcategory = models.CharField(max_length=120, blank=True, null=True)

    # Descriere editabilă de către administratori
    description = models.TextField(blank=True, null=True)

    # ✅ câmpurile care lipsesc
    diversitatea_fitocenotica = models.TextField(blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    coords_raw = models.TextField(blank=True, null=True)

    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


    class Meta:
        indexes = [models.Index(fields=["raion"])]

    def __str__(self):
        return self.name


class Species(models.Model):
    denumire_stiintifica = models.CharField(max_length=255, unique=True)
    denumire_populara = models.CharField(max_length=255, blank=True, null=True)
    clasa = models.CharField(max_length=120, blank=True, null=True)
    familia = models.CharField(max_length=120, blank=True, null=True)
    habitat = models.CharField(max_length=120, blank=True, null=True)
    localitatea = models.CharField(max_length=255, blank=True, null=True)

    # Descriere editabilă de către administratori
    description = models.TextField(blank=True, null=True)

    silvice = models.BooleanField(default=False)
    pajisti_sau_stepice = models.BooleanField(default=False) 
    stancarii = models.BooleanField(default=False)
    palustre_si_acvatice = models.BooleanField(default=False)

    is_rare = models.BooleanField(default=False, db_index=True)



    conventia_berna = models.BooleanField(default=False)
    directiva_habitate = models.BooleanField(default=False)
    cartea_rosie = models.PositiveSmallIntegerField(
        blank=True, null=True,
        help_text="Anul ediției Cărții Roșii (ex.: 2015)"
    )
    cartea_rosie_cat = models.CharField(
        max_length=10, blank=True, null=True,
        help_text="Categoria din Cartea Roșie (ex.: VU, EN, CR)"
    )

    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Frecvența (va putea fi folosită ca filtru în rapoarte)
    frecventa = models.CharField(
        max_length=50, blank=True, null=True,
        help_text="Frecvența (ex.: C, Rară, etc.)"
    )

    # @property
    # def is_rare_(self) -> bool:
    #     return bool(self.cartea_rosie_year or self.cartea_rosie_cat or self.is_rare)


    class Meta:
        indexes = [
            models.Index(fields=["familia"]),
            models.Index(fields=["is_rare"]),
            models.Index(fields=["cartea_rosie_cat"]),  # filtrare rapidă pe categorie
            models.Index(fields=["frecventa"]),          # filtrare pe frecvență
        ]

    def __str__(self):
        return self.denumire_stiintifica


class Association(models.Model):
    name = models.CharField(max_length=255, unique=True)
    notes = models.TextField(blank=True, null=True)
    def __str__(self): return self.name


class Occurrence(models.Model):
    species = models.ForeignKey(Species, on_delete=models.CASCADE, related_name="occurrences")
    reserve = models.ForeignKey(Reserve, on_delete=models.CASCADE, related_name="occurrences")
    year = models.PositiveSmallIntegerField()

    # raritatea la momentul observației, booleană
    is_rare = models.BooleanField(default=False)

    # coordonate (de obicei doar la specii rare; rămân opționale)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)

    # metadate utile
    source = models.CharField(max_length=50, blank=True, null=True)  # ex.: 'teren' | 'literatura' | 'raport'
    observer = models.CharField(max_length=255, blank=True, null=True)
    created_by = models.ForeignKey('auth.User', on_delete=models.SET_NULL, blank=True, null=True)

    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = (("species", "reserve", "year"),)
        indexes = [
            models.Index(fields=["reserve", "year"]),
            models.Index(fields=["species"]),
            models.Index(fields=["year"]),
            models.Index(fields=["is_rare"]),  # filtre rapide „doar rare”
        ]

    def __str__(self):
        return f"{self.species} @ {self.reserve} ({self.year})"



class ReserveAssociationYear(models.Model):
    association = models.ForeignKey(Association, on_delete=models.CASCADE, related_name="reserve_links")
    reserve = models.ForeignKey(Reserve, on_delete=models.CASCADE, related_name="association_links")
    year = models.PositiveSmallIntegerField()
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = (("association", "reserve", "year"),)
        indexes = [
            models.Index(fields=["reserve"]),
            models.Index(fields=["association"]),
            models.Index(fields=["year"]),
        ]

    def __str__(self):
        return f"{self.association} @ {self.reserve} ({self.year})"



class Habitat(models.Model):
    name_english  = models.CharField(max_length=255, unique=True, db_index=True)
    name_romanian = models.CharField(max_length=255, unique=True, db_index=True)
    code          = models.CharField(max_length=64, blank=True, null=True, db_index=True)
    notes         = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "core_habitat"

    def __str__(self):
        return self.name_romanian or self.name_english


class Site(models.Model):
    # din CSV: codul_sitului, denumirea, suprafata, numar_specii_pasari,
    #          alte_specii, habitate, latitudine, longitudine, STE, CONJ
    code                 = models.CharField("codul_sitului", max_length=32, unique=True, db_index=True)
    name                 = models.CharField("denumirea", max_length=255, unique=True, db_index=True)
    surface_ha           = models.DecimalField("suprafata (ha)", max_digits=12, decimal_places=2)
    bird_species_count   = models.IntegerField("numar_specii_pasari")
    other_species_count  = models.IntegerField("alte_specii")
    habitats_count       = models.IntegerField("habitate",blank=True, null=True,default=0,)

    longitude            = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    latitude             = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)

    ste                  = models.BooleanField("STE")   
    conj                 = models.BooleanField("CONJ")

    notes                = models.TextField(blank=True, null=True)

    # New editable metadata
    other_species        = models.TextField(blank=True, default="")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "core_site"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["code"]),
        ]

    def __str__(self):
        return self.name


class SiteHabitat(models.Model):
    site    = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="site_habitats")
    habitat = models.ForeignKey(Habitat, on_delete=models.CASCADE, related_name="site_habitats")
    year    = models.PositiveSmallIntegerField()
    surface = models.DecimalField(max_digits=12, decimal_places=2,blank=True, null=True,validators=[MinValueValidator(0)])
    notes   = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["site", "habitat", "year"], name="uniq_site_habitat_year")
        ]
        indexes = [
            models.Index(fields=["year"]),
            models.Index(fields=["site", "year"]),
            models.Index(fields=["habitat", "year"]),
        ]

    def __str__(self):
        return f"{self.site} – {self.habitat} ({self.year})"