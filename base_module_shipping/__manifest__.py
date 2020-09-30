# -*- encoding: utf-8 -*-
##############################################################################
# Copyright (c) 2015 - Present Planet Odoo. All Rights Reserved
#    Author: [Planet Odoo]
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    A copy of the GNU General Public License is available at:
#    <http://www.gnu.org/licenses/gpl.html>.
#
##############################################################################


{
    'name': 'Shipping Service Integration',
    'version': '1.0',
    'category': 'Generic Modules/Warehouse Management',
    'description': """
     Odoo Integration with USPS, UPS and Fedex
    """,
    "website": "www.planet-odoo.com",
    'author': 'Planet-Odoo',
    'depends': ['sale', 'stock', 'delivery', 'product', 'sale_stock'],
    'css': [
        'static/src/css/rotate_label.css',
    ],
    "demo": [],
    "data": [
        "security/shipping_security.xml",
        "security/ir.model.access.csv",
        "wizard/generate_shipping_quotes.xml",
        "wizard/generate_label_pdf_view.xml",
        "view/batch_sequence.xml",
        "view/shipping_menu.xml",
        'view/sale_view.xml',
        'view/stock_view.xml',
        'view/delivery_view.xml',
        'view/product_view.xml',
        'view/shipping_data.xml',
        'wizard/refund_request_view.xml',
    ],
    'auto_install': False,
    'installable': True,
    'qweb': ['static/src/xml/generate_report.xml'],
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
