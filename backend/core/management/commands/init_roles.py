from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from core.models import (
    Species, Reserve, Association, ReserveAssociationYear,
    Occurrence, Habitat, Site, SiteHabitat
)

class Command(BaseCommand):
    help = "Creează grupurile Administrators și Contributors și le atașează permisiunile potrivite"

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

        # --- Contributors: add/change/view pe Occurrence și SiteHabitat (fără delete) ---
        contrib_models = [Occurrence, SiteHabitat]
        contrib_perms = set()
        for model in contrib_models:
            ct = ct_map.get(model) or ContentType.objects.get_for_model(model)
            codes = [f"add_{model._meta.model_name}",
                     f"change_{model._meta.model_name}",
                     f"view_{model._meta.model_name}"]
            contrib_perms.update(Permission.objects.filter(content_type=ct, codename__in=codes))

        contrib.permissions.set(contrib_perms)
        # sau: contrib.permissions.add(*contrib_perms)

        self.stdout.write(self.style.SUCCESS(
            f"OK: Administrators({len(admin_perms)}) & Contributors({len(contrib_perms)}) permisiuni setate."
        ))
