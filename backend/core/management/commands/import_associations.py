# core/management/commands/import_associations.py
import csv
import re
import unicodedata
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from core.models import Association


def s(v):
    """string sau None (tăiat la capete)"""
    if v is None:
        return None
    v = str(v).strip()
    return v or None


def clean_name(name: str) -> str:
    """
    Curăță denumirea:
      - normalizează unicode (NFKC) ca să uniformizezi apostrofuri/ghilimele
      - taie spații la capete
      - înlătură virgulele/semicolonul rătăcite la final
      - comprimă multiple spații în unul singur
    """
    n = unicodedata.normalize("NFKC", name).strip()
    n = re.sub(r"[,\s;]+$", "", n)           # ex: "… 1957, " -> "… 1957"
    n = re.sub(r"\s+", " ", n)               # spații multiple -> unul singur
    return n


class Command(BaseCommand):
    help = "Importă asociații din CSV cu capete: ID,Denumirea"

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Calea către CSV (ex.: data\\asociatii.csv)")

    @transaction.atomic
    def handle(self, *args, **opts):
        path = opts["csv_path"]

        try:
            f = open(path, encoding="utf-8-sig", newline="")
        except FileNotFoundError:
            raise CommandError(f"Nu găsesc fișierul: {path}")

        created = updated = skipped = dup_in_file = 0
        seen = set()

        with f:
            rdr = csv.DictReader(f)
            # Acceptăm fie 'Denumirea', fie 'name' ca și cap de coloană
            if "Denumirea" not in rdr.fieldnames and "name" not in rdr.fieldnames:
                raise CommandError("CSV trebuie să conțină coloana 'Denumirea' (sau 'name').")

            for rownum, row in enumerate(rdr, start=2):
                raw = s(row.get("Denumirea") or row.get("name"))
                if not raw:
                    skipped += 1
                    continue

                name = clean_name(raw)
                if not name:
                    skipped += 1
                    continue

                # dubluri în același fișier
                key = name.lower()
                if key in seen:
                    dup_in_file += 1
                    continue
                seen.add(key)

                # get_or_create pe nume canonic (name este UNIQUE în model)
                obj, was_created = Association.objects.get_or_create(name=name)
                if was_created:
                    created += 1
                else:
                    # nimic de actualizat: cheia e chiar 'name'
                    updated += 0

        self.stdout.write(self.style.SUCCESS(
            f"Associations import: create={created}, update={updated}, skip={skipped}, dup_in_file={dup_in_file}"
        ))
