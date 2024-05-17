# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from odoo import fields, models
from multisafepay.client import Client

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    code = fields.Selection(
        selection_add=[('multisafepay', "Multisafepay")], ondelete={'multisafepay': 'set default'}
    )
    multisafepay_api_key = fields.Char(
        string="API KEY",
        required_if_provider='multisafepay',
    )

    def _aps_get_api_url(self, payload):
        if self.state == 'enabled':
            msp_client = Client()
            msp_client.set_modus('TEST')
            msp_client.set_api_key(self.multisafepay_api_key)
            order = msp_client.order.create(payload)
            url = order.get('data').get('payment_url')
            return url
