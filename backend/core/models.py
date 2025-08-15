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

    p_rara = models.BooleanField(default=False)  # 'conventia_berna'|'directiva_habitate'|'critica'
    conventia_berna = models.BooleanField(default=False)
    directiva_habitate = models.BooleanField(default=False)
    cartea_rosie = models.PositiveSmallIntegerField(
    blank=True, null=True,
    help_text="Anul ediției Cărții Roșii în care planta este inclusă (ex: 2015)"
)

    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [models.Index(fields=["familia"]), models.Index(fields=["p_rara"])]

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
    rarity_at_observation = models.CharField(max_length=20)  # 'comuna'|'rara'|'critica'

    # coordonate doar la specii rare (MVP fără PostGIS)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)

    observer = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        unique_together = (("species", "reserve", "year"),)
        indexes = [
            models.Index(fields=["reserve", "year"]),
            models.Index(fields=["species"]),
            models.Index(fields=["year"]),
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
