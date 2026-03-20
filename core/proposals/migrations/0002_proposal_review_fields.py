import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('proposals', '0001_initial'),
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='proposal',
            name='reviewed_by',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='reviewed_proposals',
                to='users.adminofficeprofile',
            ),
        ),
        migrations.AddField(
            model_name='proposal',
            name='review_comment',
            field=models.TextField(blank=True),
        ),
    ]
