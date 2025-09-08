from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0015_add_fuzzy_search_indexes"),
    ]

    operations = [
        # Safe three-step swap for Site coordinates
        migrations.RenameField(
            model_name="site",
            old_name="latitude",
            new_name="latitude_tmp",
        ),
        migrations.RenameField(
            model_name="site",
            old_name="longitude",
            new_name="latitude",
        ),
        migrations.RenameField(
            model_name="site",
            old_name="latitude_tmp",
            new_name="longitude",
        ),
    ]


