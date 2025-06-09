# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from collections import OrderedDict
from odoo import fields, http, _
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from odoo.addons.portal.controllers.mail import _message_post_helper
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager, get_records_pager
from odoo.osv import expression
import werkzeug
from datetime import datetime, date
from odoo.tools import groupby as groupbyelem
from operator import itemgetter
from odoo.tools import float_compare
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo.osv.expression import OR


class CustomerPortal(CustomerPortal):

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        payment_pool = request.env['account.payment']
        data = request.env.user.partner_id.id
        payment_count = payment_pool.sudo().search_count([
            ('partner_id', '=',request.env.user.partner_id.id )
        ])
        values.update({
            'payment_count': payment_count,
        })
        return values
    
    
    @http.route(['/my/payment', '/my/payment/page/<int:page>'], type='http', auth="user", website=True)
    def portal_my_payment(self, page=1, date_begin=None, date_end=None, sortby=None,filterby=None,groupby='none',search=None,search_in='content', **kw):
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id
        payment_pool = request.env['account.payment']

        domain = [
            ('partner_id', '=',request.env.user.partner_id.id )
        ]
        

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
        this_week_end_date = fields.Date.to_string(fields.Date.from_string(today) + timedelta(days=7))
        week_ago = datetime.today() - timedelta(days=7)
        month_ago = (datetime.today() - relativedelta(months=1)).strftime('%Y-%m-%d %H:%M:%S')
        starting_of_year = datetime.now().date().replace(month=1, day=1)    
        ending_of_year = datetime.now().date().replace(month=12, day=31)

        def sd(date):
            return fields.Datetime.to_string(date)
        def previous_week_range(date):
            start_date = date + timedelta(-date.weekday(), weeks=-1)
            end_date = date + timedelta(-date.weekday() - 1)
            return {'start_date':start_date.strftime('%Y-%m-%d %H:%M:%S'), 'end_date':end_date.strftime('%Y-%m-%d %H:%M:%S')}
        
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
            'today': {'label': _('Today'), 'domain': [('date', '>=', datetime.strftime(date.today(),'%Y-%m-%d 00:00:00')),('date', '<=', datetime.strftime(date.today(),'%Y-%m-%d 23:59:59'))]},
            'yesterday':{'label': _('Yesterday'), 'domain': [('date', '>=', datetime.strftime(date.today() - timedelta(days=1),'%Y-%m-%d 00:00:00')),('date', '<=', datetime.strftime(date.today(),'%Y-%m-%d 23:59:59'))]},
            'week': {'label': _('This Week'),
                     'domain': [('date', '>=', sd(datetime.today() + relativedelta(days=-today.weekday()))), ('date', '<=', this_week_end_date)]},
            'last_seven_days':{'label':_('Last 7 Days'),
                         'domain': [('date', '>=', sd(week_ago)), ('date', '<=', sd(datetime.today()))]},
            'last_week':{'label':_('Last Week'),
                         'domain': [('date', '>=', previous_week_range(datetime.today()).get('start_date')), ('date', '<=', previous_week_range(datetime.today()).get('end_date'))]},
            
            'last_month':{'label':_('Last 30 Days'),
                         'domain': [('date', '>=', month_ago), ('date', '<=', sd(datetime.today()))]},
            'month':{'label': _('This Month'),
                    'domain': [
                       ("date", ">=", sd(today.replace(day=1))),
                       ("date", "<", (today.replace(day=1) + relativedelta(months=1)).strftime('%Y-%m-%d 00:00:00'))
                    ]
                },
            'year':{'label': _('This Year'),
                    'domain': [
                       ("date", ">=", sd(starting_of_year)),
                       ("date", "<=", sd(ending_of_year)),
                    ]
                }
        }
        if not filterby:
            filterby = 'all'
        domain += searchbar_filters[filterby]['domain']     
        
        # default sortby order
        if not sortby:
            sortby = 'date'
        sort_order = searchbar_sortings[sortby]['order']
        
#        archive_groups = self._get_archive_groups('account.payment')
        if date_begin and date_end:
            domain += [('create_date', '>', date_begin), ('create_date', '<=', date_end)]
        # count for pager
        payment_count = payment_pool.search_count(domain)


        searchbar_inputs = {
            'name': {'input': 'name', 'label': _('Search in Number')},
			'destination_account_id': {'input': 'destination_account_id', 'label': _('Search in Destination Account')},
			'company_id': {'input': 'company_id', 'label': _('Search in Company')},
			'state': {'input': 'state', 'label': _('Search in State')},
			'journal_id': {'input': 'journal_id', 'label': _('Search in Journal')},
            'all': {'input': 'all', 'label': _('Search in All')},
        }

        # search
        if search and search_in:
            search_domain = []
            if search_in in ('name', 'all'):
                search_domain = OR([search_domain, [('name', 'ilike', search)]])
            if search_in in ('destination_account_id', 'all'):
                search_domain = OR([search_domain, [('destination_account_id', 'ilike', search)]])
            if search_in in ('company_id', 'all'):
                search_domain = OR([search_domain, [('company_id', 'ilike', search)]])
            if search_in in ('journal_id', 'all'):
                search_domain = OR([search_domain, [('journal_id', 'ilike', search)]])
            if search_in in ('state', 'all'):
                search_domain = OR([search_domain, [('state', 'ilike', search)]])
            domain += search_domain

        # make pager
        pager = portal_pager(
            url="/my/payment",
            url_args={'date_begin': date_begin, 'date_end': date_end, 'sortby': sortby,'search_in': search_in,'search': search},
            total=payment_count,
            page=page,
            step=self._items_per_page
        )
        # search the count to display, according to the pager data
        payment = payment_pool.sudo().search(domain, order=sort_order, limit=self._items_per_page, offset=pager['offset'])
        request.session['my_payment_history'] = payment.ids[:100]
        if groupby == 'partner_id':
            grouped_payment = [request.env['account.payment'].concat(*g) for k, g in groupbyelem(payment, itemgetter('partner_id'))]
        elif groupby == 'company_id':
            grouped_payment = [request.env['account.payment'].concat(*g) for k, g in groupbyelem(payment, itemgetter('company_id'))]
        else:
            grouped_payment = [payment]
        


        values.update({
            'date': date_begin,
            'payment': payment.sudo(),
            'page_name': 'payment',
            'grouped_payment': grouped_payment,
            'pager': pager,
#            'archive_groups': archive_groups,
            'default_url': '/my/payment',
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
            'searchbar_sortings': searchbar_sortings,
            'searchbar_groupby':searchbar_groupby,
            'filterby': filterby,
            'sortby': sortby,
            'groupby': groupby,
			'searchbar_inputs': searchbar_inputs,
			'search_in': search_in,
			'search': search,
        })
        return request.render("dev_payment_portal.portal_my_payment", values)


    # @http.route(['/my/payment/<int:order_id>'], type='http', auth="public", website=True)
    # def portal_payment_page(self, order_id, report_type=None, access_token=None, message=False, download=False, **kw):
    #     try:
    #         account_payment_sudo = self._document_check_access('account.payment', order_id, access_token=access_token) 
    #     except (AccessError, MissingError):
    #         return request.redirect('/my')
    #     now = fields.Date.today()
    #     if report_type in ('html', 'pdf', 'text'):
    #         return self._show_report(model=account_payment_sudo, report_type=report_type, report_ref='account.action_report_payment_receipt', download=download)
    #     if account_payment_sudo and request.session.get('view_payment_%s' % account_payment_sudo.id) != now and request.env.user.share and access_token:
    #         request.session['view_rma_%s' % account_payment_sudo.id] = now
    #         body = _('Leave viewed by customer')
    #         _message_post_helper(res_model='account.payment', res_id=account_payment_sudo.id, message=body, token=account_payment_sudo.access_token, message_type='notification', subtype="mail.mt_note", partner_ids=account_payment_sudo.user_id.sudo().partner_id.ids)
    #     values = {
    #         'payment': account_payment_sudo,
    #         'message': message,
    #         'token': access_token,
    #         'bootstrap_formatting': True,
    #         'report_type': 'html',
	# 		'p_name':account_payment_sudo.name,
			
		
    #     }
    #     if account_payment_sudo.company_id:
    #         values['res_company'] = account_payment_sudo.company_id
    #     if account_payment_sudo.name:
    #         history = request.session.get('my_contact_history', [])
    #     values.update(get_records_pager(history, account_payment_sudo))
    #     return request.render('dev_payment_portal.payment_portal_template', values)



    # RMA
