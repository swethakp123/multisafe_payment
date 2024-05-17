# Part of Odoo. See LICENSE file for full copyright and licensing details.


import logging
import pprint
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class MultiSafePayController(http.Controller):
    _return_url = '/payment/multisafepay/return'

    @http.route(
        _return_url, type='http', auth='public', csrf=False,
        save_session=False
    )
    def multisafepay_return_from_checkout(self, **data):

        t_id = data.get('transactionid')
        order = request.env['payment.transaction']._get_msp_order(t_id)
        data = order.get('data', '')
        _logger.info("Handling redirection from multisafepay with data:\n%s",
                     pprint.pformat(data))

        # Check the integrity of the notification.
        tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data('multisafepay', data)
        # Handle the notification data.
        tx_sudo._handle_notification_data('multisafepay', data)

        # Redirect the user to the status page.

        return request.redirect('/shop/confirmation')
