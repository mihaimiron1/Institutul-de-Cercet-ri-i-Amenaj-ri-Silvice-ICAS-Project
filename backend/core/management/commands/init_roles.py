from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from core.models import Species, Reserve, Association, ReserveAssociationYear, Occurrence

class Command(BaseCommand):
    help = "Create default groups and assign permissions"

    def handle(self, *args, **kwargs):
        admins, _ = Group.objects.get_or_create(name="Administrators")
        contrib, _ = Group.objects.get_or_create(name="Contributors")

        # Administrators: full perms on toate modelele din app
        for model in [Species, Reserve, Association, ReserveAssociationYear, Occurrence]:
            ct = ContentType.objects.get_for_model(model)
            perms = Permission.objects.filter(content_type=ct)
            admins.permissions.add(*perms)

        # Contributors: doar CRUD pe date (ajustează după nevoie)
        for model in [Occurrence, Species, Reserve, Association]:
            ct = ContentType.objects.get_for_model(model)
            for codename in ["add", "change", "delete", "view"]:
                p = Permission.objects.get(content_type=ct, codename=f"{codename}_{model._meta.model_name}")
                contrib.permissions.add(p)

        self.stdout.write(self.style.SUCCESS("Groups & perms initialized"))
