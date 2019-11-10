# -*- coding: utf-8 -*-

import base64
import logging
import json
import urllib

from odoo import api, http, models, _

from odoo.addons.payment.models.payment_acquirer import ValidationError

_logger = logging.getLogger(__name__)


class AcquirerRedsys(models.Model):
    _inherit = 'payment.acquirer'

    def _prepare_merchant_parameters(self, tx_values):
        """
        Workaround para reemplazar los espacios en blanco en la referencia del pedido.
        Solo se añade esta linea: order = tx_values['reference'].replace(' ', '+')
        Redsys sustituye los espacios por simbolo + por eso hay que enviarselos con un mas tambien porque sino
        cuando hace el metodo sign_parameters no coincide.
        """
        # Check multi-website
        base_url = self._get_website_url()
        callback_url = self._get_website_callback_url()
        if self.redsys_percent_partial > 0:
            amount = tx_values['amount']
            tx_values['amount'] = amount - (
                amount * self.redsys_percent_partial / 100)

        # Workaround
        order = tx_values['reference'].replace(' ', '+')

        values = {
            'Ds_Sermepa_Url': (self._get_redsys_urls(self.environment)['redsys_form_url']),
            'Ds_Merchant_Amount': str(int(round(tx_values['amount'] * 100))),
            'Ds_Merchant_Currency': self.redsys_currency or '978',
            'Ds_Merchant_Order': (order and order[-12:] or False),
            'Ds_Merchant_MerchantCode': (self.redsys_merchant_code and self.redsys_merchant_code[:9]),
            'Ds_Merchant_Terminal': self.redsys_terminal or '1',
            'Ds_Merchant_TransactionType': (self.redsys_transaction_type or '0'),
            'Ds_Merchant_Titular': (self.redsys_merchant_titular[:60] and self.redsys_merchant_titular[:60]),
            'Ds_Merchant_MerchantName': (self.redsys_merchant_name and self.redsys_merchant_name[:25]),
            'Ds_Merchant_MerchantUrl': ('%s/payment/redsys/return' % (callback_url or base_url))[:250],
            'Ds_Merchant_MerchantData': self.redsys_merchant_data or '',
            'Ds_Merchant_ProductDescription': (
                self._product_description(tx_values['reference']) or
                self.redsys_merchant_description and
                self.redsys_merchant_description[:125]),
            'Ds_Merchant_ConsumerLanguage': (self.redsys_merchant_lang or '001'),
            'Ds_Merchant_UrlOk': '%s/payment/redsys/result/redsys_result_ok' % base_url,
            'Ds_Merchant_UrlKo': '%s/payment/redsys/result/redsys_result_ko' % base_url,
            'Ds_Merchant_Paymethods': self.redsys_pay_method or 'T',
        }

        return self._url_encode64(json.dumps(values))


class TxRedsys(models.Model):
    _inherit = 'payment.transaction'

    @api.model
    def _redsys_form_get_tx_from_data(self, data):
        """
        Workaround para quitar los simbolos + del pedido que se recibe de Redsys porque sino en el search
        no lo va a encontrar.
        Solo se modifica esta linea añadiendo el replace al search: reference.replace('+', ' ')
        """
        parameters = data.get('Ds_MerchantParameters', '')
        parameters_dic = json.loads(base64.b64decode(parameters).decode())
        reference = urllib.parse.unquote(parameters_dic.get('Ds_Order', ''))
        pay_id = parameters_dic.get('Ds_AuthorisationCode')
        shasign = data.get('Ds_Signature', '').replace('_', '/').replace('-', '+')
        test_env = http.request.session.get('test_enable', False)
        if not reference or not pay_id or not shasign:
            error_msg = 'Redsys: received data with missing reference' \
                        ' (%s) or pay_id (%s) or shashign (%s)' % (reference, pay_id, shasign)
            if not test_env:
                _logger.info(error_msg)
                raise ValidationError(error_msg)
            # For tests
            http.OpenERPSession.tx_error = True

        # Workaround
        tx = self.search([('reference', '=', reference.replace('+', ' '))])

        if not tx or len(tx) > 1:
            error_msg = 'Redsys: received data for reference %s' % (reference)
            if not tx:
                error_msg += '; no order found'
            else:
                error_msg += '; multiple order found'
            if not test_env:
                _logger.info(error_msg)
                raise ValidationError(error_msg)
            # For tests
            http.OpenERPSession.tx_error = True
        if tx and not test_env:
            # verify shasign
            shasign_check = tx.acquirer_id.sign_parameters(
                tx.acquirer_id.redsys_secret_key, parameters)
            if shasign_check != shasign:
                error_msg = (
                        'Redsys: invalid shasign, received %s, computed %s, '
                        'for data %s' % (shasign, shasign_check, data)
                )
                _logger.info(error_msg)
                raise ValidationError(error_msg)
        return tx
