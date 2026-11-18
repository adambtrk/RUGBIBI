from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_federation_club_clubmembership_and_more"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="club", name="unique_club_per_federation",
        ),
        migrations.RenameModel(old_name="Federation", new_name="Division"),
        migrations.RenameField(
            model_name="club", old_name="federation", new_name="division",
        ),
        migrations.AlterModelOptions(
            name="division", options={"ordering": ["name"], "verbose_name": "division"},
        ),
        migrations.AlterField(
            model_name="club", name="division",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="clubs", to="accounts.division", verbose_name="division",
            ),
        ),
        migrations.AddConstraint(
            model_name="club",
            constraint=models.UniqueConstraint(
                fields=("name", "division"), name="unique_club_per_division",
            ),
        ),
    ]
