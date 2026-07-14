from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0002_impostazioni_sistema"),
    ]

    operations = [
        migrations.AlterField(
            model_name="user",
            name="ruolo",
            field=models.CharField(
                choices=[
                    ("DIPENDENTE", "Dipendente"),
                    ("REFERENTE", "Referente Academy"),
                ],
                default="DIPENDENTE",
                max_length=20,
            ),
        ),
    ]
