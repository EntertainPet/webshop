from __future__ import annotations
import uuid
from django.db import migrations, models


def generate_seguimiento_tokens(apps, schema_editor):
    Pedido = apps.get_model('home', 'Pedido')
    # For any existing Pedido without a token, generate a unique UUID
    for pedido in Pedido.objects.filter(seguimiento_token__isnull=True):
        pedido.seguimiento_token = uuid.uuid4()
        pedido.save(update_fields=["seguimiento_token"])


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0001_initial"),
    ]

    operations = [
        # 1) Add a nullable token column so the DB change is non-destructive
        migrations.AddField(
            model_name="pedido",
            name="seguimiento_token",
            field=models.UUIDField(null=True, editable=False),
        ),

        # 2) Backfill values for existing rows
        migrations.RunPython(generate_seguimiento_tokens, reverse_code=migrations.RunPython.noop),

        # 3) Make the field non-nullable and unique going forward
        migrations.AlterField(
            model_name="pedido",
            name="seguimiento_token",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
