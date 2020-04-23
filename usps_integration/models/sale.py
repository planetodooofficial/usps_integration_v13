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
import openerp.addons.decimal_precision as dp
import urllib

class sale_order(models.Model):
    _inherit = "sale.order"
    
    def _get_shipping_type(self):
        res = super(sale_order, self)._get_shipping_type()
        res.append(('USPS','USPS'))
        return res
    
    shipping_type = fields.Selection(_get_shipping_type,'Shipping Type', default='All')
    
    def _get_service_type_usps(self):
        return [
            ('First Class', 'First Class'),
            ('First Class HFP Commercial', 'First Class HFP Commercial'),
            ('FirstClassMailInternational', 'First Class Mail International'),
            ('Priority', 'Priority'),
            ('Priority Commercial', 'Priority Commercial'),
            ('Priority HFP Commercial', 'Priority HFP Commercial'),
            ('PriorityMailInternational', 'Priority Mail International'),
            ('Express', 'Express'),
            ('Express Commercial', 'Express Commercial'),
            ('Express SH', 'Express SH'),
            ('Express SH Commercial', 'Express SH Commercial'),
            ('Express HFP', 'Express HFP'),
            ('Express HFP Commercial', 'Express HFP Commercial'),
            ('ExpressMailInternational', 'Express Mail International'),
            ('ParcelPost', 'Parcel Post'),
            ('ParcelSelect', 'Parcel Select'),
            ('StandardMail', 'Standard Mail'),
            ('CriticalMail', 'Critical Mail'),
            ('Media', 'Media'),
            ('Library', 'Library'),
            ('All', 'All'),
            ('Online', 'Online'),
        ]

    def _get_first_class_mail_type_usps(self):
        return [
            ('Letter', 'Letter'),
            ('Flat', 'Flat'),
            ('Parcel', 'Parcel'),
            ('Postcard', 'Postcard'),
        ]


    def _get_container_usps(self):
        return [
            ('Variable', 'Variable'),
            ('Card', 'Card'),
            ('Letter', 'Letter'),
            ('Flat', 'Flat'),
            ('Parcel', 'Parcel'),
            ('Large Parcel', 'Large Parcel'),
            ('Irregular Parcel', 'Irregular Parcel'),
            ('Oversized Parcel', 'Oversized Parcel'),
            ('Flat Rate Envelope', 'Flat Rate Envelope'),
            ('Padded Flat Rate Envelope', 'Padded Flat Rate Envelope'),
            ('Legal Flat Rate Envelope', 'Legal Flat Rate Envelope'),
            ('SM Flat Rate Envelope', 'SM Flat Rate Envelope'),
            ('Window Flat Rate Envelope', 'Window Flat Rate Envelope'),
            ('Gift Card Flat Rate Envelope', 'Gift Card Flat Rate Envelope'),
            ('Cardboard Flat Rate Envelope', 'Cardboard Flat Rate Envelope'),
            ('Flat Rate Box', 'Flat Rate Box'),
            ('SM Flat Rate Box', 'SM Flat Rate Box'),
            ('MD Flat Rate Box', 'MD Flat Rate Box'),
            ('LG Flat Rate Box', 'LG Flat Rate Box'),
            ('RegionalRateBoxA', 'RegionalRateBoxA'),
            ('RegionalRateBoxB', 'RegionalRateBoxB'),
            ('Rectangular', 'Rectangular'),
            ('Non-Rectangular', 'Non-Rectangular'),
         ]
         
    def _get_size_usps(self):
        return [
            ('REGULAR', 'Regular'),
            ('LARGE', 'Large'),
         ]
         
    service_type_usps = fields.Selection(_get_service_type_usps, string='Service Type', size=100, default= 'All')
    first_class_mail_type_usps = fields.Selection(_get_first_class_mail_type_usps, string='First Class Mail Type', size=50)
    container_usps = fields.Selection(_get_container_usps,'Container', size=100)
    size_usps = fields.Selection(_get_size_usps, string='Size', default='REGULAR')
    include_postage_usps = fields.Boolean(string='Include Postage', default= True)
    width_usps = fields.Float(string='Width', digits_compute= dp.get_precision('Stock Weight'))
    length_usps = fields.Float(string='Length', digits_compute= dp.get_precision('Stock Weight'))
    height_usps = fields.Float(string='Height', digits_compute= dp.get_precision('Stock Weight'))
    girth_usps = fields.Float(string='Girth', digits_compute= dp.get_precision('Stock Weight'))
    
sale_order()