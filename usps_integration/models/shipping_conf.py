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


class shipping_usps(models.Model):
    _name = 'shipping.usps'

    name_usps = fields.Char(string='Name')
    user_id = fields.Char(string='UserID', required=True, translate=True)
    test_usps = fields.Boolean(string='Is test?')
    active_usps = fields.Boolean(string='Active', default=True)