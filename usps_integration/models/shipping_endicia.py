import xml.etree.ElementTree as etree
import re

def indent(elem, level=0):
    """Indents an etree element so printing that element is actually human-readable"""
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def debug_print_tree(elem):
    indent(elem)
    etree.dump(elem)

class Package(object):
    ### Used for input from shipping info form - refer stock.py for dict keys
    domestic_shipment_types = {
        'Priority Commercial': 'Priority',
        'Priority HFP Commercial': 'Priority',
        'Express Commercial': 'Express',
        'Express SH': 'Express',
        'Express SH Commercial': 'Express',
        'Express HFP': 'Express',
        'Express HFP Commercial': 'Express',
        'First Class': 'First',
        'First Class HFP Commercial': 'First',
        'Library': 'LibraryMail',
        'Media': 'MediaMail',
        'ParcelPost': 'ParcelPost',
        'ParcelSelect': 'ParcelSelect',
        'Standard Mail Class': 'StandardMailClass',
    }

    international_shipment_types = {
        'ExpressMailInternational': 'ExpressMailInternational',
        'FirstClassMailInternational': 'FirstClassMailInternational',
        'PriorityMailInternational': 'PriorityMailInternational',
    }

    shapes = {
        'Parcel':'Parcel',
        'Card': 'Card',
        'Letter': 'Letter',
        'Flat': 'Flat',
        'Large Parcel': 'LargeParcel',
        'Irregular Parcel': 'IrregularParcel',
        'Oversized Parcel': 'OversizedParcel',
        'Flat Rate Envelope': 'FlatRateEnvelope',
        'Legal Flat Rate Envelope': 'FlatRateLegalEnvelope',
        'Padded Flat Rate Envelope': 'FlatRatePaddedEnvelope',
        'Gift Card Flat Rate Envelope': 'FlatRateGiftCardEnvelope',
        'Window Flat Rate Envelope': 'FlatRateWindowEnvelope',
        'Cardboard Flat Rate Envelope': 'FlatRateCardboardEnvelope',
        'SM Flat Rate Envelope': 'SmallFlatRateEnvelope',
        'SM Flat Rate Box': 'SmallFlatRateBox',
        'MD Flat Rate Box': 'MediumFlatRateBox',
        'LG Flat Rate Box': 'LargeFlatRateBox',
        'RegionalRateBoxA': 'RegionalRateBoxA',
        'RegionalRateBoxB': 'RegionalRateBoxB',
    }

    def __init__(self, mail_class, weight_in_ozs, length, width, height, value=0, require_signature=False, reference=u''):
        self.mail_class = self.domestic_shipment_types.get(mail_class) and self.domestic_shipment_types[mail_class] or self.international_shipment_types.get(mail_class) and self.international_shipment_types[mail_class] or mail_class
        self.weight = weight_in_ozs / 16 if float(weight_in_ozs) >= 1.0 else (1.0/16.0)
        self.length = length
        self.width = width
        self.height = height
        self.value = value
        self.require_signature = require_signature
        self.reference = reference
    
    @property
    def weight_in_ozs(self):
        return self.weight * 16

    @property
    def weight_in_lbs(self):
        return self.weight

class Address(object):
    def __init__(self, name, address, city, state, zip, country, address2='', phone='', email='', is_residence=True, company_name=''):
        self.company_name = company_name or ''
        self.name = name or ''
        self.address1 = address or ''
        self.address2 = address2 or ''
        self.city = city or ''
        self.state = state or ''
        self.zip = str(zip).split('-')[0] if zip else ''
        self.country = country or ''
        self.phone = re.sub('[^0-9]*', '', str(phone)) if phone else ''
        self.email = email or ''
        self.is_residence = is_residence or False
    
    def __eq__(self, other):
        return vars(self) == vars(other)
    
    def __repr__(self):
        street = self.address1
        if self.address2:
            street += '\n' + self.address2
        return '%s\n%s\n%s, %s %s %s' % (self.name, street, self.city, self.state, self.zip, self.country)

def get_country_code(country):
    lookup = {
        'us': 'US',
        'usa': 'US',
        'united states': 'US',
    }

    return lookup.get(country.lower(), country)
