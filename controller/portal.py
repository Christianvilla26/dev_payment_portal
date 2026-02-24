# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from collections import OrderedDict
from datetime import date, datetime, timedelta
from operator import itemgetter

from odoo import fields, http, _
from odoo.addons.portal.controllers.portal import CustomerPortal, get_records_pager, pager as portal_pager
from odoo.http import request
from odoo.osv import expression
from odoo.tools import groupby as groupbyelem
from dateutil.relativedelta import relativedelta


class PaymentPortal(CustomerPortal):
    """Portal for account.payment: list and (optionally) detail for portal users."""

    def _get_payment_domain(self):
        """Domain for payments visible by current portal user (posted only)."""
        return [
            ('partner_id', '=', request.env.user.partner_id.id),
            ('move_id.state', '=', 'posted'),
        ]

    def _prepare_portal_layout_values(self):
        values = super()._prepare_portal_layout_values()
        payment_count = request.env['account.payment'].sudo().search_count(self._get_payment_domain())
        values['payment_count'] = payment_count
        # Subtitle for portal card: "1 pago" / "X pagos"
        values['payment_count_label'] = _('1 pago') if payment_count == 1 else _('%s pagos') % payment_count
        return values

    def _prepare_home_portal_values(self, counters):
        """Odoo 17: counters for portal home cards (e.g. payment count)."""
        values = super()._prepare_home_portal_values(counters)
        if 'payment' in counters:
            payment_count = request.env['account.payment'].sudo().search_count(self._get_payment_domain())
            values['payment_count'] = payment_count
            values['payment_count_label'] = _('1 pago') if payment_count == 1 else _('%s pagos') % payment_count
        return values

    @http.route(['/my/payment', '/my/payment/page/<int:page>'], type='http', auth='user', website=True)
    def portal_my_payment(self, page=1, date_begin=None, date_end=None, sortby=None, filterby=None,
                          groupby='none', search=None, search_in='content', **kw):
        values = self._prepare_portal_layout_values()
        payment_pool = request.env['account.payment'].sudo()
        domain = self._get_payment_domain()

        searchbar_sortings = {
            'date': {'label': _('Payment Date'), 'order': 'date desc'},
            'name': {'label': _('Name'), 'order': 'name desc'},
        }
        searchbar_groupby = {
            'none': {'input': 'none', 'label': _('All')},
            'partner_id': {'input': 'partner_id', 'label': _('Partner')},
            'company_id': {'input': 'company_id', 'label': _('Company')},
        }

        today = fields.Date.today()
        this_week_end_date = fields.Date.to_string(today + timedelta(days=7))
        week_ago = datetime.today() - timedelta(days=7)
        month_ago = (datetime.today() - relativedelta(months=1)).strftime('%Y-%m-%d %H:%M:%S')
        starting_of_year = datetime.now().date().replace(month=1, day=1)
        ending_of_year = datetime.now().date().replace(month=12, day=31)

        def sd(d):
            return fields.Datetime.to_string(d)

        def previous_week_range(d):
            start_date = d + timedelta(days=-d.weekday(), weeks=-1)
            end_date = d + timedelta(days=-d.weekday() - 1)
            return {'start_date': start_date.strftime('%Y-%m-%d %H:%M:%S'), 'end_date': end_date.strftime('%Y-%m-%d %H:%M:%S')}

        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'today': {'label': _('Today'), 'domain': [
                ('date', '>=', date.today().strftime('%Y-%m-%d')),
                ('date', '<=', date.today().strftime('%Y-%m-%d')),
            ]},
            'yesterday': {'label': _('Yesterday'), 'domain': [
                ('date', '>=', (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')),
                ('date', '<=', (date.today() - timedelta(days=1)).strftime('%Y-%m-%d')),
            ]},
            'week': {'label': _('This Week'), 'domain': [
                ('date', '>=', sd(datetime.today() + relativedelta(days=-today.weekday()))),
                ('date', '<=', this_week_end_date),
            ]},
            'last_seven_days': {'label': _('Last 7 Days'), 'domain': [
                ('date', '>=', sd(week_ago)), ('date', '<=', sd(datetime.today())),
            ]},
            'last_week': {'label': _('Last Week'), 'domain': [
                ('date', '>=', previous_week_range(datetime.today())['start_date']),
                ('date', '<=', previous_week_range(datetime.today())['end_date']),
            ]},
            'last_month': {'label': _('Last 30 Days'), 'domain': [
                ('date', '>=', month_ago), ('date', '<=', sd(datetime.today())),
            ]},
            'month': {'label': _('This Month'), 'domain': [
                ('date', '>=', sd(today.replace(day=1))),
                ('date', '<', (today.replace(day=1) + relativedelta(months=1)).strftime('%Y-%m-%d 00:00:00')),
            ]},
            'year': {'label': _('This Year'), 'domain': [
                ('date', '>=', sd(starting_of_year)), ('date', '<=', sd(ending_of_year)),
            ]},
        }

        filterby = filterby or 'all'
        domain = expression.AND([domain, searchbar_filters[filterby]['domain']])

        sortby = sortby or 'date'
        sort_order = searchbar_sortings[sortby]['order']

        if date_begin and date_end:
            domain = expression.AND([domain, [
                ('create_date', '>', date_begin), ('create_date', '<=', date_end),
            ]])

        searchbar_inputs = {
            'name': {'input': 'name', 'label': _('Number')},
            'payment_reference': {'input': 'payment_reference', 'label': _('Reference')},
            'all': {'input': 'all', 'label': _('All')},
        }

        if search and search_in:
            search_dom = []
            if search_in in ('name', 'all'):
                search_dom = expression.OR([search_dom, [('name', 'ilike', search)]])
            if search_in in ('payment_reference', 'all'):
                search_dom = expression.OR([search_dom, [('payment_reference', 'ilike', search)]])
            if search_dom:
                domain = expression.AND([domain, search_dom])

        payment_count = payment_pool.search_count(domain)
        pager = portal_pager(
            url='/my/payment',
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby,
                      'search_in': search_in, 'search': search, 'filterby': filterby, 'groupby': groupby},
            total=payment_count,
            page=page,
            step=self._items_per_page,
        )
        payment = payment_pool.search(domain, order=sort_order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_payment_history'] = payment.ids[:100]

        if groupby == 'partner_id':
            grouped_payment = [request.env['account.payment'].concat(*g) for k, g in groupbyelem(payment, itemgetter('partner_id'))]
        elif groupby == 'company_id':
            grouped_payment = [request.env['account.payment'].concat(*g) for k, g in groupbyelem(payment, itemgetter('company_id'))]
        else:
            grouped_payment = [payment]

        values.update({
            'date': date_begin,
            'payment': payment,
            'page_name': 'payment',
            'grouped_payment': grouped_payment,
            'pager': pager,
            'default_url': '/my/payment',
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'searchbar_sortings': searchbar_sortings,
            'searchbar_groupby': searchbar_groupby,
            'filterby': filterby,
            'sortby': sortby,
            'groupby': groupby,
            'searchbar_inputs': searchbar_inputs,
            'search_in': search_in or 'all',
            'search': search,
        })
        return request.render('dev_payment_portal.portal_my_payment', values)

    @http.route(['/my/payment/<int:payment_id>'], type='http', auth='user', website=True)
    def portal_payment_page(self, payment_id, message=False, **kw):
        """Detail of a single payment for the current portal user."""
        partner = request.env.user.partner_id
        payment = request.env['account.payment'].sudo().browse(payment_id)
        if not payment.exists() or payment.partner_id != partner or payment.move_id.state != 'posted':
            return request.redirect('/my/payment')
        history = request.session.get('my_payment_history', [])
        values = {
            'payment': payment,
            'message': message,
            'p_name': payment.name,
            'report_type': 'html',
        }
        values.update(get_records_pager(history, payment))
        return request.render('dev_payment_portal.payment_portal_template', values)
