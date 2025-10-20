# Institutul-de-Cercet-ri-i-Amenaj-ri-Silvice-ICAS-Project

# SILVA — Biodiversity Curation & Analysis (Django)

[![Python 3.13](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/)
[![Django 5.2](https://img.shields.io/badge/Django-5.2.x-092E20.svg)](https://docs.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-336791.svg)](https://www.postgresql.org/)
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)](#license)

> A lightweight Django web app for curating and exploring biodiversity data about **plants**, **reserves**, **associations**, **sites**, and **habitats**—with CSV imports, fine-grained filters, rare-species comparisons, and exports (CSV/XLSX). Initial focus: Moldova/Romania (ICAS context).

---

## Overview

SILVA consolidates heterogeneous sources (CSV, fieldwork, literature/web) into a clean relational database and provides:
- **Stewardship tools** (admin-grade CRUD, validation)
- **Discovery & analysis** (tolerant search, filtering, comparisons)
- **Reproducible outputs** (streamed CSV, optional Excel)

It’s designed for institutional workflows today and public read-only access later.

---

## Core Features

- **Entities & relations**: Species, Reserves, Associations, Sites, Habitats  
  - Junctions: `Occurrence` (Species–Reserve–Year), `SiteHabitat` (Site–Habitat–Year), `ReserveAssociationYear` (Association–Reserve–Year)
- **Advanced filtering**: by reserve/raion (with *rare only* toggle), by site/habitat/year
- **Comparisons**: rare species across years (within a reserve) or across multiple reserves
- **Search UX**: diacritics/typo-tolerant (`unaccent` + `pg_trgm`)
- **Exports**: CSV (streaming), XLSX (via `openpyxl`, graceful CSV fallback)

---

## Tech Stack

- **Backend**: Python 3.13, Django 5.2.x (FBV), PostgreSQL 16+
- **Search/Similarity**: PostgreSQL `unaccent`, `pg_trgm`
- **Packaging**: `psycopg` (v3), `django-environ`, `django-extensions`, `openpyxl` (optional)
- **Auth/Perms**: Django sessions; roles: **Administrators** / **Contributors** (future **Guests** read-only)
- **Ops**: `.env` config, migrations, optional Neon PostgreSQL (TLS)

---

## Quick Start


# 1) Clone & venv
```bash
git clone https://github.com/mihaimiron1/Institutul-de-Cercet-ri-i-Amenaj-ri-Silvice-ICAS-Project.git
```
```bash
cd /backend
```
```bash
python -m venv .venv
```
# Windows:
```bash
.venv\Scripts\activate
```
Unix/Mac: 
```bash
source .venv/bin/activate
```
# 2) Install
```bash
pip install -U pip
pip install -r requirements.txt
```

# 3) Configure (.env in backend/)
```bash
DEBUG=True
SECRET_KEY=replace-with-a-random-secret
ALLOWED_HOSTS=127.0.0.1,localhost

DB_NAME=your_db
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=localhost          # or Neon host (e.g., ep-xxxx-xxxx.xx-aws.neon.tech)
DB_PORT=5432
DB_SSLMODE=require         # keep 'require' for Neon
ENV
```
# 4) Database & run
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 0.0.0.0:8000
```
# 5) Project Structure
backend/

  silva/                 # Django project (settings, urls)
  
  core/                  # Single app: models, views, forms, admin, middleware
  
  management/commands/ # CSV importers (species, reserves, sites, habitats, associations)
  
  templates/           # Filters, lists, comparisons, additions
  
  static/              # CSS/JS (incl. small admin helpers)
    
# 6) Typical Flow
- **Filter Occurrences** → by reserve/raion (+ rare only) → paginate → Export CSV/XLSX
- **Compare Rare Species** → select reserve + 2–4 years or reserve:year pairs → presence/absence matrix
- **Add Data** (Contributors) → “Additions” pages with large searchable comboboxes
- **Admin** → /admin/ for full CRUD, roles, imports via management commands
# 6) Security & Integrity (essentials)
- **Session auth; login-required middleware (small whitelist)**
- **CSRF enabled; server-side validation (ranges, uniqueness, coordinates, year bounds)**
- **DB constraints (unique keys, composite uniqueness on junctions)**
- **TLS to DB (sslmode=require), env-driven secrets**
