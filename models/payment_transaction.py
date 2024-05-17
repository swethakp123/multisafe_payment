# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from werkzeug import urls

from odoo import _, models
from odoo.exceptions import ValidationError

from odoo.addons.payment import utils as payment_utils
from odoo.addons.multisafepay_payment_provider.controllers.main import MultiSafePayController
from multisafepay.client import Client

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_msp_order(self, t_id):
        msp_client = Client()
        msp_client.set_modus('TEST')
        msp_client.set_api_key('960cfc5b27f6005e73e73740e9095f0256e053ca')
        order = msp_client.order.get(t_id)
        return order

    def _get_specific_rendering_values(self, processing_values):
        super()._get_specific_rendering_values(processing_values)
        msp_client = Client()
        msp_client.set_modus('TEST')
        msp_client.set_api_key('960cfc5b27f6005e73e73740e9095f0256e053ca')
        converted_amount = payment_utils.to_minor_currency_units(self.amount,
                                                                 self.currency_id)

        base_url = self.provider_id.get_base_url()

        # Extract the payment link URL and embed it in the redirect form.
        rendering_values = {
            "type": msp_client.ordertype.REDIRECT,
            "order_id": self.reference,
            "currency": self.currency_id.name,
            "amount": converted_amount,
            "gateway": msp_client.paymentmethod.IDEAL,
            "description": "product description",
            "gateway_info": {
                "issuer_id": msp_client.issuer.ING
            },
            "payment_options": {
                "redirect_url": urls.url_join(base_url, MultiSafePayController._return_url),
                "close_window": False
            },
        }
        url = self.provider_id._aps_get_api_url(payload=rendering_values)
        msp_client.order.create(rendering_values)
        rendering_values.update({
            'api_url': url,
        })
        return rendering_values

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'multisafepay' or len(tx) == 1:
            return tx

        reference = notification_data.get('order_id')
        if not reference:
            raise ValidationError("Multisafepay: " + _("Received data with missing reference."))

        tx = self.search([('reference', '=', reference), ('provider_code', '=', 'multisafepay')])
        if not tx:
            raise ValidationError(
                "Multisafepay: " + _("No transaction found matching reference %s.", reference)
            )
        return tx

    def _get_tx_from_cancel_data(self, provider_code, reference):
        tx = super()._get_tx_from_notification_data(provider_code,
                                                    reference)
        if provider_code != 'multisafepay' or len(tx) == 1:
            return tx
        if not reference:
            raise ValidationError(
                "Multisafepay: " + _(
                    "Received data with missing reference %(ref)s.",
                    ref=reference)
            )
        tx = self.search([('reference', '=', reference),
                          ('provider_code', '=', 'multisafepay')])
        if not tx:
            raise ValidationError(
                "Multisafepay: " + _(
                    "No transaction found matching created on %s.", reference)
            )
        return tx

    def _process_notification_data(self, notification_data):
        super()._process_notification_data(notification_data)
        if self.provider_code != 'multisafepay':
            return

        status = notification_data.get('status')
        if not status:
            raise ValidationError("Multisafepay: " + _(
                "Received data with missing payment state."))
        if status == 'initialized':
            self._set_pending()
        elif status == 'completed':
            self._set_done()
        elif status in ['declined', 'cancelled']:
            self._set_pending()
        else:
            # Classify unsupported payment state as `error` tx state.
            status_description = notification_data.get('response_message')
            _logger.info(
                "Received data with invalid payment status (%(status)s) and reason '%(reason)s' "
                "for transaction with reference %(ref)s",
                {'status': status, 'reason': status_description,
                 'ref': self.reference},
            )
            self._set_error("Multisafepay: " + _(
                "Received invalid transaction status %(status)s and reason '%(reason)s'.",
                status=status, reason=status_description
            ))
