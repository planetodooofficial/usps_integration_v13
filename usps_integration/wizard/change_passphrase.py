import logging

#from custom.usps_integration_v13.usps_integration.models import endicia
import sys
sys.path.insert(1, '/opt/odoo13e/custom/usps_integration_v13/usps_integration/models')
import endicia
from odoo import models, fields
from odoo.exceptions import UserError
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)


class change_passphrase(models.TransientModel):
    _name = 'change.passphrase'

    def action_change_passphrase(self):
        new_passphrase = self.name
        if len(new_passphrase) < 5:
            raise UserError(_('Passphrase must be atleast 5 characters long'))

        ship_endicia_obj = self.env['shipping.usps']
        ship_endicia = ship_endicia_obj.get_endicia_info()
        old_passphrase = ship_endicia.passphrase

        if new_passphrase == old_passphrase:
            raise UserError(_('Old passphrase and new passphrase cannot be same'))

        # Use Endicia API
        try:
            request = endicia.ChangePasswordRequest(ship_endicia.requester_id, ship_endicia.account_id, old_passphrase,
                                                    new_passphrase, ship_endicia.test)
            response = request.send()
            change_passphrase_resp = response._get_value()
        except Exception as e:
            raise UserError(_('Error changing passphrase'))

        if change_passphrase_resp['status'] != '0':
            raise UserError(_('Error changing passphrase'))

        res = ship_endicia_obj.write_passphrase(new_passphrase)
        if res:
            message = _('Passphrase Changed successfully')
            raise UserError(_(message))
        else:
            message = _('Error changing passphrase')
            raise UserError(_(message))

        return {'type': 'ir.actions.act_window_close'}

    name = fields.Char(string='New Passphrase', required=True)
