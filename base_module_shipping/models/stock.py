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

import binascii
import logging
from base64 import b64decode

import odoo.addons.decimal_precision as dp
from .miscellaneous import Address

from odoo import models, fields, api
from odoo.osv import osv
from odoo.tools.translate import _
from . import shippingservice

logging.basicConfig(level=logging.INFO)
logging.getLogger('suds.client').setLevel(logging.DEBUG)
logger = logging.getLogger('stock')


def get_partner_details(firm_name, partneradd_lnk, context=None):
    result = {}
    if partneradd_lnk:
        result['name'] = partneradd_lnk.name
        result['firm'] = firm_name or partneradd_lnk.name
        result['add1'] = partneradd_lnk.street or ''
        result['add2'] = partneradd_lnk.street2 or ''
        result['city'] = partneradd_lnk.city or ''
        result['state_code'] = partneradd_lnk.state_id.code or ''
        result['zip5'] = ''
        result['zip4'] = ''
        if len(partneradd_lnk.zip.strip()) == 5:
            result['zip5'] = partneradd_lnk.zip
            result['zip4'] = ''
        elif len(partneradd_lnk.zip.strip()) == 4:
            result['zip4'] = partneradd_lnk.zip
            result['zip5'] = ''
        elif str(partneradd_lnk.zip).find('-'):
            zips = str(partneradd_lnk.zip).split('-')
            if len(zips[0]) == 5 and len(zips[1]) == 4:
                result['zip5'] = zips[0]
                result['zip4'] = zips[1]
            elif len(zips[0]) == 4 and len(zips[1]) == 5:
                result['zip4'] = zips[0]
                result['zip5'] = zips[1]
        else:
            result['zip4'] = result['zip5'] = ''

        result['email'] = partneradd_lnk.email or ''
        result['country_code'] = partneradd_lnk.country_id.code or ''
        result['phone'] = partneradd_lnk.phone or ''
    return result


class shipping_response(models.Model):
    _name = 'shipping.response'

    def generate_tracking_no(self, cr, uid, ids, context={}, error=False):
        stockpicking_obj = self.pool.get('stock.picking')
        #        try:
        saleorder_obj = self.pool.get('sale.order')
        shippingresp_lnk = self.browse(cr, uid, ids[0])
        picking_data = shippingresp_lnk.picking_id
        if shippingresp_lnk.type.lower() == 'usps' and not ('usps_active' in context.keys()):
            result = self.generate_usps_tracking_no(cr, uid, shippingresp_lnk.picking_id, context)
            carrier_ids = self.pool.get('delivery.carrier').search(cr, uid, [
                ('service_output', '=', picking_data.service_type_usps), ('is_usps', '=', True),
                ('container_usps', '=', picking_data.container_usps), ('size_usps', '=', picking_data.size_usps)])
        elif shippingresp_lnk.type.lower() == 'fedex':
            result = self.generate_fedex_tracking_no(cr, uid, shippingresp_lnk.picking_id, context)
            carrier_ids = self.pool.get('delivery.carrier').search(cr, uid, [
                ('service_output', '=', picking_data.service_type_fedex), ('is_fedex', '=', True)])
        elif shippingresp_lnk.type.lower() == 'ups':
            result = self.generate_ups_tracking_no(cr, uid, shippingresp_lnk.picking_id, context)
            carrier_ids = self.pool.get('delivery.carrier').search(cr, uid, [
                ('service_output', '=', picking_data.service_type_ups), ('is_ups', '=', True)])
        if context.get('track_success', False):
            if not carrier_ids:
                raise osv.except_osv(_('Error'), _('Shipping service output settings not defined'))
            self.pool.get('stock.picking').write(cr, uid, picking_data.id, {'carrier_id': carrier_ids[0]})
            saleorder_obj.write(cr, uid, picking_data.sale_id.id,
                                {'client_order_ref': context['tracking_no'], 'carrier_id': carrier_ids[0]})

            ### Write this shipping respnse is selected
            self.write(cr, uid, ids[0], {'selected': True})
            self.pool.get('stock.picking').do_transfer(cr, uid, [picking_data.id], context=context)
            return True
        else:
            return False

    _order = 'sr_no'

    name = fields.Char(string='Service Type', size=100, readonly=True)
    type = fields.Char(string='Shipping Type', size=64, readonly=True)
    usps_type = fields.Char(string='USPS Type', size=64)
    rate = fields.Char(string='Rate', size=64, readonly=True)
    weight = fields.Float(string='Weight')
    cust_default = fields.Boolean(string='Customer Default')
    sys_default = fields.Boolean(string='System Default')
    sr_no = fields.Integer(string='Sr. No', default=9)
    selected = fields.Boolean(string='Selected', default=False)
    picking_id = fields.Many2one('stock.picking', string='Picking')

def _get_container_usps():
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


def _get_service_type_ups():
    return [
        ('01', 'Next Day Air'),
        ('02', 'Second Day Air'),
        ('03', 'Ground'),
        ('07', 'Worldwide Express'),
        ('08', 'Worldwide Expedited'),
        ('11', 'Standard'),
        ('12', 'Three-Day Select'),
        ('13', 'Next Day Air Saver'),
        ('14', 'Next Day Air Early AM'),
        ('54', 'Worldwide Express Plus'),
        ('59', 'Second Day Air AM'),
        ('65', 'Saver'),
        ('86', 'Express Saver'),
    ]


def get_ups_servicetype_name(code, mag_code=False):
    if code:
        if code == '01':
            return 'Next Day Air'
        elif code == '02':
            return 'Second Day Air'
        elif code == '03':
            return 'Ground'
        elif code == '07':
            return 'Worldwide Express'
        elif code == '08':
            return 'Worldwide Expedited'
        elif code == '11':
            return 'Standard'
        elif code == '12':
            return 'Three-Day Select'
        elif code == '13':
            return 'Next Day Air Saver'
        elif code == '14':
            return 'Next Day Air Early AM'
        elif code == '54':
            return 'Worldwide Express Plus'
        elif code == '59':
            return 'Second Day Air AM'
        elif code == '65':
            return 'Saver'
        else:
            return False
    elif mag_code:
        if mag_code == 'ups_3DS':
            return 'Three-Day Select'
        elif mag_code == 'ups_GND':
            return 'Ground'
        elif mag_code == 'ups_2DA':
            return 'Second Day Air'
        elif mag_code == 'ups_1DP':
            return 'Next Day Air Saver'
        elif mag_code == 'ups_1DA':
            return 'Next Day Air'
        elif mag_code == 'ups_1DM':
            return 'Next Day Air Early AM'
    else:
        return False


class stock_picking(models.Model):
    _inherit = "stock.picking"

    def do_print_picking(self, cr, uid, ids, context=None):
        '''This function prints the picking list'''
        context = dict(context or {}, active_ids=ids)
        return self.pool.get("report").get_action(cr, uid, ids, 'shipping_teckzilla.shipping_report_picking',
                                                  context=context)

    def action_assign_new(self, cr, uid, ids, *args):
        """ Changes state of picking to available if all moves are confirmed.
        @return: True
        """
        for pick in self.browse(cr, uid, ids):
            move_ids = [x.id for x in pick.move_lines if x.state == 'confirmed']
            if not move_ids:
                return False
            self.pool.get('stock.move').action_assign(cr, uid, move_ids)
        return True

    #    product_id = fields.related('move_lines', 'product_id', type='many2one', relation="product.product" ,string='Product name')
    #    product_id = fields.Many2one(string='Product name', related='product_id.move_lines')
    #    product_qty = fields.related('move_lines', 'product_qty', type='char', string='Qty')
    #    product_qty = fields.Char(string='Qty', related='move_lines.product_qty')
    shipping_type = fields.Selection([('All', 'All')], 'Shipping Type', default='All')
    use_shipping = fields.Boolean(string='Use Shipping', default=True)
    is_residential = fields.Boolean(string='Residential')
    weight_package = fields.Float(string='Package Weight', digits=dp.get_precision('Stock Weight'),
                                  help="Package weight which comes from weighinig machine in pounds")
    length_package = fields.Float(string='Package Length')
    width_package = fields.Float(string='Package Width')
    height_package = fields.Float(string='Package Height')
    units_package = fields.Char(string='Package Units', size=64, default='IN')
    service_type_usps = fields.Selection([
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
    ], string='Service Type', size=100)

    first_class_mail_type_usps = fields.Selection([
        ('Letter', 'Letter'),
        ('Flat', 'Flat'),
        ('Parcel', 'Parcel'),
        ('Postcard', 'Postcard'),
    ], string='First Class Mail Type',size=50)
    size_usps = fields.Selection([('REGULAR', 'Regular'),('LARGE', 'Large')], string='Size')
    width_usps = fields.Float(string='Width', digits=dp.get_precision('Stock Weight'))
    length_usps = fields.Float(string='Length', digits=dp.get_precision('Stock Weight'))
    height_usps = fields.Float(string='Height', digits=dp.get_precision('Stock Weight'))
    girth_usps = fields.Float(string='Girth', digits=dp.get_precision('Stock Weight'))
    include_postage_usps = fields.Boolean(string='Include Postage')
    dropoff_type_fedex = fields.Selection([
        ('REGULAR_PICKUP', 'REGULAR PICKUP'),
        ('REQUEST_COURIER', 'REQUEST COURIER'),
        ('DROP_BOX', 'DROP BOX'),
        ('BUSINESS_SERVICE_CENTER', 'BUSINESS SERVICE CENTER'),
        ('STATION', 'STATION'),
    ], string='Dropoff Type')
    service_type_fedex = fields.Selection([
        ('EUROPE_FIRST_INTERNATIONAL_PRIORITY', 'EUROPE_FIRST_INTERNATIONAL_PRIORITY'),
        ('FEDEX_1_DAY_FREIGHT', 'FEDEX_1_DAY_FREIGHT'),
        ('FEDEX_2_DAY', 'FEDEX_2_DAY'),
        ('FEDEX_2_DAY_FREIGHT', 'FEDEX_2_DAY_FREIGHT'),
        ('FEDEX_3_DAY_FREIGHT', 'FEDEX_3_DAY_FREIGHT'),
        ('FEDEX_EXPRESS_SAVER', 'FEDEX_EXPRESS_SAVER'),
        ('STANDARD_OVERNIGHT', 'STANDARD_OVERNIGHT'),
        ('PRIORITY_OVERNIGHT', 'PRIORITY_OVERNIGHT'),
        ('FEDEX_GROUND', 'FEDEX_GROUND'),
    ], string='Service Type', size=100)
    packaging_type_fedex = fields.Selection([
        ('FEDEX_BOX', 'FEDEX BOX'),
        ('FEDEX_PAK', 'FEDEX PAK'),
        ('FEDEX_TUBE', 'FEDEX_TUBE'),
        ('YOUR_PACKAGING', 'YOUR_PACKAGING')
    ], string='Packaging Type', help="What kind of package this will be shipped in")
    package_detail_fedex = fields.Selection([
        ('INDIVIDUAL_PACKAGES', 'INDIVIDUAL_PACKAGES'),
        ('PACKAGE_GROUPS', 'PACKAGE_GROUPS'),
        ('PACKAGE_SUMMARY', 'PACKAGE_SUMMARY'),
    ], string='Package Detail')
    payment_type_fedex = fields.Selection([
        ('RECIPIENT', 'RECIPIENT'),
        ('SENDER', 'SENDER'),
        ('THIRD_PARTY', 'THIRD_PARTY'),
    ], string='Payment Type', help="Who pays for the rate_request?")
    physical_packaging_fedex = fields.Selection([
        ('BAG', 'BAG'),
        ('BARREL', 'BARREL'),
        ('BOX', 'BOX'),
        ('BUCKET', 'BUCKET'),
        ('BUNDLE', 'BUNDLE'),
        ('CARTON', 'CARTON'),
        ('TANK', 'TANK'),
        ('TUBE', 'TUBE'),
    ], string='Physical Packaging')
    shipping_label = fields.Binary(string='Logo')
    shipping_rate = fields.Float(string='Shipping Rate')
    response_usps_ids = fields.One2many('shipping.response', 'picking_id', string='Shipping Response')
    batch_no = fields.Char('Batch No', size=64)
    is_faulty = fields.Boolean(string='Is faulty')
    is_international = fields.Boolean(string='Is International')
    is_expedited = fields.Boolean(string='Is Expedited')
    is_one_day_expedited = fields.Boolean(string='Is One Day Expedited')
    is_two_day_expedited = fields.Boolean(string='Is Two Day Expedited')
    sku = fields.Char(string='sku', size=64)
    error_for_faulty = fields.Text('Error Log Faulty Order')
    label_printed = fields.Boolean('Label Printed')
    label_printed_datetime = fields.Date('Label Printed on Date')
    label_generated = fields.Boolean('Label Generated')
    is_faulty_deliv_order = fields.Boolean('Faulty Delivery Order')
    container_usps = fields.Selection([
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
    ], string='Container', size=100)
    number_of_packages = fields.Integer(string='Number of Packages', copy=False)
    company_id = fields.Many2one('res.company', string='Company', store=True, readonly=False)

    def generate_fedex_shipping(self, id, dropoff_type_fedex, service_type_fedex, packaging_type_fedex,
                                package_detail_fedex, payment_type_fedex, physical_packaging_fedex, weight,
                                shipper_postal_code, shipper_country_code, customer_postal_code, customer_country_code,
                                sys_default=False, cust_default=False, error=True, context=None):
        '''
        This function is used to Get shipping rates for Fedex 
        parameters: 
            All the Fedex Shipping and packaging type parameters
        '''
        fedex_rate = self.return_fedex_shipping_rate(dropoff_type_fedex, service_type_fedex, packaging_type_fedex,
                                                     package_detail_fedex, payment_type_fedex, physical_packaging_fedex,
                                                     weight, shipper_postal_code, shipper_country_code,
                                                     customer_postal_code, customer_country_code, sys_default,
                                                     cust_default, error, context)
        sr_no = 9
        sys_default_value = False
        cust_default_value = False
        if sys_default:
            sys_default_vals = sys_default.split('/')
            if sys_default_vals[0] == 'FedEx':
                sys_default_value = True
                sr_no = 2

        if cust_default:
            cust_default_vals = cust_default.split('/')
            if cust_default_vals[0] == 'FedEx':
                cust_default_value = True
                sr_no = 1

        fedex_res_vals = {
            'name': service_type_fedex,
            'type': 'FedEx',
            'rate': fedex_rate,
            'weight': weight,
            'sys_default': sys_default_value,
            'cust_default': cust_default_value,
            'sr_no': sr_no
        }
        if self._context.get('saleorder_id', False):
            fedex_res_vals['saleorder_id'] = self._context['saleorder_id']
        else:
            fedex_res_vals['picking_id'] = self[0].id
        fedex_res_id = self.env['shipping.response'].create(fedex_res_vals)
        logger.info('fedex_res_id=====> %s', fedex_res_id)
        logger.info('fedex_res_vals=====> %s', fedex_res_vals)
        if fedex_res_id:
            return True
        else:
            return False

    def create_quotes(self, values):
        '''
        This function is used to Create the shipping rates in sale aswell as in delivey order
        parameters: 
            values : shipping rate creation values
            type: Dictionary
        '''
        for vals in values.postage:
            quotes_vals = {
                'name': vals['Service'],
                'type': self._context['type'] or '',
                'rate': vals['Rate'],
                'weight': values.weight,
                'sys_default': False,
                'cust_default': False,
                'sr_no': vals['sr_no'],
            }
            if self._context.get('saleorder_id', False):
                quotes_vals['saleorder_id'] = self._context['saleorder_id']
            else:
                quotes_vals['picking_id'] = self[0].id

            res_id = self.env['shipping.response'].create(quotes_vals)
        if res_id:
            return True
        else:
            return False

    def create_attachment(self, vals):
        attachment_pool = self.env['ir.attachment']
        data_attach = {
            'name': 'PackingList.' + vals.image_format.lower(),
            'datas': binascii.b2a_base64(str(b64decode(vals.graphic_image))),
            'description': 'Packing List',
            'res_name': self.browse(self[0].id).name,
            'res_model': 'stock.picking',
            'res_id': self._ids[0],
        }
        attach_id = attachment_pool.search([('res_id', '=', id[0]), ('res_name', '=', self.browse(self[0].id).name)])
        if not attach_id:
            attach_id = attachment_pool.create(data_attach)
        else:
            attach_id = attach_id[0]
            attach_result = attach_id.write(data_attach)
        return attach_id

    # @api.multi
    def generate_shipping(self):
        '''
        This function is used to Get the shipping Rates in Delivery Order
        parameters: 
            No parameters
        '''
        context = dict(self._context or {})
        context = self._context.copy()
        if context is None:
            context = {}
        for id in self._ids:
            try:
                stockpicking = self.browse(id)
                shipping_type = stockpicking.shipping_type

                weight = stockpicking.weight_package
                residential = stockpicking.is_residential
                if not weight:
                    raise osv.except_osv(_('Error'), _('Package Weight Invalid!'))
                cust_address = stockpicking.sale_id.shop_id.cust_address or False
                if not cust_address:
                    if 'error' not in context.keys() or context.get('error', False):
                        raise Exception('Shop Address not defined!')
                    else:
                        return False

                shipper = Address(cust_address.name, cust_address.street, cust_address.street2 or '', cust_address.city,
                                  cust_address.state_id.code or '', cust_address.zip, cust_address.country_id.code,
                                  cust_address.phone or '', cust_address.email, cust_address.name)

                ### Recipient
                cust_address = stockpicking.partner_id
                receipient = Address(cust_address.name, cust_address.street, cust_address.street2 or '',
                                     cust_address.city, cust_address.state_id.code or '', cust_address.zip,
                                     cust_address.country_id.code, cust_address.phone or '', cust_address.email,
                                     cust_address.name)

                # Deleting previous quotes
                shipping_res_obj = self.env['shipping.response']
                saleorder_obj = self.env['sale.order']
                shipping_res_ids = shipping_res_obj.search([('picking_id', '=', self._ids[0])])
                if shipping_res_ids:
                    shipping_res_ids.unlink()

                lines = saleorder_obj.browse(stockpicking.sale_id.id).order_line
                heaviest_product_id = self._get_heaviest_product([id], lines)
                context['manual_click'] = True
                sys_default = self._get_sys_default_shipping(stockpicking.sale_id, heaviest_product_id, weight)
                context['sys_default'] = sys_default
                cust_default = self._get_cust_default_shipping(stockpicking.carrier_id.id)
                context['cust_default'] = cust_default
                if 'usps_active' not in context.keys() and (shipping_type == 'USPS' or shipping_type == 'All'):
                    usps_info = self.env['shipping.usps'].get_usps_info()
                    usps_info = self.env['stock.picking'].get_usps_info()
                    service_type_usps = stockpicking.service_type_usps
                    first_class_mail_type_usps = stockpicking.first_class_mail_type_usps or ''
                    container_usps = stockpicking.container_usps or ''
                    size_usps = stockpicking.size_usps
                    width_usps = stockpicking.width_usps
                    length_usps = stockpicking.length_usps
                    height_usps = stockpicking.height_usps
                    girth_usps = stockpicking.girth_usps
                    usps = shippingservice.USPSRateRequest(usps_info, service_type_usps, first_class_mail_type_usps,
                                                           container_usps, size_usps, width_usps, length_usps,
                                                           height_usps, girth_usps, weight, shipper, receipient,
                                                           cust_default, sys_default)
                    usps_response = usps.send()
                    context['type'] = 'USPS'
                    self.with_context(context).create_quotes(usps_response)

                if shipping_type == 'UPS' or shipping_type == 'All':
                    ups_info = self.env['shipping.ups'].get_ups_info()
                    pickup_type_ups = stockpicking.pickup_type_ups
                    service_type_ups = stockpicking.service_type_ups
                    packaging_type_ups = stockpicking.packaging_type_ups
                    if cust_address.country_id.code == 'US':
                        measurement = 'LBS'
                    else:
                        measurement = 'KGS'
                    ups = shippingservice.UPSRateRequest(ups_info, pickup_type_ups, service_type_ups,
                                                         packaging_type_ups, weight, shipper, receipient, cust_default,
                                                         sys_default, measurement, residential)
                    ups_response = ups.send()
                    context['type'] = 'UPS'
                    self.with_context(context).create_quotes(ups_response)

                if shipping_type == 'Fedex' or shipping_type == 'All':
                    dropoff_type_fedex = stockpicking.dropoff_type_fedex
                    service_type_fedex = stockpicking.service_type_fedex
                    packaging_type_fedex = stockpicking.packaging_type_fedex
                    package_detail_fedex = stockpicking.package_detail_fedex
                    payment_type_fedex = stockpicking.payment_type_fedex
                    physical_packaging_fedex = stockpicking.physical_packaging_fedex
                    shipper_postal_code = shipper.zip
                    shipper_country_code = shipper.country_code
                    customer_postal_code = receipient.zip
                    customer_country_code = receipient.country_code
                    error_required = True
                    shipping_res = self.generate_fedex_shipping([id], dropoff_type_fedex, service_type_fedex,
                                                                packaging_type_fedex, package_detail_fedex,
                                                                payment_type_fedex, physical_packaging_fedex, weight,
                                                                shipper_postal_code, shipper_country_code,
                                                                customer_postal_code, customer_country_code,
                                                                sys_default, cust_default, error_required, context)
            except Exception as exc:
                check = self.write({'error_for_faulty': 'Error While Generating Shipping Quotes \n' + str(exc)})
                self._cr.commit()
                raise osv.except_osv(_('Error!'), _('%s' % (exc,)))
            return True

    def _get_cust_default_shipping(self, carrier_id):
        '''
        This function is used to Get the default shipping type based on carrier
        parameters: 
            carrier_id : (int) 
        '''
        if carrier_id:
            carrier_obj = self.env['delivery.carrier']
            carrier_lnk = carrier_obj
            cust_default = ''
            if carrier_lnk.is_ups:
                cust_default = 'UPS'
                service_type_ups = carrier_lnk.service_output or '03'
                cust_default += '/' + service_type_ups
            elif carrier_lnk.is_fedex:
                cust_default = 'FedEx'
                service_type_fedex = carrier_lnk.service_output or 'FEDEX_GROUND'
                cust_default += '/' + service_type_fedex
            elif carrier_lnk.is_usps:
                service_type_usps = 'First Class'
                if carrier_lnk.service_output:
                    service_type_usps = carrier_lnk.service_output

                container_usps = 'Parcel'
                if carrier_lnk.container_usps:
                    container_usps = carrier_lnk.container_usps

                size_usps = 'REGULAR'
                if carrier_lnk.size_usps:
                    size_usps = carrier_lnk.size_usps
                cust_default = 'USPS' + '/' + service_type_usps + '/' + container_usps + '/' + size_usps
        else:
            cust_default = False
        return cust_default

    def _get_sys_default_shipping(self, sale_id, product_id, weight):
        '''
        This function is used to Get the default shipping type based on product Id, Weight and sale order Id
        parameters: 
            sale_id : (int) 
            product_id : (int) 
            weight : (float) 
        '''
        context = dict(self._context or {})
        product_obj = self.env['product.product']
        product_shipping_obj = self.env['product.product.shipping']
        product_shipping_ids = product_shipping_obj.search([('product_id', '=', product_id)])
        sys_default = ''
        #        sys_default = 'USPS/ParcelPost/Parcel/REGULAR/0'
        #        sys_default = 'UPS/11/00'
        #        if weight >= 5.0:
        #            sys_default = 'UPS/03/02'
        #        elif (weight*16) > 14.0:
        #            sys_default = 'USPS/Priority/Parcel/REGULAR/1'
        #        else:
        #            sys_default = 'USPS/First Class/Parcel/REGULAR/1'
        # Do Not Call the Function if it is manually Clicked
        if product_shipping_ids:
            self._cr.execute(
                'SELECT * FROM product_product_shipping WHERE weight <= %s and product_id=%s order by sequence desc limit 1' % (
                    weight, product_id))
        else:
            categ_id = product_obj.browse(product_id).product_tmpl_id.categ_id.id
            self._cr.execute(
                'SELECT * FROM product_category_shipping WHERE weight <= %s and product_categ_id=%s order by sequence desc limit 1' % (
                    weight, categ_id))
        res = self._cr.dictfetchall()
        logger.info('res==jkjk===> %s', res)
        if res:
            if res[0]['shipping_type'] == 'USPS':
                service_type_usps = 'First Class'
                if res[0]['service_type_usps']:
                    service_type_usps = res[0]['service_type_usps']

                container_usps = 'Parcel'
                if res[0]['container_usps']:
                    container_usps = res[0]['container_usps']

                size_usps = 'REGULAR'
                if res[0]['size_usps']:
                    size_usps = res[0]['size_usps']

                postage = '0'
                if res[0]['postage_usps']:
                    postage = '1'

                sys_default = res[0][
                                  'shipping_type'] + '/' + service_type_usps + '/' + container_usps + '/' + size_usps + '/' + postage

            elif res[0]['shipping_type'] == 'UPS':
                service_type_ups = '03'
                if res[0]['service_type_ups']:
                    service_type_ups = res[0]['service_type_ups']

                packaging_type_ups = '02'
                if res[0]['service_type_ups']:
                    packaging_type_ups = res[0]['packaging_type_ups']
                sys_default = res[0]['shipping_type'] + '/' + service_type_ups + '/' + packaging_type_ups

            elif res[0]['shipping_type'] == 'Fedex':
                service_type_fedex = 'FEDEX_GROUND'
                if res[0]['service_type_fedex']:
                    service_type_fedex = res[0]['service_type_fedex']

                sys_default = res[0]['shipping_type'] + '/' + service_type_fedex + '/' + 'YOUR_PACKAGING'
        return sys_default

    # @api.multi
    def get_min_shipping_rate(self, sale_id, product_shipping_ids, weight):
        context = dict(self._context or {})
        shipment_types = {
            'Priority': 'Priority',
            'Express': 'Express',
            'First': 'First Class',
            'ParcelPost': 'ParcelPost',
            'ParcelSelect': 'ParcelSelect',
            'ExpressMailInternational': 'Express',
            'FirstClassMailInternational': 'First Class',
            'PriorityMailInternational': 'Priority',
        }
        product_shipping_obj = self.env['product.product.shipping']
        rate_service = {}
        if context is None:
            context = {}

        shop_address = sale_id and sale_id.shop_id.cust_address or False
        if not shop_address:
            if 'error' not in context.keys() or context.get('error', False):
                raise Exception('Shop Address not defined!')
            else:
                return False

        shipper = Address(shop_address.name or shop_address.name, shop_address.street, shop_address.city,
                          shop_address.state_id.code or '', shop_address.zip, shop_address.country_id.code,
                          shop_address.street2 or '', shop_address.phone or '', shop_address.email, shop_address.name)
        ### Recipient
        cust_address = sale_id.partner_shipping_id
        receipient = Address(cust_address.name or cust_address.name, cust_address.street, cust_address.city,
                             cust_address.state_id.code or '', cust_address.zip, cust_address.country_id.code,
                             cust_address.street2 or '', cust_address.phone or '', cust_address.email,
                             cust_address.name)

        for product_shipping_id in product_shipping_ids:
            product_shipping_data = product_shipping_obj.browse(product_shipping_id)
            if product_shipping_data:
                if product_shipping_data.shipping_type == 'USPS':
                    service_type_usps = 'First Class'
                    if product_shipping_data.service_type_usps:
                        service_type_usps = product_shipping_data.service_type_usps

                    container_usps = 'Parcel'
                    if product_shipping_data.container_usps:
                        container_usps = product_shipping_data.container_usps

                    size_usps = 'REGULAR'
                    if product_shipping_data.size_usps:
                        size_usps = product_shipping_data.size_usps

                    postage = '0'
                    if product_shipping_data.postage_usps:
                        postage = '1'

                    usps_rate_sys_default = product_shipping_data.shipping_type + '/' + service_type_usps + '/' + container_usps + '/' + size_usps + '/' + postage
                    try:
                        all_shipping_res = self.get_endicia_rates(False, weight, shipper, receipient,
                                                                  context.get('cust_default', False),
                                                                  usps_rate_sys_default, context.get('error', False),
                                                                  context)
                        usps_rate = []
                        shipping_usps_rate = {}
                        for shipping_res in all_shipping_res['info']:
                            if shipment_types.get(shipping_res['package']) == product_shipping_data.service_type_usps:
                                rate_service['usps_rate'] = shipping_res['cost']
                    except:
                        rate_service['usps_rate'] = 999
                        pass

                elif product_shipping_data.shipping_type == 'UPS':
                    service_type_ups = '03'
                    if product_shipping_data.service_type_ups:
                        service_type_ups = product_shipping_data.service_type_ups

                    packaging_type_ups = '02'
                    if product_shipping_data.packaging_type_ups:
                        packaging_type_ups = product_shipping_data.packaging_type_ups

                    ups_rate_sys_default = product_shipping_data.shipping_type + '/' + service_type_ups + '/' + packaging_type_ups

                    ups_info = self.env['shipping.ups'].get_ups_info()
                    pickup_type_ups = '01'
                    ups_rate = 999
                    try:
                        if cust_address.country_id.code == 'US':
                            measurement = 'LBS'
                        else:
                            measurement = 'KGS'
                        ups = shippingservice.UPSRateRequest(ups_info, pickup_type_ups, service_type_ups,
                                                             packaging_type_ups, weight, shipper, receipient, False,
                                                             ups_rate_sys_default, measurement, True)
                        ups_response = ups.send()
                        if len(ups_response.postage):
                            ups_rate = ups_response.postage[0]['Rate']
                            rate_service['ups_rate'] = ups_rate
                    except:
                        rate_service['ups_rate'] = ups_rate
                        pass


                elif product_shipping_data.shipping_type == 'Fedex':
                    service_type_fedex = 'FEDEX_GROUND'
                    if product_shipping_data:
                        service_type_fedex = product_shipping_data.service_type_fedex

                    fedex_rate_sys_default = product_shipping_data.shipping_type + '/' + service_type_fedex + '/' + 'YOUR_PACKAGING'
                    dropoff_type_fedex = 'REGULAR_PICKUP'
                    packaging_type_fedex = 'YOUR_PACKAGING'
                    package_detail_fedex = 'INDIVIDUAL_PACKAGES'
                    payment_type_fedex = 'SENDER'
                    physical_packaging_fedex = 'BOX'
                    error_required = True
                    #                    try:
                    fedex_rate = self.return_fedex_shipping_rate(dropoff_type_fedex, service_type_fedex,
                                                                 packaging_type_fedex, package_detail_fedex,
                                                                 payment_type_fedex, physical_packaging_fedex, weight,
                                                                 shipper.zip, shipper.country_code, receipient.zip,
                                                                 receipient.country_code, fedex_rate_sys_default, False,
                                                                 error_required, context)
                    rate_service['fedex_rate'] = fedex_rate
        #                    except:
        #                        rate_service['fedex_rate']=999
        #                        pass

        logger.info('Minimum shipping rate=====> %s', min(rate_service.items(), key=lambda x: x[1])[1])
        min_rate_shipping = min(rate_service.items(), key=lambda x: x[1])[0]
        if min_rate_shipping == 'usps_rate':
            sys_default = usps_rate_sys_default
        elif min_rate_shipping == 'ups_rate':
            sys_default = ups_rate_sys_default
        elif min_rate_shipping == 'fedex_rate':
            sys_default = fedex_rate_sys_default
        else:
            sys_default = False
        return sys_default

    @api.model
    def create(self, vals):
        saleorder_obj = self.env['sale.order']
        context = dict(self._context or {})
        if context is None:
            context = {}
        vals['length_package'] = 0.0
        vals['height_package'] = 0.0
        vals['width_package'] = 0.0
        logger.info('vals===top==> %s', vals)
        if vals.get('picking_type_id', False) and vals['picking_type_id'] == 2 and vals.get('origin', False):
            carrier_obj = self.env['delivery.carrier']
            saleorder_obj = self.env['sale.order']
            order_id = saleorder_obj.search([('name', '=', vals['origin'])])
            saleorder_lnk = order_id[0]
            vals['length_package'] = saleorder_lnk.length_package
            vals['height_package'] = saleorder_lnk.length_package
            vals['width_package'] = saleorder_lnk.width_package
            vals['weight_package'] = saleorder_lnk.weight_package
            lines = saleorder_lnk.order_line
            weight = vals.get('weight_net', 0.00)
            if weight == 0.00:
                for line in lines:
                    weight = weight + line.product_id.weight_net * line.product_uom_qty
            vals['weight_package'] = weight

            if vals.get('carrier_id', False):
                ### Customer default
                carrier = carrier_obj.browse(vals['carrier_id'])
                if carrier.name == 'Economy Shipping':
                    vals = self._get_shipping_data(vals, weight)
                else:
                    if carrier.is_usps:
                        vals['shipping_type'] = 'USPS'
                        vals['service_type_usps'] = carrier.service_output
                        vals['container_usps'] = carrier.container_usps
                        vals['size_usps'] = carrier.size_usps
                    elif carrier.is_ups:
                        vals['shipping_type'] = 'UPS'
                        vals['pickup_type_ups'] = '01'
                        vals['service_type_ups'] = carrier.service_output
                        vals['packaging_type_ups'] = '03'
                    elif carrier.is_fedex:
                        vals['shipping_type'] = 'Fedex'
                        vals['service_type_fedex'] = carrier.service_output
            else:
                logger.info('vals==economy===> %s', vals)
                vals = self._get_shipping_data(vals, weight)

            # Check International Order
            address_data = self.env['res.partner'].browse(vals['partner_id'])
            if not address_data.country_id.code:
                raise osv.except_osv(_('Error'), _('Customer Country Not Defined!!'))
            if address_data.country_id.code.upper() != 'US':
                vals['is_international'] = True
            else:
                logger.info('vals==else===> %s', vals)
                vals['is_international'] = False
        logger.info('vals=====> %s', vals)
        return super(stock_picking, self).create(vals)

    def _get_shipping_data(self, vals, weight):
        ### System default
        context = dict(self._context or {})
        prod_obj = self.env['product.product']
        saleorder_obj = self.env['sale.order']
        order_id = saleorder_obj.search([('name', '=', vals['origin'])])
        saleorder_lnk = order_id[0]
        lines = saleorder_lnk.order_line
        heaviest_product_id = self._get_heaviest_product(False, lines)
        product = prod_obj.browse(heaviest_product_id)
        vals['is_deliveryconfirmation'] = True if saleorder_lnk.amount_total >= 200.0 else False
        sys_default = self._get_sys_default_shipping(saleorder_lnk, heaviest_product_id, weight)
        logger.info('sys_default=====> %s', sys_default)
        if sys_default.split('/')[0] == 'USPS':
            vals['shipping_type'] = 'USPS'
            vals['service_type_usps'] = sys_default.split('/')[1] or ''
            vals['container_usps'] = sys_default.split('/')[2] or ''
            vals['size_usps'] = sys_default.split('/')[3] or ''
            postage_usps = sys_default.split('/')[4] or ''
            if postage_usps == '1':
                vals['include_postage_usps'] = True
            else:
                vals['include_postage_usps'] = False
        elif sys_default.split('/')[0] == 'UPS':
            vals['shipping_type'] = 'UPS'
            vals['pickup_type_ups'] = '01'
            vals['service_type_ups'] = sys_default.split('/')[1]
            vals['packaging_type_ups'] = sys_default.split('/')[2]
        elif sys_default.split('/')[0] == 'Fedex':
            vals['shipping_type'] = 'Fedex'
            vals['service_type_fedex'] = sys_default.split('/')[1] or ''
        return vals

    def _get_total_product_weight(self, lines):
        weight = 0.0
        for line in lines:
            product_qty = 0.0
            try:
                product_qty = line.product_uos_qty
            except Exception as e:
                product_qty = line.product_qty

            weight += line.product_id.product_tmpl_id.weight_net * product_qty
        return weight

    # @api.multi
    def _get_heaviest_product(self, id, lines):
        '''
        This function is used to Get heaviest product id to get the carrier type in delivery order based on product or product category conf
        parameters: 
            lines: (dictionary) Product Line
        '''
        context = dict(self._context or {})
        weight = 0.0
        product_id = False
        for line in lines:
            product_qty = 0.0
            try:
                product_qty = line.product_uom_qty
            except Exception as e:
                product_qty = line.product_uom_qty

            if (line.product_id.product_tmpl_id.weight_net * product_qty) >= weight:
                product_id = line.product_id.id
                weight = line.product_id.product_tmpl_id.weight_net * product_qty
        return product_id

    def _cal_weight_usps(self, name, args):
        context = dict(self._context or {})
        res = {}
        uom_obj = self.env['product.uom']
        for picking in self:
            weight_net = picking.weight_net or 0.00
            weight_net_usps = weight_net / 2.2

            res[picking.id] = {
                'weight_net_usps': weight_net_usps,
            }
        return res

    def _get_picking_line(self):
        result = {}
        for line in self.env['stock.move'].browse(self._ids):
            result[line.picking_id.id] = True
        return result.keys()

    def action_assign_new(self, cr, uid, ids, *args):
        """
        Inherited from stock/stock.py
        Changes state of picking to available if all moves are confirmed and done.
        Rather than returning osv.except_osv, it returns False
        @return: True
        """
        for pick in self.browse(cr, uid, ids):
            move_ids = [x.id for x in pick.move_lines if x.state == 'confirmed']
            if not move_ids:
                return False
            self.pool.get('stock.move').action_assign(cr, uid, move_ids)
        return True


stock_picking()
