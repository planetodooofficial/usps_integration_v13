# -*- encoding: utf-8 -*-
##############################################################################
#    Copyright (c) 2015 - Present Planet Odoo. All Rights Reserved
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

from odoo import models, fields


class delivery_carrier(models.Model):
    _inherit = "delivery.carrier"

    is_usps = fields.Boolean(string='Is USPS', help="If the field is set to True, it will consider it as USPS service type.")
    is_fedex = fields.Boolean(string='Is Fedex',
                             help="If the field is set to True, it will consider it as Fedex service type.")
    container_usps = fields.Char(string='Container')
    size_usps = fields.Char(string='Size')
    first_class_mail_type_usps = fields.Char(string='First Class Mail Type')
    partner_id = fields.Many2one('res.partner', string='Recipient', required=True)
