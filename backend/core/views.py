# core/views.py
from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.db.models import Q
from .models import Reserve, Association, ReserveAssociationYear
from .models import Occurrence, Species, Reserve, SiteHabitat, Site, Habitat
import csv
from io import StringIO, BytesIO
from django.contrib.auth.decorators import login_required
from openpyxl import Workbook






def _resolve_reserve(q):
    """
    Permite căutare fie după id (număr), fie după nume (case-insensitive contains).
    Returnează un obiect Reserve sau ridică Http404.
    """
    if not q:
        raise Http404("Lipsește parametrul 'reserve'")
    if str(q).isdigit():
        try:
            return Reserve.objects.get(pk=int(q))
        except Reserve.DoesNotExist:
            raise Http404("Rezervație inexistentă")
    # nume parțial
    try:
        return Reserve.objects.get(name__iexact=q)
    except Reserve.DoesNotExist:
        # fallback: primul match parțial
        match = Reserve.objects.filter(name__icontains=q).first()
        if not match:
            raise Http404("Rezervație inexistentă")
        return match

def home(request):
    return HttpResponse("Pagina principală funcționează.")

def species_list(request):
    return HttpResponse("Test species_list – aici vor veni filtrările pentru specii.")


def associations_filters_page(request):
    """
    Pagina cu cele 3 filtrări + export CSV/XLSX.
    GET:
      mode: one_of ["by_reserve_year", "by_reserve_all_years", "by_year_all_reserves"]
      reserve_name: nume rezervație (când e nevoie)
      year: YYYY (când e nevoie)
      export: "csv" | "xlsx"
    """

    mode = (request.GET.get("mode") or "").strip() or "by_reserve_year"
    reserve_name = (request.GET.get("reserve_name") or "").strip()
    year_q = (request.GET.get("year") or "").strip()
    export = (request.GET.get("export") or "").strip().lower()

    # dropdown: toate rezervațiile alfabetic (doar pt UI)
    all_reserves = Reserve.objects.order_by("name").only("id", "name")

    # construim queryset-ul în funcție de mod
    links = ReserveAssociationYear.objects.select_related("reserve", "association")

    err = None
    results = []

    def push_rows(qs):
        rows = []
        for l in qs:
            rows.append({
                "reserve": l.reserve.name,
                "association": l.association.name,
                "year": l.year,
                "notes": l.notes or "",
            })
        return rows

    if mode == "by_reserve_year":
        if not reserve_name or not year_q.isdigit():
            err = "Alege o rezervație și un an."
        else:
            qs = links.filter(
                reserve__name__iexact=reserve_name,
                year=int(year_q)
            ).order_by("association__name")
            results = push_rows(qs)

    elif mode == "by_reserve_all_years":
        if not reserve_name:
            err = "Alege o rezervație."
        else:
            qs = links.filter(
                reserve__name__iexact=reserve_name
            ).order_by("-year", "association__name")
            results = push_rows(qs)

    elif mode == "by_year_all_reserves":
        if not year_q.isdigit():
            err = "Alege un an."
        else:
            qs = links.filter(
                year=int(year_q)
            ).order_by("reserve__name", "association__name")
            results = push_rows(qs)
    else:
        err = "Mod invalid."

    # --- Export ---
    if export and not err:
        if export == "csv":
            sio = StringIO()
            w = csv.writer(sio)
            w.writerow(["Rezervație", "Asociație", "An", "Note"])
            for r in results:
                w.writerow([r["reserve"], r["association"], r["year"], r["notes"]])
            resp = HttpResponse(sio.getvalue(), content_type="text/csv; charset=utf-8")
            fn = f"asociatii_{mode}.csv"
            resp["Content-Disposition"] = f'attachment; filename="{fn}"'
            return resp

        if export == "xlsx":
            try:
                import openpyxl
                wb = openpyxl.Workbook()
                ws = wb.active
                ws.title = "Asociatii"
                ws.append(["Rezervație", "Asociație", "An", "Note"])
                for r in results:
                    ws.append([r["reserve"], r["association"], r["year"], r["notes"]])
                bio = BytesIO()
                wb.save(bio)
                bio.seek(0)
                resp = HttpResponse(
                    bio.read(),
                    content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                fn = f"asociatii_{mode}.xlsx"
                resp["Content-Disposition"] = f'attachment; filename="{fn}"'
                return resp
            except ModuleNotFoundError:
                # mesaj clar dacă lipsește openpyxl
                return HttpResponse(
                    "Export XLSX necesită pachetul 'openpyxl'. Rulează: pip install openpyxl",
                    content_type="text/plain; charset=utf-8",
                    status=500
                )

    # --- HTML ---
    return render(request, "core/associations_filters.html", {
        "all_reserves": all_reserves,
        "mode": mode,
        "reserve_name": reserve_name,
        "year_q": year_q,
        "rows": results[:2000],
        "error": err,
    })

def occurrences_filters_page(request):
    """
    4 moduri:
      - by_reserve_all:    plante (toate) din rezervația X
      - by_reserve_rare:   plante rare din rezervația X
      - by_raion_all:      plante (toate) pe raionul R
      - by_raion_rare:     plante rare pe raionul R
    GET:
      mode: vezi mai sus (default by_reserve_all)
      reserve_name: necesar în modurile 'by_reserve_*' (după nume, nu ID)
      raion:        necesar în modurile 'by_raion_*'
    """
    mode = (request.GET.get("mode") or "by_reserve_all").strip()
    reserve_name = (request.GET.get("reserve_name") or "").strip()
    raion = (request.GET.get("raion") or "").strip()

    # dropdown-uri
    all_reserves = Reserve.objects.order_by("name").only("id", "name")
    all_raions = (Reserve.objects
                  .exclude(raion__isnull=True).exclude(raion="")
                  .values_list("raion", flat=True).distinct().order_by("raion"))

    qs = (Occurrence.objects
          .select_related("species", "reserve")
          .all())

    error = None

    if mode in ("by_reserve_all", "by_reserve_rare"):
        if not reserve_name:
            error = "Alege o rezervație."
            qs = qs.none()
        else:
            qs = qs.filter(reserve__name__iexact=reserve_name)
            if mode == "by_reserve_rare":
                qs = qs.filter(Q(is_rare=True) | Q(species__is_rare=True))

    elif mode in ("by_raion_all", "by_raion_rare"):
        if not raion:
            error = "Alege un raion."
            qs = qs.none()
        else:
            qs = qs.filter(reserve__raion__iexact=raion)
            if mode == "by_raion_rare":
                qs = qs.filter(Q(is_rare=True) | Q(species__is_rare=True))

    else:
        error = "Mod invalid."
        qs = qs.none()

    # Sortare prietenoasă: după rezervație, apoi specie, apoi an desc
    qs = qs.order_by("reserve__name", "species__denumire_stiintifica", "-year")

    # Pregătim rândurile pentru tabel
    rows = []
    for o in qs[:2000]:  # limit de siguranță
        rows.append({
            "reserve": o.reserve.name,
            "raion": o.reserve.raion or "",
            "species_sci": o.species.denumire_stiintifica,
            "species_pop": o.species.denumire_populara or "",
            "year": o.year,
            "rare": "Da" if (o.is_rare or o.species.is_rare) else "Nu",
            "lat": o.latitude,
            "lon": o.longitude,
        })

    return render(request, "core/occurrences_filters.html", {
        "mode": mode,
        "reserve_name": reserve_name,
        "raion": raion,
        "all_reserves": all_reserves,
        "all_raions": all_raions,
        "rows": rows,
        "error": error,
    })

@login_required
def sitehab_filters_page(request):
    """
    Mode:
      - by_site:     toate habitatele din site-ul X (param: site_name)
      - by_habitat:  toate site-urile care conțin habitatul H (param: habitat_name)
      - by_year:     toate relațiile din anul Y (param: year)
    Export:
      - ?export=csv  sau  ?export=xlsx
    """
    mode = request.GET.get("mode", "by_site")
    site_name = (request.GET.get("site_name") or "").strip()
    habitat_name = (request.GET.get("habitat_name") or "").strip()
    year = (request.GET.get("year") or "").strip()
    export = (request.GET.get("export") or "").strip().lower()

    qs = SiteHabitat.objects.select_related("site", "habitat")

    if mode == "by_site" and site_name:
        qs = qs.filter(site__name__iexact=site_name).order_by("year", "habitat__name_romanian", "habitat__name_english")
        title = f"Habitate în site-ul: {site_name}"
    elif mode == "by_habitat" and habitat_name:
        qs = qs.filter(
            Q(habitat__name_romanian__iexact=habitat_name) |
            Q(habitat__name_english__iexact=habitat_name) |
            Q(habitat__code__iexact=habitat_name)
        ).order_by("year", "site__name")
        title = f"Site-uri pentru habitat: {habitat_name}"
    elif mode == "by_year" and year.isdigit():
        qs = qs.filter(year=int(year)).order_by("site__name", "habitat__name_romanian", "habitat__name_english")
        title = f"Relații Site–Habitat în anul: {year}"
    else:
        qs = qs.none()
        title = "Selectează un filtru"

    if export in ("csv", "xlsx"):
        return _export_sitehab(qs, export)

    sites = Site.objects.order_by("name").values_list("name", flat=True)
    habitats = Habitat.objects.order_by("name_romanian", "name_english").values_list("name_romanian", flat=True)

    return render(request, "core/sitehab_filters.html", {
        "mode": mode,
        "site_name": site_name,
        "habitat_name": habitat_name,
        "year": year,
        "qs": qs,
        "title": title,
        "sites": list(sites),
        "habitats": list(habitats),
    })


def _export_sitehab(qs, kind):
    headers = ["Site", "Habitat (RO)", "Habitat (EN)", "Cod habitat", "An", "Suprafață (ha)", "Notițe"]
    rows = [
        [
            r.site.name,
            getattr(r.habitat, "name_romanian", "") or "",
            getattr(r.habitat, "name_english", "") or "",
            getattr(r.habitat, "code", "") or "",
            r.year,
            r.surface if r.surface is not None else "",
            r.notes or "",
        ]
        for r in qs
    ]

    if kind == "csv":
        buf = StringIO()
        writer = csv.writer(buf)
        writer.writerow(headers)
        writer.writerows(rows)
        resp = HttpResponse(buf.getvalue(), content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = 'attachment; filename="site_habitats.csv"'
        return resp

    wb = Workbook()
    ws = wb.active
    ws.title = "SiteHabitats"
    ws.append(headers)
    for row in rows:
        ws.append(row)
    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)
    resp = HttpResponse(stream.read(), content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    resp["Content-Disposition"] = 'attachment; filename="site_habitats.xlsx"'
    return resp