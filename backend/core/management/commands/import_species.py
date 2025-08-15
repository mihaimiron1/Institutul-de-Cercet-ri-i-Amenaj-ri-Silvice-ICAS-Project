# core/management/commands/import_species.py
import csv
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from core.models import Species

def as_bool(val):
    if val is None: 
        return False
    s = str(val).strip().lower()
    return s in {"1","true","da","yes","y","t","x","✓"}

def as_str(val):
    if val is None: 
        return None
    s = str(val).strip()
    return s or None

def as_int(val):
    if val is None or str(val).strip()=="":
        return None
    try:
        return int(str(val).strip())
    except ValueError:
        return None

class Command(BaseCommand):
    help = "Importă specii dintr-un CSV cu antetele din p1."

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Calea către species.csv")

    @transaction.atomic
    def handle(self, *args, **opts):
        path = opts["csv_path"]
        created, updated, skipped = 0, 0, 0

        try:
            f = open(path, encoding="utf-8-sig", newline="")
        except FileNotFoundError:
            raise CommandError(f"Nu găsesc fișierul: {path}")

        with f:
            rdr = csv.DictReader(f)
            # Așteptăm antete în română (cum le ai în p1):
            # Denumirea_stiintifică, Denumirea_populară, Clasa, Familia, Habitat, Localitatea,
            # Silvice, Pajisti_sau_stepice, Stancarii, Palustre_si_acvatice,
            # P_rară, Conventia_Berna, Directiva_Habitate, RM_Cartea_R_2015 (opțional ori gol)
            for i, row in enumerate(rdr, start=2):
                sci = as_str(row.get("Denumirea_stiintifică"))
                if not sci:
                    skipped += 1
                    continue

                obj, was_created = Species.objects.get_or_create(
                    denumire_stiintifica=sci,
                    defaults=dict(
                        denumire_populara=as_str(row.get("Denumirea_populară")),
                        clasa=as_str(row.get("Clasa")),
                        familia=as_str(row.get("Familia")),
                        habitat=as_str(row.get("Habitat")),
                        localitatea=as_str(row.get("Localitatea")),
                        silvice=as_bool(row.get("Silvice")),
                        pajisti_sau_stepice=as_bool(row.get("Pajisti_sau_stepice")),
                        stancarii=as_bool(row.get("Stancarii")),
                        palustre_si_acvatice=as_bool(row.get("Palustre_si_acvatice")),
                        p_rara=as_str(row.get("P_rară")),  # 'comuna' | 'rara' | 'critica' sau gol
                        conventia_berna=as_bool(row.get("Conventia_Berna")),
                        directiva_habitate=as_bool(row.get("Directiva_Habitate")),
                        # dacă ai schimbat în models.py la 'cartea_rosie' (an), mapează aici:
                        # cartea_rosie=as_int(row.get("RM_Cartea_R_2015")),
                        rm_cartea_rosie_2015=as_bool(row.get("RM_Cartea_R_2015")),
                    )
                )
                if was_created:
                    created += 1
                else:
                    # opțional: update ușor dacă vrei să sincronizezi câmpuri la re-import
                    updated += 1  # sau fă assign pe câmpuri și obj.save()

        self.stdout.write(self.style.SUCCESS(
            f"Species import: create={created}, update={updated}, skip={skipped}"
        ))
