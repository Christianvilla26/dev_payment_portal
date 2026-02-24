# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from odoo import models, fields, api, _


class AccountPayment(models.Model):
    _name = 'account.payment'
    _inherit = ['account.payment', 'portal.mixin']

    def _get_report_base_filename(self):
        self.ensure_one()
        return '%s %s' % (_('Payment'), self.name)

    def _compute_access_url(self):
        super()._compute_access_url()
        for payment in self:
            payment.access_url = '/my/payment/%s' % payment.id
