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

from odoo.osv import osv
from odoo.tools.translate import _
import cStringIO
from datetime import datetime
import random
import StringIO
import time
import base64
from base64 import b64decode
from PyPDF2 import PdfFileMerger, PdfFileReader
from odoo import models, fields, api, _
import binascii
import commands
import os


class generate_label_pdf(models.TransientModel):
    _name = "generate.label.pdf"
    _description = "Generate Label PDF"
     
     
    @api.multi
    def print_lable(self):
        picking_object = self.env['stock.picking']
        para = self.env["ir.config_parameter"]
        attachment_pool = self.env['ir.attachment']
        ip_address = para.get_param("web.base.url")
        dir_loc = os.path.dirname(os.path.abspath(__file__))
        a= dir_loc.split('/')
        a.pop()
        path = ""
        for i in a:
            if i == '':
                path = ""
            path += i + '/'
        new_path = path + 'static/src/'
        random_sequence = random.sample(range(1,1000),1)
        batch_file =  str(new_path) + '/sevicelabel' + str(random_sequence[0]) + '.pdf'
        
        if os.path.exists(batch_file):
            os.remove(batch_file)
        
        merger = PdfFileMerger()
        i = datetime.now()
        date = i.strftime('%Y/%m/%d %H:%M:%S')
        for pick in picking_object.browse(self._context.get('active_ids')):
            attachment_ids = attachment_pool.search([('res_id','=',pick.id)])
            if attachment_ids:
                for i in attachment_ids:
                    a_obj = i
                    file1 = new_path +str(pick.id)+".pdf"
                    f = open(file1, 'wb')
                    f.write(b64decode(a_obj.datas))
                    f.close()
                    merger.append(PdfFileReader(file(file1, 'rb')))
                pick.write({'label_printed' : True, 'label_printed_datetime' : date})
        merger.write(str(batch_file))
        self._cr.commit()
        if attachment_ids:
            url =  ip_address + "/base_module_shipping/static/src" + '/sevicelabel' + str(random_sequence[0]) + '.pdf'
            return {
                            'type': 'ir.actions.act_url',
                            'url': url,
                            'target': 'new'
                    }
        if not attachment_ids:
           raise osv.except_osv(_('Error'), _('No Attachment Found!'),)

generate_label_pdf()