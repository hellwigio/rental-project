from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0002_migrate_roles_to_groups"),
    ]

    operations = [
        migrations.RemoveConstraint(model_name="user", name="user_valid_role"),
        migrations.RemoveField(model_name="user", name="role"),
    ]
