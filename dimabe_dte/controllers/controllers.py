# -*- coding: utf-8 -*-
# from odoo import http


# class DimabeDte(http.Controller):
#     @http.route('/dimabe_dte/dimabe_dte/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/dimabe_dte/dimabe_dte/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('dimabe_dte.listing', {
#             'root': '/dimabe_dte/dimabe_dte',
#             'objects': http.request.env['dimabe_dte.dimabe_dte'].search([]),
#         })

#     @http.route('/dimabe_dte/dimabe_dte/objects/<model("dimabe_dte.dimabe_dte"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('dimabe_dte.object', {
#             'object': obj
#         })
