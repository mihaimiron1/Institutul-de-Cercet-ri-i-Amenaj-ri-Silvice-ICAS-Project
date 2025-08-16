from django.db import models

from django.db import models

class Reserve(models.Model):
    name = models.CharField(max_length=255, unique=True)
    raion = models.CharField(max_length=255, blank=True, null=True)
    amplasare = models.TextField(blank=True, null=True)
    proprietar = models.CharField(max_length=255, blank=True, null=True)
    suprafata_ha = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    category = models.CharField(max_length=120, blank=True, null=True)
    subcategory = models.CharField(max_length=120, blank=True, null=True)

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

    silvice = models.BooleanField(default=False)
    pajisti_sau_stepice = models.BooleanField(default=False) 
    stancarii = models.BooleanField(default=False)
    palustre_si_acvatice = models.BooleanField(default=False)

    p_rara = models.CharField(max_length=20, blank=True, null=True)  # permite NULL
     # 'conventia_berna'|'directiva_habitate'|'critica'
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

    class Meta:
        indexes = [
            models.Index(fields=["familia"]),
            models.Index(fields=["p_rara"]),
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
    rarity = models.BooleanField(default=False)

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
            models.Index(fields=["rarity"]),  # filtre rapide „doar rare”
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
