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

default_type = ['4X6','4X5','4X4.5','DocTab','6X4']
certified_type = ['4X6','7X4','8X3','Booklet','EnvelopeSize10']
destconfirm_type = ['7X3','6X4','Dymo30384','Mailer7x5','EnvelopeSize10']



class shipping_usps(models.Model):
    _inherit = 'shipping.usps'
    
    @api.multi
    def write_passphrase(self, new_passphrase):
        ship_endicia_id = self.search([('active','=',True)])
        if not ship_endicia_id:
            ### This is required because when picking is created when saleorder is confirmed and if the default parameter has some error then it should not stop as the order is getting imported from external sites
            if error:
                raise osv.except_osv(_('Error'), _('Active Endicia settings not defined'))
            else:
                return False
        else:
            ship_endicia_id = ship_endicia_id[0]
        return ship_endicia_id.write({'passphrase':new_passphrase})
    
    @api.multi
    def get_endicia_info(self):
        ship_endicia_id = self.search([('active','=',True)])
        if not ship_endicia_id:
              raise osv.except_osv(_('Error'), _('Active Endicia settings not defined'))
        else:
            ship_endicia_id = ship_endicia_id[0]
        return ship_endicia_id
    
    
    @api.multi
    def get_usps_info(self):
        ship_usps_id = self.search([('active_usps','=',True)])
        if not ship_usps_id:
              raise osv.except_osv(_('Error'), _('Active USPS settings not defined'))
        else:
            ship_usps_id = ship_usps_id[0]
        return ship_usps_id
    
    name = fields.Char(string='Name', size=64, required=True, translate=True)
    requester_id = fields.Char(string='RequesterID', size=64, required=True)
    account_id = fields.Char(string='AccountID', size=64, required=True)
    passphrase = fields.Char(string='Passphrase', size=64, required=True)
    test = fields.Boolean(string='Is test?')
    active = fields.Boolean(string='Active', default=True)
    label_type = fields.Selection([
            ('Default','Default'),
            ('CertifiedMail','Certified Mail'),
            ('DestinationConfirm','Destination Confirm'),
            ('Domestic','Domestic'),
            ('International','International')
        ], string='Label Type',size=64, required=True)
    label_size = fields.Selection([
            ('4X6','4X6'),
            ('4X5','4X5'),
            ('4X4.5','4X4.5'),
            ('DocTab','DocTab'),
            ('6X4','6X4'),
            ('7X3','7X3'),
            ('7X4','7X4'),
            ('8X3','8X3'),
            ('Dymo30384','Dymo 30384'),
            ('Booklet','Booklet'),
            ('EnvelopeSize10','Envelope Size 10'),
            ('Mailer7x5','Mailer 7x5'),
        ], string='Label Size',required=True)
    image_format = fields.Selection([
            ('GIF','GIF'),
            ('JPEG','JPEG'),
            ('PDF','PDF'),
            ('PNG','PNG'),
        ], string='Image Format', required=True)
    image_rotation = fields.Selection([
            ('None','None'),
            ('Rotate90','Rotate 90'),
            ('Rotate180','Rotate 180'),
            ('Rotate270','Rotate 270'),
        ], string='Image Rotation',required=True)
    config_shipping_address_id = fields.Many2one('res.partner', "shipping Address")
            
            
            
shipping_usps()