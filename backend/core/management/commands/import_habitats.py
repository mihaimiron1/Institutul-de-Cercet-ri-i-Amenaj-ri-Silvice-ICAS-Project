# core/management/commands/import_habitats.py
import csv
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from core.models import Habitat


class Command(BaseCommand):
    help = "Importă habitate din CSV (coloane: denumirea_engleza, denumirea_romana, codul)"

    def add_arguments(self, parser):
        # Poți pasa alt CSV cu: --file=cale/catre/alt.csv
        parser.add_argument("--file", default="data/habitate.csv")

    def _resolve_path(self, file_arg: str) -> Path:
        """Rezolvă calea fișierului:
        - dacă e absolută -> o folosește
        - dacă e relativă -> încearcă:
            1) <BASE_DIR>/<file_arg>        (ex: backend/data/habitate.csv)
            2) <BASE_DIR>/../<file_arg>     (ex: data/habitate.csv lângă backend)
        """
        p = Path(file_arg)
        if p.is_absolute() and p.exists():
            return p

        base = Path(settings.BASE_DIR)
        candidates = [
            base / file_arg,
            base.parent / file_arg,
        ]
        for c in candidates:
            if c.exists():
                return c

        # ca fallback: întoarce prima variantă (pt. mesaj de eroare clar)
        return candidates[0]

    def handle(self, *args, **opts):
        path = self._resolve_path(opts["file"])
        if not path.exists():
            raise CommandError(f"Fișierul nu a fost găsit: {path}")

        created = updated = skipped = 0

        with path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            required = {"denumirea_engleza", "denumirea_romana"}
            headers = set(reader.fieldnames or [])
            if not required.issubset(headers):
                raise CommandError(
                    "Fișierul trebuie să conțină coloanele: denumirea_engleza, denumirea_romana "
                    "(opțional: codul)"
                )

            for i, row in enumerate(reader, start=1):
                name_english = (row.get("denumirea_engleza") or "").strip()
                name_romanian = (row.get("denumirea_romana") or "").strip()
                code = (row.get("codul") or "").strip() or None

                if not name_english or not name_romanian:
                    skipped += 1
                    continue

                obj, is_created = Habitat.objects.update_or_create(
                    name_english=name_english,
                    name_romanian=name_romanian,
                    defaults={"code": code},
                )
                if is_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"Habitate importate din {path} — create={created}, update={updated}, skip={skipped}"
        ))
