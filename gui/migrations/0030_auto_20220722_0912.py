# Generated by Django 3.2.7 on 2022-07-21 05:57

from django.db import migrations, models
from requests import get
from lndg.settings import LND_NETWORK

def update_close_fees(apps, schedma_editor):
    channels = apps.get_model('gui', 'channels')
    closures = apps.get_model('gui', 'closures')
    resolutions = apps.get_model('gui', 'resolutions')
    settings = apps.get_model('gui', 'localsettings')
    def network_links():
        if settings.objects.filter(key='GUI-NetLinks').exists():
            network_links = str(settings.objects.filter(key='GUI-NetLinks')[0].value)
        else:
            network_links = 'https://mempool.space'
        return network_links
    def get_tx_fees(txid):
        base_url = network_links() + ('/testnet' if LND_NETWORK == 'testnet' else '') + '/api/tx/'
        try:
            request_data = get(base_url + txid).json()
            fee = request_data['fee']
        except Exception as e:
            print('Error getting closure fees for', txid, '-', str(e))
            fee = 0
        return fee
    try:
        for closure in closures.objects.exclude(open_initiator=2, close_type=0):
            if channels.objects.filter(chan_id=closure.chan_id).exists():
                channel = channels.objects.filter(chan_id=closure.chan_id)[0]
                closing_costs = get_tx_fees(closure.closing_tx) if closure.open_initiator == 1 else 0
                for resolution in resolutions.objects.filter(chan_id=closure.chan_id).exclude(resolution_type=2):
                    closing_costs += get_tx_fees(resolution.sweep_txid)
                channel.closing_costs = closing_costs
                channel.save()
    except Exception as e:
        print('Migration step failed:', str(e))

def revert_close_fees(apps, schedma_editor):
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('gui', '0029_update_percent_vars'),
    ]

    operations = [
        migrations.AddField(
            model_name='channels',
            name='closing_costs',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='rebalancer',
            name='fees_paid',
            field=models.FloatField(default=None, null=True),
        ),
        migrations.AlterField(
            model_name='channels',
            name='ar_in_target',
            field=models.IntegerField(),
        ),
        migrations.AlterField(
            model_name='channels',
            name='auto_fees',
            field=models.BooleanField(),
        ),
        migrations.RunPython(update_close_fees, revert_close_fees),
    ]
