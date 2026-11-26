from itertools import islice

from django.db import migrations


def assign_groups(apps, schema_editor):
    database = schema_editor.connection.alias
    users = apps.get_model("users", "User").objects.using(database)
    groups = apps.get_model("auth", "Group").objects.using(database)
    for name in ("renter", "landlord"):
        group, _ = groups.get_or_create(name=name)
        user_ids = users.filter(role=name).values_list("pk", flat=True).iterator(chunk_size=1000)
        while batch := list(islice(user_ids, 1000)):
            group.user_set.add(*batch)


def restore_roles(apps, schema_editor):
    database = schema_editor.connection.alias
    users = apps.get_model("users", "User").objects.using(database)
    # The old column can represent only one role. Keep group memberships intact.
    users.filter(groups__name="landlord").update(role="landlord")


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(assign_groups, restore_roles),
    ]
