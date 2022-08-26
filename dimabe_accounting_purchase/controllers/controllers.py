# -*- coding: utf-8 -*-
# from odoo import http


# class DimabeAccountingPurchase(http.Controller):
#     @http.route('/dimabe_accounting_purchase/dimabe_accounting_purchase', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/dimabe_accounting_purchase/dimabe_accounting_purchase/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('dimabe_accounting_purchase.listing', {
#             'root': '/dimabe_accounting_purchase/dimabe_accounting_purchase',
#             'objects': http.request.env['dimabe_accounting_purchase.dimabe_accounting_purchase'].search([]),
#         })

#     @http.route('/dimabe_accounting_purchase/dimabe_accounting_purchase/objects/<model("dimabe_accounting_purchase.dimabe_accounting_purchase"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('dimabe_accounting_purchase.object', {
#             'object': obj
#         })
