# Generated manually for fuzzy search indexes

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0014_enable_postgres_extensions'),
    ]

    operations = [
        # Create immutable unaccent function for indexes
        migrations.RunSQL(
            "CREATE OR REPLACE FUNCTION immutable_unaccent(text) RETURNS text AS $$ SELECT public.unaccent($1) $$ LANGUAGE sql IMMUTABLE;",
            reverse_sql="DROP FUNCTION IF EXISTS immutable_unaccent(text);"
        ),
        
        # Association indexes (name + optional metadata if present in schema)
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS core_association_name_unaccent_trgm_idx ON core_association USING gin (immutable_unaccent(lower(name)) gin_trgm_ops);",
            reverse_sql="DROP INDEX IF EXISTS core_association_name_unaccent_trgm_idx;"
        ),

        # Site indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS core_site_name_unaccent_trgm_idx ON core_site USING gin (immutable_unaccent(lower(name)) gin_trgm_ops);",
            reverse_sql="DROP INDEX IF EXISTS core_site_name_unaccent_trgm_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS core_site_code_unaccent_trgm_idx ON core_site USING gin (immutable_unaccent(lower(code)) gin_trgm_ops);",
            reverse_sql="DROP INDEX IF EXISTS core_site_code_unaccent_trgm_idx;"
        ),
        
        # Habitat indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS core_habitat_name_romanian_unaccent_trgm_idx ON core_habitat USING gin (immutable_unaccent(lower(name_romanian)) gin_trgm_ops);",
            reverse_sql="DROP INDEX IF EXISTS core_habitat_name_romanian_unaccent_trgm_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS core_habitat_name_english_unaccent_trgm_idx ON core_habitat USING gin (immutable_unaccent(lower(name_english)) gin_trgm_ops);",
            reverse_sql="DROP INDEX IF EXISTS core_habitat_name_english_unaccent_trgm_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS core_habitat_code_unaccent_trgm_idx ON core_habitat USING gin (immutable_unaccent(lower(code)) gin_trgm_ops);",
            reverse_sql="DROP INDEX IF EXISTS core_habitat_code_unaccent_trgm_idx;"
        ),
    ]
