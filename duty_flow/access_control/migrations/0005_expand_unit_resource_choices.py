from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("access_control", "0004_accesschoicerule_mode_accesschoicerule_units_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="accessrule",
            name="resource",
            field=models.CharField(
                choices=[
                    ("user", "Пользователи"),
                    ("person", "Сотрудники"),
                    ("unit", "Подразделения"),
                ],
                max_length=50,
                verbose_name="Ресурс",
            ),
        ),
        migrations.AlterField(
            model_name="accessfieldrule",
            name="resource",
            field=models.CharField(
                choices=[
                    ("user", "Пользователи"),
                    ("person", "Сотрудники"),
                    ("unit", "Подразделения"),
                ],
                max_length=50,
                verbose_name="Ресурс",
            ),
        ),
        migrations.AlterField(
            model_name="accesschoicerule",
            name="resource",
            field=models.CharField(
                choices=[
                    ("user", "Пользователи"),
                    ("person", "Сотрудники"),
                    ("unit", "Подразделения"),
                ],
                max_length=50,
                verbose_name="Ресурс",
            ),
        ),
    ]