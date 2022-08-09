# -*- coding: utf-8 -*-
# from odoo import http


# class TrnBase(http.Controller):
#     @http.route('/trn_base/trn_base', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/trn_base/trn_base/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('trn_base.listing', {
#             'root': '/trn_base/trn_base',
#             'objects': http.request.env['trn_base.trn_base'].search([]),
#         })

#     @http.route('/trn_base/trn_base/objects/<model("trn_base.trn_base"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('trn_base.object', {
#             'object': obj
#         })
