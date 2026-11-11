
from datetime import timedelta
import orders.models
from django.db import migrations, models
from django.utils import timezone


def set_existing_orders_expiry(apps, schema_editor):
    Order = apps.get_model('orders', 'Order')
    now = timezone.now()

    for order in Order.objects.all().iterator():
        order.expires_at = order.created + timedelta(minutes=30)

        if order.status == 'pending' and order.expires_at <= now:
            order.status = 'expired'

        order.save(update_fields=['expires_at', 'status'])


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0005_alter_order_id_alter_orderitem_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='expires_at',
            field=models.DateTimeField(
                null=True,
                blank=True,
                db_index=True,
                verbose_name='زمان انقضای سفارش'
            ),
        ),

        migrations.RunPython(
            set_existing_orders_expiry,
            migrations.RunPython.noop,
        ),

        migrations.AlterField(
            model_name='order',
            name='expires_at',
            field=models.DateTimeField(
                default=orders.models.order_expiry_time,
                db_index=True,
                verbose_name='زمان انقضای سفارش'
            ),
        ),

        migrations.AddField(
            model_name='order',
            name='payment_authority',
            field=models.CharField(
                blank=True,
                default='',
                max_length=100,
                verbose_name='شناسه پرداخت'
            ),
        ),

        migrations.AddField(
            model_name='order',
            name='payment_ref_id',
            field=models.CharField(
                blank=True,
                default='',
                max_length=100,
                verbose_name='شماره پیگیری پرداخت'
            ),
        ),

        migrations.AlterField(
            model_name='order',
            name='id',
            field=models.BigAutoField(
                auto_created=True,
                primary_key=True,
                serialize=False,
                verbose_name='ID'
            ),
        ),

        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(
                choices=[
                    ('pending', 'در انتظار پرداخت'),
                    ('paid', 'پرداخت شده'),
                    ('processing', 'در حال آماده‌سازی'),
                    ('shipped', 'ارسال شده'),
                    ('delivered', 'تحویل شده'),
                    ('cancelled', 'لغو شده'),
                    ('expired', 'منقضی شده'),
                ],
                default='pending',
                max_length=20
            ),
        ),

        migrations.AlterField(
            model_name='orderitem',
            name='id',
            field=models.BigAutoField(
                auto_created=True,
                primary_key=True,
                serialize=False,
                verbose_name='ID'
            ),
        ),
    ]
