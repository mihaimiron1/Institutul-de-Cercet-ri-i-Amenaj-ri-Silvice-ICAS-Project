# core/management/commands/import_reserves.py
import re
import csv
from typing import Optional, Tuple

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from core.models import Reserve


# ------------------------ helpers de parsing ------------------------ #

def s(v):
    """string curat sau None"""
    if v is None:
        return None
    v = str(v).strip()
    return v or None


def num(v):
    """float din string cu punct sau virgulă; None dacă nu se poate"""
    if v is None:
        return None
    vs = str(v).strip()
    if not vs:
        return None
    vs = vs.replace(",", ".")
    try:
        return float(vs)
    except ValueError:
        return None


def _to_float(deg: str, minute: Optional[str], sec: Optional[str], hemi: str) -> float:
    """deg/min/sec + emisfera (N/S/E/W) -> grade zecimale cu semn corect"""
    def _f(x):
        return float(str(x).replace(",", ".")) if x is not None and str(x).strip() != "" else 0.0

    d = _f(deg)
    m = _f(minute)
    s = _f(sec)
    val = abs(d) + m / 60.0 + s / 3600.0
    hemi = hemi.upper()
    if hemi in ("S", "W"):
        val = -val
    return val


# Regex pentru lat/lon cu DMS sau zecimal + literă emisferă.
# Exemple potrivite:
#  - 47°04′N
#  - 46.678361°N
#  - 28°30′E
#  - 28.228158°E
DMS_LAT = re.compile(
    r"""
    (?P<deg>[+-]?\d+(?:[.,]\d+)?)
    \s*(?:°|º)?\s*
    (?:
       (?P<min>[0-5]?\d(?:[.,]\d+)?)\s*(?:′|’|\'|m)?
       \s*
       (?:
          (?P<sec>[0-5]?\d(?:[.,]\d+)?)\s*(?:″|\"|s)?
       )?
    )?
    \s*(?P<hemi>[NSns])
    """,
    re.VERBOSE,
)

DMS_LON = re.compile(
    r"""
    (?P<deg>[+-]?\d+(?:[.,]\d+)?)
    \s*(?:°|º)?\s*
    (?:
       (?P<min>[0-5]?\d(?:[.,]\d+)?)\s*(?:′|’|\'|m)?
       \s*
       (?:
          (?P<sec>[0-5]?\d(?:[.,]\d+)?)\s*(?:″|\"|s)?
       )?
    )?
    \s*(?P<hemi>[EWew])
    """,
    re.VERBOSE,
)


def parse_coords(raw: Optional[str]) -> Tuple[Optional[float], Optional[float]]:
    """
    Acceptă:
      - '47°04′N 28°30′E'
      - '46.678361°N 28.228158°E'
      - '46.678361, 28.228158'
      - '46.678361 28.228158'
    Întoarce (lat, lon) sau (None, None).
    """
    if not raw:
        return None, None

    txt = str(raw).strip()

    # 1) încearcă modele cu emisferă (N/S/E/W)
    lat_m = DMS_LAT.search(txt)
    lon_m = DMS_LON.search(txt)
    if lat_m and lon_m:
        lat = _to_float(lat_m.group("deg"), lat_m.group("min"), lat_m.group("sec"), lat_m.group("hemi"))
        lon = _to_float(lon_m.group("deg"), lon_m.group("min"), lon_m.group("sec"), lon_m.group("hemi"))
        # validare simplă
        if -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0:
            return lat, lon

    # 2) fără emisferă: două numere (lat, lon) separate de virgulă / spațiu
    #   ex: "46.678361, 28.228158" sau "46.678361 28.228158"
    #   (presupunem N/E => semne pozitive)
    #   Atenție: uneori apar grade (°) ca simbol decorativ -> eliminăm
    clean = re.sub(r"[°º]", "", txt)
    # separatori: virgulă sau spațiu
    parts = re.split(r"[\s,;]+", clean.strip())
    # caută primele două valori parsabile ca float
    floats = []
    for p in parts:
        try:
            fv = float(p.replace(",", "."))
            floats.append(fv)
        except Exception:
            continue
        if len(floats) == 2:
            break
    if len(floats) == 2:
        lat, lon = floats[0], floats[1]
        if -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0:
            return lat, lon

    # 3) nu am reușit să interpretăm
    return None, None


# ------------------------ comanda de import ------------------------ #

class Command(BaseCommand):
    help = "Importă rezervații din CSV cu capete: ID,Denumirea,Raion,Amplasare,Proprietar,Suprafata,Coordonate,Categorie,Subcategorie,Diversitatea_fitocenotica"

    def add_arguments(self, parser):
        parser.add_argument("csv_path", type=str, help="Calea către rezervatii_combinate.csv")

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
            for row in rdr:
                name = s(row.get("Denumirea")) or s(row.get("name")) or s(row.get("Nume"))
                if not name:
                    skipped += 1
                    continue

                raion     = s(row.get("Raion"))
                amplasare = s(row.get("Amplasare"))
                proprietar = s(row.get("Proprietar"))
                suprafata_ha = num(row.get("Suprafata"))
                category  = s(row.get("Categorie"))
                subcat    = s(row.get("Subcategorie"))
                div_fitoc = s(row.get("Diversitatea_fitocenotica"))
                coords_raw = s(row.get("Coordonate"))

                lat = lon = None
                if coords_raw:
                    lat, lon = parse_coords(coords_raw)

                defaults = dict(
                    raion=raion,
                    amplasare=amplasare,
                    proprietar=proprietar,
                    suprafata_ha=suprafata_ha,
                    category=category,
                    subcategory=subcat,
                    diversitatea_fitocenotica=div_fitoc,
                    latitude=lat,
                    longitude=lon,
                    coords_raw=coords_raw,
                )

                obj, was_created = Reserve.objects.get_or_create(name=name, defaults=defaults)
                if was_created:
                    created += 1
                else:
                    # update "blând": doar câmpurile cu valori noi (non-None) și diferite
                    changed = False
                    for field, val in defaults.items():
                        if val is not None and getattr(obj, field, None) != val:
                            setattr(obj, field, val)
                            changed = True
                    if changed:
                        obj.save()
                        updated += 1

        self.stdout.write(self.style.SUCCESS(
            f"Reserves import: create={created}, update={updated}, skip={skipped}"
        ))
