from django.contrib.auth.models import Group, User
from django.db.models.signals import m2m_changed, post_save
from django.dispatch import receiver


ADMIN_GROUP_NAME = "Administrators"
CONTRIB_GROUP_NAME = "Contributors"


def _sync_is_staff(user: User):
    if user.is_superuser:
        return
    is_admin = user.groups.filter(name__iexact=ADMIN_GROUP_NAME).exists()
    if user.is_staff != is_admin:
        user.is_staff = is_admin
        user.save(update_fields=["is_staff"])


@receiver(m2m_changed, sender=User.groups.through)
def on_user_groups_changed(sender, instance: User, action, reverse, model, pk_set, **kwargs):
    if action in {"post_add", "post_remove", "post_clear"}:
        _sync_is_staff(instance)


@receiver(post_save, sender=User)
def on_user_created(sender, instance: User, created: bool, **kwargs):
    # Defaults: active true, staff false for normal users
    if created and not instance.is_superuser:
        changed = False
        if instance.is_active is False:
            instance.is_active = True
            changed = True
        if instance.is_staff is True and not instance.groups.filter(name__iexact=ADMIN_GROUP_NAME).exists():
            instance.is_staff = False
            changed = True
        # Ensure Contributors group exists and add user to it
        try:
            contrib_group, _ = Group.objects.get_or_create(name=CONTRIB_GROUP_NAME)
            if not instance.groups.filter(pk=contrib_group.pk).exists():
                instance.groups.add(contrib_group)
        except Exception:
            pass
        if changed:
            instance.save(update_fields=["is_active", "is_staff"])

