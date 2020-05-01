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

from odoo import models, fields, api, _


class delivery_carrier(models.Model):
    _inherit = "delivery.carrier"

    service_code = fields.Char(string='Service Code', help="Code used as input to API")
    service_output = fields.Char(string='Service Output', help="Code returned as output by API")
    is_expedited = fields.Boolean(string='Is Expedited')
    partner_id = fields.Many2one('res.partner', string='Recipient', required=True)
    size_usps = fields.Selection([('REGULAR', 'Regular'), ('LARGE', 'Large')], string='Size')
    is_fedex = fields.Boolean('Is Fedex')
