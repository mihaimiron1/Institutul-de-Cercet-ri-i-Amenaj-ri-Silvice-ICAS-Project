from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType

from core.models import (
    Species, Reserve, Association, ReserveAssociationYear,
    Occurrence, Habitat, Site, SiteHabitat
)

class Command(BaseCommand):
    help = "Creează grupurile Administrators și Contributors; admin=all perms, contributors baseline access"

    def handle(self, *args, **kwargs):
        admins, _ = Group.objects.get_or_create(name="Administrators")
        contrib, _ = Group.objects.get_or_create(name="Contributors")

        # --- Administrators: toate permisiunile pe toate modelele aplicației ---
        admin_models = [Species, Reserve, Association, ReserveAssociationYear,
                        Occurrence, Habitat, Site, SiteHabitat]

        ct_map = ContentType.objects.get_for_models(*admin_models)
        admin_perms = set()
        for model, ct in ct_map.items():
            admin_perms.update(Permission.objects.filter(content_type=ct))

        # dacă vrei să sincronizezi exact perm-urile (recomandat):
        admins.permissions.set(admin_perms)
        # dacă preferi să nu atingi ce există deja, folosește:
        # admins.permissions.add(*admin_perms)

        # --- Contributors: în noul model, nu impunem perm-uri granulate; accesul e dat de login ---
        contrib.permissions.clear()

        # Backfill is_staff based on Administrator membership (superusers unchanged)
        updated_true = 0
        updated_false = 0
        for u in User.objects.all():
            if u.is_superuser:
                continue
            is_admin = u.groups.filter(name__iexact="Administrators").exists()
            if u.is_staff != is_admin:
                u.is_staff = is_admin
                u.save(update_fields=["is_staff"])
                if is_admin:
                    updated_true += 1
                else:
                    updated_false += 1

        self.stdout.write(self.style.SUCCESS(
            f"OK: Admin perms={len(admin_perms)}, Contributors cleared. "
            f"Backfilled is_staff true: {updated_true}, false: {updated_false}."
        ))
