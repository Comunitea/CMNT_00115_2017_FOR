# -*- coding: utf-8 -*-
#
# © 2018 Comunitea
# Pavel Smirnov <pavel@comunitea.com>
# Rubén Seijas <ruben@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
#
##############################################################################
#
#    Copyright (C) {year} {company} All Rights Reserved
#    ${developer} <{mail}>$
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



{
    'name': 'Theme Forestal',
    'version': '1.0',
    'summary': 'FrontEnd customization for Forestal Website',
    'description': '',
    'category': 'Theme',
    'author': 'Comunitea',
    'website': 'http://www.comunitea.com',
    'license': 'AGPL-3',
    'contributors': [
        'Pavel Smirnov <pavel@comunitea.com>',
        'Rubén Seijas <ruben@comunitea.com>',
    ],
    'depends': [
        'website_base_forestal',
        'website_sale',
        'website_sale_options',
        'sale_volume',
        'website_sale_product_brand',
    ],
    'data': [
        'templates/pages.xml',
        'data/page_data.xml',
        'data/menu_data.xml',
        'data/shop_data.xml',
        'templates/head.xml',
        'templates/footer.xml',
        'templates/header.xml',
        'templates/breadcrumbs_bar.xml',
        'templates/404.xml',
        'templates/product.xml',
        'templates/cart.xml',
        'templates/page_home.xml',
        'templates/page_who_we_are.xml',
        'templates/page_our_advantages.xml',
        'templates/page_products.xml',
    ],
    'images': [
        '/static/description/icon.png',
    ],
    'qweb': [
    ],
    'installable': True,
    'application': False,
}

