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

from odoo import models, fields, api, _
from odoo.osv import osv
import odoo.addons.decimal_precision as dp
from .miscellaneous import Address
import urllib
from . import shippingservice
import logging

logging.basicConfig(level=logging.INFO)
logging.getLogger('suds.client').setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)


class sale_order(models.Model):
    _inherit = "sale.order"

    def _get_shipping_type(self):
        return [
            ('All', 'All'),
        ]

    def _default_journal(self):
        accountjournal_obj = self.env['account.journal']
        accountjournal_ids = accountjournal_obj.search([('name', '=', 'Sales Journal')])
        if accountjournal_ids:
            return accountjournal_ids[0]
        else:
            #            raise wizard.except_wizard(_('Error !'), _('Sales journal not defined.'))
            return False

    use_shipping = fields.Boolean(string='Use Shipping', default=True)
    shipping_type = fields.Selection(_get_shipping_type, string='Shipping Type', default='All')
    weight_package = fields.Float(string='Package Weight', digits_compute=dp.get_precision('Stock Weight'),
                                  help="Package weight which comes from weighinig machine in pounds", default='1')
    length_package = fields.Float(string='Package Length', default='1')
    width_package = fields.Float(string='Package Width', default='1')
    height_package = fields.Float(string='Package Height', default='1')
    units_package = fields.Char(string='Package Units', size=64, default='1')
    dropoff_type_fedex = fields.Selection([
        ('REGULAR_PICKUP', 'REGULAR PICKUP'),
        ('REQUEST_COURIER', 'REQUEST COURIER'),
        ('DROP_BOX', 'DROP BOX'),
        ('BUSINESS_SERVICE_CENTER', 'BUSINESS SERVICE CENTER'),
        ('STATION', 'STATION'),
    ], string='Dropoff Type', default='REGULAR_PICKUP')
    shipping_label = fields.Binary(string='Logo')
    shipping_rate = fields.Float(string='Shipping Rate')
    batch_no = fields.Char(string='Batch No', size=64)
    is_faulty = fields.Boolean(string='Is faulty')
    is_international = fields.Boolean(string='Is International')
    is_expedited = fields.Boolean('Is Expedited')
    is_one_day_expedited = fields.Boolean(string='Is One Day Expedited')
    is_two_day_expedited = fields.Boolean(string='Is Two Day Expedited')
    sku = fields.Char(string='sku', size=64)
    # defult feld
    invalid_addr = fields.Boolean(string='Invalid Address', readonly=True)
    client_order_ref = fields.Char(string='Tracking Number', size=64)
    journal_id = fields.Many2one('account.journal', string='Journal', readonly=True, default=_default_journal)
    response_usps_ids = fields.One2many('shipping.response', 'saleorder_id', string='Shipping Response')

    # @api.multi
    def generate_shipping_order(self):
        '''
        This function is used to Get the shipping Rates in sale order
        parameters: 
            No parameters
        '''
        context = self._context.copy()
        picking_obj = self.env['stock.picking']
        if context is None:
            context = {}
        pick_data = picking_obj.search([('origin', '=', self.name)])
        for stockpicking in self:
            #            try:
            shipping_type = stockpicking.shipping_type
            if shipping_type.lower() == 'usps':
                usps_obj = self.env['shipping.usps']
                usps_data = usps_obj.search([])
                cust_address = usps_data.config_shipping_address_id or False

            if shipping_type.lower() == 'fedex':
                fedex_obj = self.env['shipping.fedex']
                fedex_data = fedex_obj.search([])
                cust_address = fedex_data.config_shipping_address_id or False

            if shipping_type.lower() == 'ups':
                ups_obj = self.env['shipping.ups']
                ups_data = ups_obj.search([])
                cust_address = ups_data.config_shipping_address_id or False

            weight = stockpicking.weight_package
            if not weight:
                raise Exception('Package Weight Invalid!')
            if cust_address.country_id.code != stockpicking.partner_id.country_id.code:
                residential = True
            else:
                residential = False
            if not cust_address:
                if 'error' not in context.keys() or context.get('error', False):
                    raise Exception('Shipping Address not defined!')
                else:
                    return False

            shipper = Address(cust_address.name, cust_address.street, cust_address.street2 or '', cust_address.city,
                              cust_address.state_id.code or '', cust_address.zip, cust_address.country_id.code,
                              cust_address.phone or '', cust_address.email, cust_address.name)

            ### Recipient
            cust_address = stockpicking.partner_id
            receipient = Address(cust_address.name, cust_address.street, cust_address.street2 or '', cust_address.city,
                                 cust_address.state_id.code or '', cust_address.zip, cust_address.country_id.code,
                                 cust_address.phone or '', cust_address.email, cust_address.name)

            # Deleting previous quotes
            shipping_res_obj = self.env['shipping.response']
            shipping_res_ids = shipping_res_obj.search([('picking_id', '=', self._ids[0])])
            shipping_res_ids_sales = shipping_res_obj.search([('saleorder_id', '=', self._ids[0])])
            logger.info('fshipping_res_ids_salesshipping_res_ids_sales %s', shipping_res_ids_sales)
            if shipping_res_ids_sales:
                shipping_res_ids_sales.unlink()
                self._cr.commit()
            if shipping_res_ids:
                shipping_res_ids.unlink()
                self._cr.commit()

            lines = stockpicking.order_line
            heaviest_product_id = picking_obj._get_heaviest_product([id], lines)
            context['manual_click'] = True

            sys_default = picking_obj._get_sys_default_shipping(stockpicking.id, heaviest_product_id, weight)
            context['sys_default'] = sys_default
            cust_default = picking_obj._get_cust_default_shipping(stockpicking.carrier_id.id)
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
                                                       container_usps, size_usps, width_usps, length_usps, height_usps,
                                                       girth_usps, weight, shipper, receipient, cust_default,
                                                       sys_default)
                usps_response = usps.send()
                context['type'] = 'USPS'
                context['saleorder_id'] = self._ids
                pick_data.with_context(context).create_quotes(usps_response)

            if shipping_type == 'UPS' or shipping_type == 'All':
                ups_info = self.env['shipping.ups'].get_ups_info()
                pickup_type_ups = stockpicking.pickup_type_ups
                service_type_ups = stockpicking.service_type_ups
                packaging_type_ups = stockpicking.packaging_type_ups
                if cust_address.country_id.code == 'US':
                    measurement = 'LBS'
                else:
                    measurement = 'KGS'
                ups = shippingservice.UPSRateRequest(ups_info, pickup_type_ups, service_type_ups, packaging_type_ups,
                                                     weight, shipper, receipient, cust_default, sys_default,
                                                     measurement, residential)
                ups_response = ups.send()
                context['type'] = 'UPS'
                context['saleorder_id'] = self._ids
                pick_data.with_context(context).create_quotes(ups_response)

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
                context['saleorder_id'] = self._ids
                logger.info('fcontextcontextcontextcontextid %s', context)
                shipping_res = pick_data.with_context(context).generate_fedex_shipping([id], dropoff_type_fedex,
                                                                                       service_type_fedex,
                                                                                       packaging_type_fedex,
                                                                                       package_detail_fedex,
                                                                                       payment_type_fedex,
                                                                                       physical_packaging_fedex, weight,
                                                                                       shipper_postal_code,
                                                                                       shipper_country_code,
                                                                                       customer_postal_code,
                                                                                       customer_country_code,
                                                                                       sys_default, cust_default,
                                                                                       error_required, context)
            #            except Exception, exc:
            #                raise osv.except_osv(_('Error!'),_('%s' % (exc,)))

            return True


sale_order()


class shipping_response(models.Model):
    _inherit = "shipping.response"

    saleorder_id = fields.Many2one('sale.order', string='Picking')


shipping_response()
