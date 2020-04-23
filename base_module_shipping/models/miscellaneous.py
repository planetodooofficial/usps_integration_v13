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

import re

class Address(object):
    def __init__(self, name, address, address2, city, state_code, zip, country_code, phone='', email='', company_name='', country='', is_residence=True):
        self.company_name = company_name or ''
        self.name = name or ''
        self.address1 = address or ''
        self.address2 = address2 or ''
        self.city = city or ''
        self.state_code = state_code or ''
        self.zip = str(zip) if zip else ''
        self.country_code = country_code or ''
        self.country = country or ''
        self.phone = re.sub('[^0-9]*', '', str(phone)) if phone else ''
        self.email = email or ''
        self.is_residence = is_residence or False

    def __eq__(self, other):
        return vars(self) == vars(other)

    def __repr__(self):
        return (self.company_name, self.name, self.address1 , self.address2, self.city, self.state_code, self.zip, self.country_code, self.phone, self.email)