# -*- encoding: utf-8 -*-
##############################################################################
#    Copyright (c) 2015 - Present Teckzilla Software Solutions Pvt. Ltd. All Rights Reserved
#    Author: [Teckzilla Software Solutions]  <[sales@teckzilla.net]>
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

from openerp import models, fields, api, _

class delivery_carrier(models.Model):
    _inherit = "delivery.carrier"
    
    container_usps = fields.Char(string='Container')
    size_usps = fields.Char(string='Size', size=100)
    first_class_mail_type_usps = fields.Char(string='First Class Mail Type')
    is_usps = fields.Boolean(string='Is USPS', help="If the field is set to True, it will consider it as USPS service type.")
    
delivery_carrier()    