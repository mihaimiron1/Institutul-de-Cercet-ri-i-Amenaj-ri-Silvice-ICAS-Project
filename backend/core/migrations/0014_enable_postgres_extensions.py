# Generated manually for PostgreSQL extensions

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_reserve_description_species_description'),
    ]

    operations = [
        migrations.RunSQL(
            "CREATE EXTENSION IF NOT EXISTS unaccent;",
            reverse_sql="DROP EXTENSION IF EXISTS unaccent;"
        ),
        migrations.RunSQL(
            "CREATE EXTENSION IF NOT EXISTS pg_trgm;",
            reverse_sql="DROP EXTENSION IF EXISTS pg_trgm;"
        ),
    ]
