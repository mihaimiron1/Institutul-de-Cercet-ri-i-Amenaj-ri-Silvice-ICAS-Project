from django.contrib.auth.decorators import user_passes_test

def in_group(group_name: str):
    def check(user):
        return user.is_authenticated and user.groups.filter(name=group_name).exists()
    return user_passes_test(check)

is_admin_required = in_group("Administrators")
is_contributor_required = in_group("Contributors")