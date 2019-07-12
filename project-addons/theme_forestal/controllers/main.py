# -*- coding: utf-8 -*-
import json
import logging
from werkzeug.exceptions import Forbidden, NotFound

from odoo import http, tools, _
from odoo.http import request
from odoo.addons.base.ir.ir_qweb.fields import nl2br
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website.controllers.main import QueryURL
from odoo.exceptions import ValidationError
from odoo.addons.website.controllers.main import Website
from odoo.addons.website_form.controllers.main import WebsiteForm
from odoo.osv import expression
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.addons.website_sale_options.controllers.main import WebsiteSaleOptions
from pprint import pprint

_logger = logging.getLogger(__name__)

class WebsiteSaleExtended(WebsiteSale):

    def _filter_attributes(self, **kw):
        res = super(WebsiteSaleExtended, self)._filter_attributes(**kw)
        if kw and kw['product_length']:
            res['product_length'] = kw['product_length']
            
        return res

    @http.route(['/shop/cart/update_json'], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_update_json(self, product_id, line_id=None, add_qty=None, set_qty=None, display=True):
        order = request.website.sale_get_order(force_create=1)
        is_custom_length = order.check_custom_length(line_id)
        if is_custom_length:
            product_length = order.get_product_length(line_id)
            ctx = request.env.context.copy()
            ctx.update({'product_length': product_length})
            if order.state != 'draft':
                request.website.sale_reset()
                return {}
            value = order.with_context(ctx)._cart_update(product_id=product_id, line_id=line_id, add_qty=add_qty, set_qty=set_qty)

            if not order.cart_quantity:
                pprint("magia")
                request.website.sale_reset()
                return value

            order = request.website.sale_get_order()
            value['cart_quantity'] = order.cart_quantity
            from_currency = order.company_id.currency_id
            to_currency = order.pricelist_id.currency_id
            if not display:
                return value

            value['website_sale.cart_lines'] = request.env['ir.ui.view'].render_template("website_sale.cart_lines", {
                'website_sale_order': order,
                'compute_currency': lambda price: from_currency.compute(price, to_currency),
                'suggested_products': order._cart_accessories()
            })
            return value
        
        return super(WebsiteSaleExtended, self).cart_update_json(product_id, line_id, add_qty, set_qty, display)