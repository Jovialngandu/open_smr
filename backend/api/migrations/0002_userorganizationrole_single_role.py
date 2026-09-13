from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [('api', '0001_initial')]

    operations = [
        migrations.AlterUniqueTogether(
            name='userorganizationrole',
            unique_together={('user', 'organization')},
        ),
    ]
