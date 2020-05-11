import logging
import requests
from suds.sudsobject import asdict
import json
import xmltodict
import pprint




import datetime
import  unicodedata
import sys
# sys.path.insert(1, '/opt/odoo13e/custom/usps_integration_v13/usps_integration/models')
# import endicia

from custom_addons.usps_integration_v13.usps_integration.models import endicia
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
        post_balance =1
        ship_endicia = self.env['shipping.usps'].get_endicia_info()
        requester_id = ship_endicia.requester_id
        account_id = ship_endicia.account_id
        passphrase = ship_endicia.passphrase
        debug = ship_endicia.test

        tot_rate = self.name
        if tot_rate < 10.00:
            raise osv.except_osv(_('Warning'), _('You cannot buy postage less than $10'))

        try:
            # request = endicia.RecreditRequest(requester_id, account_id, passphrase, tot_rate, debug=debug)
            # response = request.send()
            # buy_postage_resp = response._get_value()


            res = self.buying_soap(requester_id,account_id,passphrase, str(tot_rate))
            response = json.loads(res)
            # buy_postage_resp = response.text.encode('utf8')
            recredit_req = response.get("soap:Envelope").get("soap:Body").get("BuyPostageResponse").get(
                "RecreditRequestResponse")
            if 'ErrorMessage' in recredit_req:
                print("There is an error")
                Certified_Intermediary = recredit_req.get("CertifiedIntermediary")
                post_balance = Certified_Intermediary.get('PostageBalance')
                print(post_balance)
            else:
                Certified_Intermediary = recredit_req.get("CertifiedIntermediary")
                post_balance = Certified_Intermediary.get('PostageBalance')
                print(post_balance)


        except Exception as e:
            raise osv.except_osv(_('Error'), _('Error buying postage'))

        message = _('Remaining postage balance: %s\nTotal amount of postage printed:' % (post_balance))

        if message:
            raise osv.except_osv(_('Message'), _(message))



        # message = _('Remaining postage balance: %s\nTotal amount of postage printed: %s' % (
        #     buy_postage_resp['postage_balance'], buy_postage_resp['postage_printed']))
        # if message:
        #     raise osv.except_osv(_('Message'), _(message))

        return {'type': 'ir.actions.act_window_close'}

    name = fields.Float(string='Total Rate')



    def buying_soap(self,requester_id,account_id,passphrase, tot_rate):
        url = "https://elstestserver.endicia.com/LabelService/EwsLabelService.asmx"

        payload = "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n" \
                  "<soap:Envelope xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"\n               " \
                  "xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\"\n               " \
                  "xmlns:soap=\"http://schemas.xmlsoap.org/soap/envelope/\">\n  " \
                  "<soap:Body>\n    " \
                  "<BuyPostage xmlns=\"www.envmgr.com/LabelService\">\n      " \
                  "<RecreditRequest>\n        " \
                  "<RequesterID>"+requester_id+"</RequesterID>\n        " \
                  "<RequestID>1</RequestID>\n        " \
                  "<CertifiedIntermediary>\n         " \
                  " <AccountID>"+account_id+"</AccountID>\n          " \
                  "<PassPhrase>"+passphrase+"</PassPhrase>\n        " \
                  "</CertifiedIntermediary>\n        " \
                  "<RecreditAmount>"+tot_rate+"</RecreditAmount>\n      " \
                  "</RecreditRequest>\n    " \
                  "</BuyPostage>\n  " \
                  "</soap:Body>\n" \
                  "</soap:Envelope>"
        headers = {
            'Host': 'elstestserver.endicia.com',
            'Content-Type': 'text/xml; charset=utf-8',
            'SOAPAction': '"www.envmgr.com/LabelService/BuyPostage"'
        }
        response = requests.request("POST", url, headers=headers, data=payload)
        d = response.text.encode('utf8')
        pp = pprint.PrettyPrinter(indent=4)
        # pp.pprint(json.dumps(xmltodict.parse(d)))
        py_res = json.dumps(xmltodict.parse(d))
        return  py_res


        # json_form = json.dumps(self.recursive_asdict(d))

        # example = json_form




