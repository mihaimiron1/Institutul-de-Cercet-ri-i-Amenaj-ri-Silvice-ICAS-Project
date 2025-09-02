# core/views.py
from django.shortcuts import render
from django.http import HttpResponse, Http404, StreamingHttpResponse
from django.db.models import Q
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db.models import Max
from django.utils.timezone import localtime




# Modele – fără dubluri
from .models import (
    Reserve, Association, ReserveAssociationYear,
    Occurrence, Species, SiteHabitat, Site, Habitat,
)

# CSV/XLSX
import csv
from io import StringIO, BytesIO

class _Echo:
    def write(self, value):  # csv.writer cere un .write()
        return value

def _stream_csv(filename: str, headers, rows_iter):
    """rows_iter -> iterabil de liste/tupluri; folosește csv.writer streaming."""
    pseudo = _Echo()
    writer = csv.writer(pseudo)

    def generator():
        yield writer.writerow(headers)
        for row in rows_iter:
            yield writer.writerow(row)

    resp = StreamingHttpResponse(generator(), content_type="text/csv; charset=utf-8")
    resp["Content-Disposition"] = f'attachment; filename="{filename}"'
    return resp

def _paginate(request, qs, default=50, max_per_page=200):
    """Returnează (paginator, page_obj) pe baza ?page=&per_page=."""
    try:
        per_page = min(max_per_page, max(1, int(request.GET.get("per_page", default))))
    except ValueError:
        per_page = default
    try:
        page_no = int(request.GET.get("page", 1))
    except ValueError:
        page_no = 1
    paginator = Paginator(qs, per_page)
    return paginator, paginator.get_page(page_no)


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

@login_required
def home(request):
    stats = {
        "species": Species.objects.count(),
        "reserves": Reserve.objects.count(),
        "sites": Site.objects.count(),
        "habitats": Habitat.objects.count(),
    }

    context = {
        "stats": stats,
        "user_role": (
            "Administrator" if request.user.is_staff else
            ("Contributor" if request.user.groups.filter(name__iexact="Contributors").exists() else "Utilizator")
        ),
        "last_login": localtime(request.user.last_login) if request.user.last_login else None,
    }
    return render(request, "core/home.html", context)

@login_required
def vizualizari_home(request):
    # stub simplu până facem charts reale
    return render(request, "core/coming_soon.html", {
        "title": "Vizualizări (Charts)",
        "subtitle": "Aici vor fi grafice și hărți interactive."
    })

@login_required
def comparatii_home(request):
    # stub simplu până definim comparațiile
    return render(request, "core/coming_soon.html", {
        "title": "Comparații",
        "subtitle": "Compară rezervații, habitate sau ani diferiți."
    })

@login_required
def species_list(request):
    return HttpResponse("Test species_list – aici vor veni filtrările pentru specii.")

@login_required
@permission_required("core.view_reserveassociationyear", raise_exception=True)
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
    results = []  # listă de dict-uri {reserve, association, year, notes}

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

    # --- Export (toate rândurile din results) ---
    if export and not err:
        if export == "csv":
            headers = ["Rezervație", "Asociație", "An", "Note"]

            def rows_iter():
                for r in results:
                    yield [r["reserve"], r["association"], r["year"], r["notes"]]

            fn = f"asociatii_{mode}.csv"
            return _stream_csv(fn, headers, rows_iter())

        if export == "xlsx":
            try:
                # import "lazy" – doar dacă chiar exportăm XLSX
                from openpyxl import Workbook
            except ModuleNotFoundError:
                # mesaj clar dacă lipsește openpyxl
                return HttpResponse(
                    "Export XLSX necesită pachetul 'openpyxl'. Rulează: pip install openpyxl",
                    content_type="text/plain; charset=utf-8",
                    status=500
                )
            wb = Workbook()
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

    # --- HTML (paginăm results pentru afișare) ---
    paginator, page_obj = _paginate(request, results, default=50)
    return render(request, "core/associations_filters.html", {
        "all_reserves": all_reserves,
        "mode": mode,
        "reserve_name": reserve_name,
        "year_q": year_q,
        "rows": page_obj.object_list,
        "page_obj": page_obj,
        "paginator": paginator,
        "error": err,
    })

@login_required
@permission_required("core.view_occurrence", raise_exception=True)
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

    # Paginăm queryset-ul și construim rândurile DOAR pentru pagina curentă
    paginator, page_obj = _paginate(request, qs, default=50)
    rows = []
    for o in page_obj.object_list:
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
        "page_obj": page_obj,
        "paginator": paginator,
        "error": error,
    })


@login_required
@permission_required("core.view_sitehabitat", raise_exception=True)
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

    qs_full = SiteHabitat.objects.select_related("site", "habitat")

    if mode == "by_site" and site_name:
        qs_full = qs_full.filter(site__name__iexact=site_name).order_by(
            "year", "habitat__name_romanian", "habitat__name_english"
        )
        title = f"Habitate în site-ul: {site_name}"
    elif mode == "by_habitat" and habitat_name:
        qs_full = qs_full.filter(
            Q(habitat__name_romanian__iexact=habitat_name) |
            Q(habitat__name_english__iexact=habitat_name) |
            Q(habitat__code__iexact=habitat_name)
        ).order_by("year", "site__name")
        title = f"Site-uri pentru habitat: {habitat_name}"
    elif mode == "by_year" and year.isdigit():
        qs_full = qs_full.filter(year=int(year)).order_by(
            "site__name", "habitat__name_romanian", "habitat__name_english"
        )
        title = f"Relații Site–Habitat în anul: {year}"
    else:
        qs_full = qs_full.none()
        title = "Selectează un filtru"

    # Export (din QS-ul complet, nu doar pagina curentă)
    if export in ("csv", "xlsx"):
        return _export_sitehab(qs_full, export)

    # Paginăm pentru afișare
    paginator, page_obj = _paginate(request, qs_full, default=50)
    qs = page_obj.object_list  # pentru compatibilitate cu template-ul existent

    sites = Site.objects.order_by("name").values_list("name", flat=True)
    habitats = Habitat.objects.order_by("name_romanian", "name_english").values_list("name_romanian", flat=True)

    return render(request, "core/sitehab_filters.html", {
        "mode": mode,
        "site_name": site_name,
        "habitat_name": habitat_name,
        "year": year,
        "qs": qs,
        "page_obj": page_obj,
        "paginator": paginator,
        "title": title,
        "sites": list(sites),
        "habitats": list(habitats),
    })
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

@login_required
def comparatii_home(request):
    return render(request, "core/comparatii_home.html")


@login_required
def _export_sitehab(qs, kind):
    headers = ["Site", "Habitat (RO)", "Habitat (EN)", "Cod habitat", "An", "Suprafață (ha)", "Notițe"]

    if kind == "csv":
        def rows_iter():
            for r in qs:
                yield [
                    r.site.name,
                    getattr(r.habitat, "name_romanian", "") or "",
                    getattr(r.habitat, "name_english", "") or "",
                    getattr(r.habitat, "code", "") or "",
                    r.year,
                    r.surface if r.surface is not None else "",
                    r.notes or "",
                ]
        return _stream_csv("site_habitats.csv", headers, rows_iter())

    # XLSX – import "lazy"
    try:
        from openpyxl import Workbook
    except ModuleNotFoundError:
        return HttpResponse(
            "Export XLSX necesită pachetul 'openpyxl'. Rulează: pip install openpyxl",
            content_type="text/plain; charset=utf-8",
            status=500
        )

    wb = Workbook()
    ws = wb.active
    ws.title = "SiteHabitats"
    ws.append(headers)
    for r in qs:
        ws.append([
            r.site.name,
            getattr(r.habitat, "name_romanian", "") or "",
            getattr(r.habitat, "name_english", "") or "",
            getattr(r.habitat, "code", "") or "",
            r.year,
            r.surface if r.surface is not None else "",
            r.notes or "",
        ])
    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)
    resp = HttpResponse(
        stream.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    resp["Content-Disposition"] = 'attachment; filename="site_habitats.xlsx"'
    return resp
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