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
        product_length = self.env.context.get('product_length', False)
        if product_length and product_length != '0':
            product_length_str = str(int(product_length))
            product_length = float(product_length)/1000
        else:
            product_length = False
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
                pu = self.env['account.tax'].with_context(product_context)._fix_tax_included_price_company(pu, product.taxes_id, 
                order_line[0].tax_id, self.company_id)

        # Dimensions depends product variants
        height, width, length = '0', '0', '0'
        if product.attribute_value_ids:
            if len(product.attribute_value_ids) > 2:
                height = product.attribute_value_ids[0].name
                width = product.attribute_value_ids[1].name
                if product.attribute_value_ids[2].name == 'Personalizado' and product_length:
                    length = product_length
                else:
                    length = product.attribute_value_ids[2].name
            elif len(product.attribute_value_ids) > 1:
                width = product.attribute_value_ids[0].name
                if product.attribute_value_ids[1].name == 'Personalizado' and product_length:
                    length = product_length
                else:
                    length = product.attribute_value_ids[1].name

        if product_length:
            return {
                'product_id': product_id,
                'order_id': order_id,
                'product_uom': product.uom_id.id,
                'price_unit': pu,
                # Set custom field
                'product_uom_unit': qty,
                # Set dimension
                'escuadria': height + 'x' + width + 'x' + product_length_str,
                'product_length': length,
            }
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

    @api.multi
    def _cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0, attributes=None, **kwargs):
        """ Add product_length """
        ctx = self.env.context.copy()
        length = self.env.context.get('product_length', False)
        product_uom_unit = False
        original_p_uom_unit = False
        if attributes:
            length = attributes.get('product_length', False)
            
        if line_id:
            line_obj = self.env['sale.order.line'].browse(line_id)
            length = line_obj.product_length * 1000 if line_obj.product_uom_unit != line_obj.product_uom_qty else False
            product_uom_unit = line_obj.product_uom_unit if length and add_qty == 0 and set_qty == 0 else False

        if length and length != '0':
                ctx['product_length'] = length
        if length and not line_id:
            possible_lines = self.order_line.search([('product_id', '=', product_id), ('product_length', '=', int(length)/1000)])
            original_p_uom_unit = possible_lines[0].product_uom_unit if possible_lines and possible_lines[0] else False        

        res = super(SaleOrder, self.with_context(ctx))._cart_update(product_id, line_id, add_qty, set_qty)
        add_qty = int(add_qty) or add_qty if add_qty else False
        if res and res['quantity'] != 0 and length and length != '0':
            line_obj_res = self.env['sale.order.line'].browse(res['line_id'])
            if add_qty != 0 and set_qty == 0 and add_qty != res['quantity']:
                line_obj_res.update({
                    'product_uom_unit': original_p_uom_unit + add_qty if original_p_uom_unit else add_qty
                })
            elif set_qty != 0 and line_obj_res.product_uom_unit == 0:
                line_obj_res.update({
                    'product_uom_unit': set_qty
                })
            elif product_uom_unit and product_uom_unit != res['quantity']:
                line_obj_res.update({
                    'product_uom_unit': product_uom_unit
                })
            line_obj_res._compute_product_uom_qty_cart(custom_length=True) 
        return res

    @api.multi
    def _get_line_description(self, order_id, product_id, attributes=None):

        res = super(SaleOrder, self)._get_line_description(order_id, product_id, attributes)

        product_context = dict(self.env.context)
        product_length = self.env.context.get('product_length', False)
        if product_length and product_length != '0':
            res = res.replace('0', str(product_length))
        return res

    def get_product_length(self, line_id):
        line_obj = self.env['sale.order.line'].browse(line_id)
        product_length = line_obj.product_length * 1000
        return product_length

    def check_custom_length(self, line_id):
        is_custom_length = False
        line_obj = self.env['sale.order.line'].browse(line_id)
        if line_obj.escuadria.count('x') == 2:
            is_custom_length = True
        
        return is_custom_length

    @api.multi
    @api.depends('website_order_line.product_uom_qty', 'website_order_line.product_id', 'website_order_line.product_uom_unit')
    def _compute_cart_info(self):
        for order in self:
            order.cart_quantity = int(sum(order.mapped('website_order_line.product_uom_unit')))
            order.only_services = all(l.product_id.type in ('service', 'digital') for l in order.website_order_line)

    @api.multi
    def _cart_find_product_line(self, product_id=None, line_id=None, **kwargs):
        self.ensure_one()
        
        lines = super(SaleOrder, self)._cart_find_product_line(product_id, line_id)

        product_length = self.env.context.get('product_length', False)
        if product_length and not line_id:
            lines = lines.search([('product_length', '=', int(product_length)/1000)])
        elif line_id and product_length:
            lines = lines.search([('id', '=', line_id)])
            
        return lines

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('product_uom_unit', 'escuadria', 'product_length')
    def _compute_product_uom_qty_cart(self, custom_length=False):

        if custom_length:
            for line in self:
                if not line.escuadria and not line.product_length:
                    line.product_uom_qty = line.product_uom_unit
                elif not line.escuadria and line.product_length:
                    line.product_uom_qty = line.product_uom_unit * \
                        line.product_length
                elif not line.product_length:
                    # Puede haber casos en los que se establezca escuadria pero no longitud
                    pass
                else:
                    if line.escuadria.find('x') != -1 or line.escuadria.find(
                            'X') != -1:
                        line.product_uom_qty = line.product_uom_unit * \
                            line.escuadria_float / 10000 * line.product_length
                    else:
                        line.product_uom_qty = line.product_uom_unit * \
                            line.escuadria_float / 100 * line.product_length
        else:
            super(SaleOrderLine, self)._compute_product_uom_qty()           