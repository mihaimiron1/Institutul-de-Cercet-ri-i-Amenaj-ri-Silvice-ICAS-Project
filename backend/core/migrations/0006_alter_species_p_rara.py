from django.db import migrations

TRUE_TOKENS = {"+", "x", "✓", "1", "true", "t", "da", "yes", "y"}

def forwards(apps, schema_editor):
    Species = apps.get_model("core", "Species")
    for s in Species.objects.all():
        raw = (getattr(s, "p_rara", None) or "").strip().lower()
        s.p_rara = raw in TRUE_TOKENS
        s.save(update_fields=["p_rara"])

def backwards(apps, schema_editor):
    # invers: punem "+" pentru True, altfel gol
    Species = apps.get_model("core", "Species")
    for s in Species.objects.all():
        s.p_rara = "+" if getattr(s, "p_rara", False) else ""
        s.save(update_fields=["p_rara"])

class Migration(migrations.Migration):
    dependencies = [
        ("core", "0005_remove_occurrence_rarity_at_observation_and_more"),  # ajustează după cazul tău
    ]
    operations = [
        migrations.RunPython(forwards, backwards),
    ]
