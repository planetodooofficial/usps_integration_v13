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


import base64
import binascii
import logging
import os
from io import StringIO

from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.platypus import Image

from custom.usps_integration_v13.base_module_shipping.models.miscellaneous import Address
from odoo import models, fields
from odoo.osv import osv
from odoo.tools.translate import _
from . import endicia
from .endicia import Package

logger = logging.getLogger('stock')


class stock_picking(models.Model):
    _inherit = "stock.picking"

    def get_endicia_info(self):
        shipping_usps_obj = self.env['shipping.usps']
        ship_endicia_id = shipping_usps_obj.search([('active', '=', True)])
        if not ship_endicia_id:
            raise osv.except_osv(_('Error'), _('Active Endicia settings not defined'))
        else:
            ship_endicia_id = ship_endicia_id[0]
        return ship_endicia_id

    def get_usps_info(self):
        shipping_usps_obj = self.env['shipping.usps']
        ship_usps_id = shipping_usps_obj.search([('active_usps', '=', True)])
        if not ship_usps_id:
            raise osv.except_osv(_('Error'), _('Active USPS settings not defined'))
        else:
            ship_usps_id = ship_usps_id[0]
        return ship_usps_id

    shipping_type = fields.Selection([('Fedex', 'Fedex'), ('UPS', 'UPS'), ('USPS', 'USPS'), ('All', 'All')],
                                     string='Shipping Type')

    def create_shipping_quotes(self, response, weight, cust_default, sys_default):
        shipping_res_obj = self.env['shipping.response']

        for resp in response['info']:
            sr_no = 1 if cust_default and cust_default.split('/')[0] == 'USPS' and \
                         cust_default.split('/')[1].split(' ')[0] in resp['service'] else 9
            sr_no = 2 if sr_no == 9 and sys_default and sys_default.split('/')[0] == 'USPS' and \
                         sys_default.split('/')[1].split(' ')[0] in resp['service'] else sr_no
            vals = {
                'name': resp['service'],
                'type': 'USPS',
                'rate': resp['cost'],
                'weight': weight,
                'usps_type': resp['package'],
                'sys_default': False,
                'cust_default': False,
                'sr_no': sr_no,
                'picking_id': self[0].id
            }
            res_id = shipping_res_obj.create(vals)
        return True

    def get_endicia_rates(self, weight, shipper, recipient, cust_default=False, sys_default=False, error=True):
        if 'usps_endicia_active' in self._context.keys() and self._context['usps_endicia_active'] == False:
            return False

        ship_endicia = self.env['shipping.usps'].get_endicia_info()
        credentials = {'partner_id': ship_endicia.requester_id, 'account_id': ship_endicia.account_id,
                       'passphrase': ship_endicia.passphrase}

        service_type = sys_default.split('/')[1]
        container = sys_default.split('/')[2]

        packages = [
            Package(service_type, round(weight * 16, 1), 0, 0, 0, value=1000, require_signature=3, reference='a12302b')]

        en = endicia.Endicia(credentials, ship_endicia.test)
        response = en.rate(packages, Package.shapes[container], shipper, recipient)
        logger.info('endicia response:   %s', response)
        if response['status'] == 0:
            return response

    def generate_usps_endicia_shipping(self, weight, shipper, recipient, cust_default=False, sys_default=False,
                                       error=True, context=None):
        response = self.get_endicia_rates(weight, shipper, recipient, cust_default, sys_default, error, context)
        logger.info('endicia response:   %s', response)
        if response['status'] == 0:
            return self.create_shipping_quotes(response, weight, cust_default, sys_default, context)

    # @api.multi
    def generate_shipping(self):
        #        sys_default = 'USPS/First Class/Letter/Reqular'
        context = self._context.copy()
        if context is None:
            context = {}
        context['usps_active'] = False
        context['ups_active'] = False
        super(stock_picking, self).generate_shipping()
        ship_usps = self.env['shipping.usps'].search([('active', '=', True)])

        for id in self:
            #            try:
            stockpicking = self
            shipping_type = stockpicking.shipping_type

            if shipping_type == 'USPS' or shipping_type == 'All':
                weight = stockpicking.weight_package if stockpicking.weight_package else stockpicking.weight_net

                if not weight:
                    raise Exception('Package Weight Invalid!')

                # cust_address = lines.sale_id.shop_id.cust_address
                cust_address = ship_usps.config_shipping_address_id
                if not cust_address:
                    raise Exception('Shop Address not defined!')

                shipper = Address(cust_address.name, cust_address.street, cust_address.city,
                                  cust_address.state_id.code or '', cust_address.zip, cust_address.country_id.code,
                                  cust_address.street2 or '', cust_address.phone or '', cust_address.email,
                                  cust_address.name)

                # Recipient
                cust_address = self.sale_id.partner_id
                receipient = Address(cust_address.name or '', cust_address.street and cust_address.street.rstrip(','),
                                     cust_address.city and cust_address.city.rstrip(','),
                                     cust_address.state_id.code or '', cust_address.zip, cust_address.country_id.code,
                                     cust_address.street2 and (
                                             cust_address.street != cust_address.street2) and cust_address.street2.rstrip(
                                         ',') or '', cust_address.phone or '', cust_address.email,
                                     (cust_address.name != cust_address.name) and cust_address.name or '')
                lines = self.env['sale.order'].browse(self.sale_id.id)
                heaviest_product_id = self._get_heaviest_product([id], lines)
                sys_default = self._get_sys_default_shipping(lines.sale_id, heaviest_product_id, weight)
                self.context['sys_default'] = sys_default
                cust_default = self._get_cust_default_shipping(stockpicking.carrier_id.id)
                self.context['cust_default'] = cust_default
                shipping_res = self.generate_usps_endicia_shipping([id], weight, shipper, receipient,
                                                                   self._context.get('cust_default', False),
                                                                   self._context.get('sys_default', False),
                                                                   self._context.get('error', False), self._context)
                logger.info('endicia shipping_res:  %s', shipping_res)
        return True


class shipping_response(models.Model):
    _inherit = 'shipping.response'

    def generate_usps_tracking_no(self, picking, error=False):
        """
        This function is used to Generated USPS Shipping Label in Delivery order
        parameters:
            picking : (int) stock picking ID,(delivery order ID)
        """
        sale_id = self.env['sale.order'].search([('name', '=', picking.origin)])
        context = dict(self._context or {})
        if not self.env['shipping.usps'].search([('active', '=', True)]):
            raise osv.except_osv(_('Error'), _('Default Endicia settings not defined'))
        ship_endicia = self.env['shipping.usps'].search([('active', '=', True)])
        context['usps_active'] = False
        # Endicia Quotes Selected
        stockpicking_obj = self.env['stock.picking']
        if picking.service_type_usps.find('First') != -1:
            mail_class = 'First'
        elif picking.service_type_usps.find('Express') != -1:
            mail_class = 'Express'
        else:
            mail_class = picking.service_type_usps

        cust_address = ship_endicia.config_shipping_address_id
        shipper = Address(cust_address.name or '', cust_address.street, cust_address.street2 or '', cust_address.city,
                          cust_address.state_id.code or '', cust_address.zip, cust_address.country_id.code,
                          cust_address.phone or '', cust_address.email,
                          (cust_address.name != cust_address.name) and cust_address.name or '')
        cust_address = picking.partner_id
        receipient = Address(cust_address.name or '', cust_address.street and cust_address.street.rstrip(','),
                             cust_address.street2 and (
                                     cust_address.street != cust_address.street2) and cust_address.street2.rstrip(
                                 ',') or '', cust_address.city and cust_address.city.rstrip(','),
                             cust_address.state_id.code or '', cust_address.zip, cust_address.country_id.code,
                             cust_address.phone or '', cust_address.email,
                             (cust_address.name != cust_address.name) and cust_address.name or '')
        international_label = False
        if receipient.country_code.lower() != 'us' and receipient.country_code.lower() != 'usa' and receipient.country_code.lower() != 'pr':
            international_label = True
            if picking.service_type_usps.find('First') != -1:
                mail_class = 'FirstClassMailInternational'
            elif picking.service_type_usps.find('Express') != -1:
                mail_class = 'ExpressMailInternational'
            elif picking.service_type_usps.find('Priority') != -1:
                mail_class = 'PriorityMailInternational'
        package = endicia.Package(mail_class,
                                  int(round(picking.weight_package * 10 >= 1.0 and picking.weight_package * 10 or 1.0)),
                                  endicia.Package.shapes[picking.container_usps], picking.length_package,
                                  picking.width_package, picking.height_package, picking.name, sale_id.amount_total)
        customs = []
        if international_label:
            for move_line in picking.move_lines:
                weight_net = move_line.product_id.product_tmpl_id.weight_net * 16 >= 1.0 and move_line.product_id.product_tmpl_id.weight_net * 16 * move_line.product_qty or 1.0
                customs.append(endicia.Customs(move_line.product_id.default_code + '-' + move_line.product_id.name,
                                               int(move_line.product_qty), int(round(weight_net)),
                                               move_line.price_unit > 0.00 and move_line.price_unit or 39.00,
                                               shipper.country_code))

        reference = ''
        reference2 = ''
        for move_line in picking.move_lines:
            reference += ' (' + str(int(move_line.product_qty)) + ')'
            if move_line.product_id.default_code:
                reference += str(move_line.product_id.default_code) + '+'

        reference = reference[:-1]
        reference = reference[20:]
        reference2 += ' ' + ship_endicia.config_shipping_address_id.name

        #        try:

        include_postage = picking.include_postage_usps
        if picking.service_type_usps.find('International') != -1 or picking.container_usps == 'Letter' != -1:
            image_rotation = 'Rotate90'
        else:
            image_rotation = ship_endicia.image_rotation

        request = endicia.LabelRequest(ship_endicia.requester_id, ship_endicia.account_id, ship_endicia.passphrase,
                                       ship_endicia.label_type if not international_label else 'International',
                                       ship_endicia.label_size, ship_endicia.image_format, image_rotation, package,
                                       shipper, receipient, reference, reference2, include_postage,
                                       debug=ship_endicia.test,
                                       destination_confirm=True if picking.service_type_usps == 'First Class' and picking.container_usps == 'Letter' else False,
                                       customs_info=customs)
        response = request.send()
        if isinstance(response, str):
            log_data = picking.write({'error_for_faulty': str(response), 'is_faulty_deliv_order': True})
            return True
        endicia_res = response._get_value()
        im_barcode = StringIO.StringIO(endicia_res['label'])  # constructs a StringIO holding the image
        img_barcode = Image.open(im_barcode)
        output = StringIO.StringIO()
        img_barcode.save(output, format='PNG')
        data = binascii.b2a_base64(output.getvalue())
        f = open('/tmp/test.png', 'wb')
        f.write(output.getvalue())
        f.close()
        c = canvas.Canvas("/tmp/picking_list.pdf")
        c.setPageSize((400, 650))
        c.drawImage('/tmp/test.png', 10, 10, 380, 630)
        c.save()
        f = open('/tmp/picking_list.pdf', 'rb')

        attachment_pool = self.env['ir.attachment']
        data_attach = {
            'name': 'PackingList_USPS.pdf',
            'datas_fname': 'PackingList_USPS.pdf',
            'datas': base64.b64encode(f.read()),
            'description': 'Packing List',
            'res_name': picking.name,
            'res_model': 'stock.picking',
            'res_id': picking.id,
        }
        attach_id = attachment_pool.search([('res_id', '=', picking.id), ('res_name', '=', picking.name)])
        if not attach_id:
            attach_id = attachment_pool.create(data_attach)
            os.remove('/tmp/test.png')
            os.remove('/tmp/picking_list.pdf')
        else:
            attach_result = attachment_pool.write(attach_id, data_attach)
            attach_id = attach_id[0]
        context['attach_id'] = attach_id

        if endicia_res['tracking']:
            carrier_id = self.env['delivery.carrier'].search(
                [('service_code', '=', picking.service_type_usps), ('container_usps', '=', picking.container_usps)])
            if len(carrier_id):
                carrier_id = carrier_id[0]
                cost = endicia_res['cost']
            else:
                carrier_id = False
                cost = False
            vals = {
                'carrier_tracking_ref': endicia_res['tracking'],
                'carrier_id': carrier_id.id,
                'shipping_rate': cost
            }
            picking.write(vals)
            context['track_success'] = True
            context['tracking_no'] = endicia_res['tracking']
        return True
