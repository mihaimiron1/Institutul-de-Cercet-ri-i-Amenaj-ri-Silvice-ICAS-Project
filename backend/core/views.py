# core/views.py
from django.shortcuts import render
from django.http import HttpResponse, Http404
from django.db.models import Q
from .models import Reserve, Association, ReserveAssociationYear
import csv
from io import StringIO, BytesIO

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