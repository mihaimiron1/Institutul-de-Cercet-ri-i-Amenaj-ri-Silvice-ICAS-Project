from django.db import migrations, models

from django.db import migrations, models

def backfill_is_rare(apps, schema_editor):
    Species = apps.get_model("core", "Species")
    # Pentru MVP: marcăm ca rare speciile care au cartea_rosie = 2015
    Species.objects.filter(cartea_rosie=2015).update(is_rare=True)


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_remove_species_core_specie_p_rara_d94577_idx_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='species',
            name='is_rare',
            field=models.BooleanField(default=False),
        ),
        migrations.RunPython(backfill_is_rare, migrations.RunPython.noop),
    ]



