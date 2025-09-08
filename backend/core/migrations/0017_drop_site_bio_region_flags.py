from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0016_swap_site_lat_lon"),
    ]

    operations = [
        migrations.RemoveField(model_name="site", name="bio_region_stepica"),
        migrations.RemoveField(model_name="site", name="bio_region_continentala"),
    ]


