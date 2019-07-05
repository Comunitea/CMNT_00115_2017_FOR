# -*- coding: utf-8 -*

##############################################################################
#
#    License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
#    © 2019 Comunitea - Ruben Seijas <ruben@comunitea.com>
#    © 2019 Comunitea - Pavel Smirnov <pavel@comunitea.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from odoo import api, models
from pprint import pprint


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.multi
    def _website_product_id_change(self, order_id, product_id, qty=0):
        """
        Sets customs fields in backend orders.
        escuadria, product_length and product_uom_unit as same as product_uom_qty field.

        """
        order = self.sudo().browse(order_id)
        product_context = dict(self.env.context)
        pprint(self.env.context)
        custom_length = self.env.context.get('custom_length', False)
        pprint(custom_length)
        product_context.setdefault('lang', order.partner_id.lang)
        product_context.update({
            'partner': order.partner_id.id,
            'quantity': qty,
            'date': order.date_order,
            'pricelist': order.pricelist_id.id,
        })
        product = self.env['product.product'].with_context(product_context).browse(product_id)
        pu = product.price
        if order.pricelist_id and order.partner_id:
            order_line = order._cart_find_product_line(product.id)
            if order_line:
                pu = self.env['account.tax']._fix_tax_included_price_company(pu, product.taxes_id,
                                                                             order_line[0].tax_id, self.company_id)

        # Dimensions depends product variants
        height, width, length = '0', '0', '0'
        if product.attribute_value_ids:
            pprint(product.attribute_value_ids)
            if len(product.attribute_value_ids) > 2:
                height = product.attribute_value_ids[0].name
                width = product.attribute_value_ids[1].name
                pprint(product.attribute_value_ids[2].name)
                if product.attribute_value_ids[2].name == 0:
                    length = product_context.get('custom_length', False)
                else:
                    length = product.attribute_value_ids[2].name
            elif len(product.attribute_value_ids) > 1:
                width = product.attribute_value_ids[0].name
                pprint(product.attribute_value_ids[1].name)
                if product.attribute_value_ids[1].name == 0:
                    length = product_context.get('custom_length', False)
                else:
                    length = product.attribute_value_ids[1].name
        
        pprint(length)

        return {
            'product_id': product_id,
            'product_uom_qty': qty,
            'order_id': order_id,
            'product_uom': product.uom_id.id,
            'price_unit': pu,
            # Set custom field
            'product_uom_unit': qty,
            # Set dimension
            'escuadria': height + 'x' + width,
            'product_length': length,
        }
