from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('operasional', '0004_biayaoperasional_dibuat_pada'),
    ]

    operations = [
        migrations.AddField(
            model_name='biayaoperasional',
            name='foto_bukti',
            field=models.ImageField(blank=True, null=True, upload_to='biaya/'),
        ),
    ]
