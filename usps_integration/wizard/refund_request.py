from openerp.osv import osv
from openerp import models, fields, api, _
from openerp.tools.translate import _
from openerp.addons.usps_integration.models import endicia
import datetime
import logging
import time
import commands
_logger = logging.getLogger(__name__)


class refund_request(models.TransientModel):
    _inherit = "refund.request"


    @api.multi
    def action_refund_request_usps(self):
        '''
        This function is used to Cancel shipping label based on the carrier type choosen in the deilvery order
        parameters: 
            No Parameters
        '''
        if self._context.get('active_ids',False):
            picking_obj = self.env['stock.picking']
            ship_endicia = self.env['shipping.usps'].get_endicia_info()
            requester_id = ship_endicia.requester_id
            account_id = ship_endicia.account_id
            passphrase = ship_endicia.passphrase
            debug = ship_endicia.test
            tracking_numbers = []
            for picking in picking_obj.browse(self._context['active_ids']):
                tracking_number = picking.carrier_tracking_ref
                if tracking_number:
                    tracking_numbers.append(tracking_number)

            if len(tracking_numbers) > 100:
                raise osv.except_osv(_('Error'), _('Maximum 100 requests can be submitted'))

            if picking.carrier_id and (picking.carrier_id.name.startswith('USPS')) or picking.shipping_type.lower() == 'usps':
                try:
                    request = endicia.RefundRequest(requester_id, account_id, passphrase, tracking_numbers, debug=debug)
                    response = request.send()
                    response = response._get_value()
                    for i in range(len(response['tracking_no'])):
                        is_approved = (response['is_approved'][i].text == 'YES') and 'approved' or 'not approved'

                except Exception, e:
                    raise osv.except_osv(_('Error'), _('%s' % (e,)))
            for picking in picking_obj.browse(self._context['active_ids']):
                picking.write({'shipping_rate': 0.00, 'carrier_id': False, 'carrier_tracking_ref': False, 'postage_bought': False})
                picking.write({'label_printed' : False, 'label_printed_datetime': False, 'label_generated': False} )
            return {'type': 'ir.actions.act_window_close'}


refund_request()
