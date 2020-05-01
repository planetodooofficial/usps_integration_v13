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

import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class generate_shipping_quotes(models.TransientModel):
    _name = "generate.shipping.quotes"
    _description = "Generate Shipping Quotes"

    name = fields.Char(string='Batch No',
                       defaults=lambda self, cr, uid, context: self.pool['ir.sequence'].next_by_code(cr, uid,
                                                                                                     'print.packing.slip',
                                                                                                     context=context))

    @api.model
    def default_get(self, fields):
        '''
        This function is used to Get the Batch Number while generating shipping label in delivery order
        parameters: 
        '''
        if self._context is None:
            self._context = {}
        res = super(generate_shipping_quotes, self).default_get(fields)
        res.update({'name': self.env['ir.sequence'].next_by_code('print.packing.slip')})
        return res

        # @api.multi

    def action_get_quotes(self):
        '''
        This function is used to Generated the generate shipping label function based on the carrier type choosen in the deilvery order
        parameters: 
            No Parameters
        '''
        result = False
        context = dict(self._context or {})
        if context.get('active_ids', False):
            picking_obj = self.env['stock.picking']
            sale_obj = self.env['sale.order']
            carrier_ids = []
            (data,) = self
            shipping_response_obj = self.env['shipping.response']
            picking_ids = context['active_ids']
            for picking_id in picking_ids:
                picking_data = picking_obj.browse(picking_id)
                sale_data = sale_obj.search([('name', '=', picking_data.origin)])
                if picking_data.state != 'done':
                    if picking_data.shipping_type.lower() == 'usps':
                        carrier_ids = self.env['delivery.carrier'].search(
                            [('service_output', '=', picking_data.service_type_usps), ('is_usps', '=', True),
                             ('container_usps', '=', picking_data.container_usps)])
                    elif picking_data.shipping_type.lower() == 'fedex':
                        carrier_ids = self.env['delivery.carrier'].search(
                            [('service_output', '=', picking_data.service_type_fedex), ('is_fedex', '=', True)])
                    elif picking_data.shipping_type.lower() == 'ups':
                        carrier_ids = self.env['delivery.carrier'].search(
                            [('service_output', '=', picking_data.service_type_ups), ('is_usps', '=', True)])
                    if not carrier_ids:
                        picking_data.write(
                            {'is_faulty': True, 'error_for_faulty': 'Shipping service output settings not defined'})
                        continue

                    try:
                        if picking_data.shipping_type.lower() == 'usps':
                            result = shipping_response_obj.with_context().generate_usps_tracking_no(picking_data)
                        elif picking_data.shipping_type.lower() == 'fedex':
                            result = shipping_response_obj.with_context().generate_fedex_tracking_no(picking_data)
                        elif picking_data.shipping_type.lower() == 'ups':
                            result = shipping_response_obj.with_context().generate_ups_tracking_no(picking_data)
                    except Exception as e:
                        log_data = picking_data.write({'error_for_faulty': str(e), 'is_faulty_deliv_order': True})
                        self._cr.commit()
                        pass
                    if result:
                        picking_data.write({'carrier_id': carrier_ids[0].id, 'batch_no': data.name})
                        sale_data.write({'carrier_id': carrier_ids[0].id})
                        picking_data.write({'label_generated': True, 'is_faulty_deliv_order': False})
                        self._cr.commit()
        return {'type': 'ir.actions.act_window_close'}


generate_shipping_quotes()
