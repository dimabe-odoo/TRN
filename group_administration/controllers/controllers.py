# -*- coding: utf-8 -*-
# from odoo import http


# class GroupAdministration(http.Controller):
#     @http.route('/group_administration/group_administration', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/group_administration/group_administration/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('group_administration.listing', {
#             'root': '/group_administration/group_administration',
#             'objects': http.request.env['group_administration.group_administration'].search([]),
#         })

#     @http.route('/group_administration/group_administration/objects/<model("group_administration.group_administration"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('group_administration.object', {
#             'object': obj
#         })
