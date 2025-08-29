import csv
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from core.models import Site

def clean(s):
    if s is None:
        return ""
    return str(s).strip()

def to_int(s, default=0):
    s = clean(s)
    if s == "":
        return default
    try:
        return int(s)
    except ValueError:
        # încearcă să elimini spații interne
        try:
            return int(s.replace(" ", ""))
        except Exception:
            return default

def to_float(s, default=0.0):
    s = clean(s)
    if s == "":
        return default
    # dacă CSV-ul are virgule ca separator zecimal
    s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return default

def to_bool(s, default=False):
    s = clean(s).lower()
    if s in {"true", "t", "1", "da", "yes", "y"}:
        return True
    if s in {"false", "f", "0", "nu", "no", "n"}:
        return False
    return default

class Command(BaseCommand):
    help = "Importă situri din data/situri_modificat.csv (vezi coloanele din CSV)."

    def add_arguments(self, parser):
        parser.add_argument("--file", default="data/situri_modificat.csv")

    def handle(self, *args, **opts):
        path = Path(opts["file"])
        if not path.exists():
            raise CommandError(f"Fișierul nu a fost găsit: {path}")

        required = {
            "codul_sitului",
            "denumirea",
            "suprafata",
            "numar_specii_pasari",
            "alte_specii",
            "habitate",
            "latitudine",
            "longitudine",
            "STE",
            "CONJ",
        }

        created = updated = skipped = 0

        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            headers = set(reader.fieldnames or [])
            missing = required - headers
            if missing:
                raise CommandError(
                    "Lipsesc coloane din CSV: " + ", ".join(sorted(missing))
                )

            for i, row in enumerate(reader, start=2):  # start=2 (linia 1 are header)
                try:
                    code   = clean(row.get("codul_sitului"))
                    name   = clean(row.get("denumirea"))

                    # conversii robuste
                    surface_ha          = to_float(row.get("suprafata"), default=0.0)
                    bird_species_count  = to_int(row.get("numar_specii_pasari"), default=0)
                    other_species_count = to_int(row.get("alte_specii"), default=0)
                    habitats_count      = to_int(row.get("habitate"), default=0)

                    latitude  = clean(row.get("latitudine"))
                    longitude = clean(row.get("longitudine"))
                    lat = None if latitude == "" else to_float(latitude, default=None)
                    lon = None if longitude == "" else to_float(longitude, default=None)

                    ste  = to_bool(row.get("STE"), default=False)
                    conj = to_bool(row.get("CONJ"), default=False)

                    if not code or not name:
                        skipped += 1
                        continue

                    obj, is_created = Site.objects.update_or_create(
                        code=code,
                        defaults={
                            "name": name,
                            "surface_ha": surface_ha,
                            "bird_species_count": bird_species_count,
                            "other_species_count": other_species_count,
                            "habitats_count": habitats_count,  # ← acum nu mai e None
                            "latitude": lat,
                            "longitude": lon,
                            "ste": ste,
                            "conj": conj,
                        },
                    )
                    if is_created:
                        created += 1
                    else:
                        updated += 1

                except Exception as e:
                    skipped += 1
                    self.stderr.write(
                        f"[Linia {i}] Eroare la procesare: {e}"
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"Site-uri: create={created}, actualizate={updated}, sărite={skipped}"
            )
        )
