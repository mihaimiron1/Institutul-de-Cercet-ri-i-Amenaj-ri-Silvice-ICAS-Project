import csv
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from core.models import Species

# ---- helpers ---------------------------------------------------------------

CAT_SET = {"EN","VU","CR","NT","LC","DD","EX","EW"}  # poți extinde

def as_str(val):
    if val is None:
        return None
    s = str(val).strip()
    return s or None

def as_bool_plus(val):
    """Interpretează '+' ca True, gol ca False; acceptă și da/true/1."""
    if val is None:
        return False
    s = str(val).strip().lower()
    if s == '+':
        return True
    return s in {'1','true','da','yes','y','t','x','✓'}

def parse_year(val):
    """Întoarce anul (int) dacă val conține doar cifre de 4 caractere; altfel None."""
    s = as_str(val)
    if not s:
        return None
    s_digits = ''.join(ch for ch in s if ch.isdigit())
    if len(s_digits) == 4:
        try:
            y = int(s_digits)
            # un mic sanity check:
            if 1800 <= y <= 2100:
                return y
        except ValueError:
            return None
    return None

def parse_cat(val):
    """Normalizează categoria (EN/VU/CR …) dacă e una validă."""
    s = as_str(val)
    if not s:
        return None
    s = s.upper().replace('.', '').replace(' ', '')
    return s if s in CAT_SET else None

# ---- command ---------------------------------------------------------------

class Command(BaseCommand):
    help = "Importă specii din CSV (capete așteptate: Denumirea_stiintifică, ..., Cartea_R, Frcevența/Frecevnta)."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Calea către data\\plante_combinate.csv")

    @transaction.atomic
    def handle(self, *args, **opts):
        path = opts["csv_path"]

        try:
            f = open(path, encoding="utf-8-sig", newline="")
        except FileNotFoundError:
            raise CommandError(f"Nu găsesc fișierul: {path}")

        created = updated = skipped = 0

        with f:
            rdr = csv.DictReader(f)
            for rownum, row in enumerate(rdr, start=2):
                sci = as_str(row.get("Denumirea_stiintifică"))
                if not sci:
                    skipped += 1
                    continue

                defaults = dict(
                    denumire_populara = as_str(row.get("Denumirea_populară")),
                    clasa             = as_str(row.get("Clasa")),
                    familia           = as_str(row.get("Familia")),
                    habitat           = as_str(row.get("Habitat")),
                    localitatea       = as_str(row.get("Localitatea")),

                    silvice              = as_bool_plus(row.get("Silvice")),
                    pajisti_sau_stepice  = as_bool_plus(row.get("Pajisti_sau_stepice")),
                    stancarii            = as_bool_plus(row.get("Stancarii")),
                    palustre_si_acvatice = as_bool_plus(row.get("Palustre_si_acvatice")),

                    p_rara             = as_str(row.get("P_rară")),
                    conventia_berna    = as_bool_plus(row.get("Conventia_Berna")),
                    directiva_habitate = as_bool_plus(row.get("Directiva_Habitate")),
                )

                # Cartea Roșie – din CSV, Cartea_R conține de obicei CATEGORIA (EN/VU/CR…)
                cartea_r_raw = as_str(row.get("Cartea_R"))
                cartea_rosie_cat = parse_cat(cartea_r_raw)  # EN/VU/CR/...
                defaults["cartea_rosie_cat"] = cartea_rosie_cat

                # ANUL: dacă ai coloană separată (Cartea_R_An/Cartea_R_Year), o folosim;
                # altfel încercăm să extragem un an din text.
                cartea_r_an = as_str(row.get("Cartea_R_An")) or as_str(row.get("Cartea_R_Year"))
                cartea_rosie_year = parse_year(cartea_r_an) or parse_year(cartea_r_raw)

                # ✅ Regula cerută: dacă există categorie (cat) dar nu avem an -> pune 2015
                if cartea_rosie_cat and not cartea_rosie_year:
                    cartea_rosie_year = 2015

                defaults["cartea_rosie"] = cartea_rosie_year

                # Frecvența (acceptăm Frcevența/Frecevnta/Frecventa)
                frecv = as_str(row.get("Frecevnta")) or as_str(row.get("Frcevența")) or as_str(row.get("Frecventa"))
                defaults["frecventa"] = frecv


                # Frecvența (acceptăm Frcevența cu diacritice sau Frecevnta fără)
                frecv = as_str(row.get("Frecevnta")) or as_str(row.get("Frcevența")) or as_str(row.get("Frecventa"))
                defaults["frecventa"] = frecv


                obj, was_created = Species.objects.get_or_create(
                    denumire_stiintifica=sci,
                    defaults=defaults
                )
                if was_created:
                    created += 1
                else:
                    # la re-import actualizăm câmpurile dacă primim valori noi
                    changed = False
                    for field, value in defaults.items():
                        if value is not None and getattr(obj, field, None) != value:
                            setattr(obj, field, value)
                            changed = True
                    if changed:
                        obj.save()
                        updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"Import specii: create={created}, update={updated}, skip={skipped}"
        ))
