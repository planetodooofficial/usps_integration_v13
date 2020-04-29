import logging

from custom.usps_integration_v13.usps_integration.models import endicia
from odoo import models, fields
from odoo.osv import osv
from odoo.tools.translate import _
# import commands
_logger = logging.getLogger(__name__)


class buying_postage(models.TransientModel):
    _name = "buying.postage"
    _description = "Buying Postage"

    # @api.multi
    def action_buy_postge(self):
        """
        This function is used to Re-credit Endicia Account
        parameters:
            No Parameters
        """
        ship_endicia = self.env['shipping.usps'].get_endicia_info()
        requester_id = ship_endicia.requester_id
        account_id = ship_endicia.account_id
        passphrase = ship_endicia.passphrase
        debug = ship_endicia.test

        tot_rate = self.name
        if tot_rate < 10.00:
            raise osv.except_osv(_('Warning'), _('You cannot buy postage less than $10'))

        try:
            request = endicia.RecreditRequest(requester_id, account_id, passphrase, tot_rate, debug=debug)
            response = request.send()
            buy_postage_resp = response._get_value()
        except Exception as e:
            raise osv.except_osv(_('Error'), _('Error buying postage'))

        message = _('Remaining postage balance: %s\nTotal amount of postage printed: %s' % (
            buy_postage_resp['postage_balance'], buy_postage_resp['postage_printed']))
        if message:
            raise osv.except_osv(_('Message'), _(message))

        return {'type': 'ir.actions.act_window_close'}

    name = fields.Float(string='Total Rate')