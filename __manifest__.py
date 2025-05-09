# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

{
    'name': 'Portal Payment- Website',
    'version': '15.0.1.0',
    'sequence': 1,
    'category': 'Website',
    'description':
        """
 Website Payment Portal
Portal Payment to allow portal user to see payment,view payment, Portal Payment filter, Portal Payment filter by date,company, partner website, Access portal payment website,website payment details portal,Website Portal payment full details

    """,
    'summary': 'Portal Payment to allow portal user to see payment,view payment, Portal Payment filter, Portal Payment filter by date,company, partner website, Access portal payment website,website payment details portal,Website Portal payment full details',
    'depends': ['portal','website','account'],
    'data': [
        'security/ir.model.access.csv',
        'views/payment_portal_templates.xml',
        ],
    'demo': [],
    'test': [],
    'css': [],
    'qweb': [],
    'js': [],
    'images': ['images/main_screenshot.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
    
    # author and support Details =============#
    'author': 'DevIntelle Consulting Service Pvt.Ltd',
    'website': 'http://www.devintellecs.com',    
    'maintainer': 'DevIntelle Consulting Service Pvt.Ltd', 
    'support': 'devintelle@gmail.com',
    'price':29.0,
    'currency':'EUR',
    #'live_test_url':'https://youtu.be/A5kEBboAh_k',
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
