from odoo import models, fields, api


class GroupAdministration(models.Model):
	_name = 'group.administration'
	_description = 'Administración de Grupos'
	
	group_id = fields.Many2one('res.groups', string='Grupo', help="Grupo a administrar", required=True)
	
	user_ids = fields.Many2many('res.users', string='Usuarios', help="Usuarios")
	
	name = fields.Char('Nombre', required=True)
	
	@api.model
	def create(self, vals_list):
		res = super(GroupAdministration, self).create(vals_list)
		if res.group_id:
			res.group_id.write({
				'users': [(6, 0, [user.id for user in res.user_ids])],
				'admin_group_id': res.id,
			})
		return res
	
	def write(self, vals_list):
		res = super(GroupAdministration, self).write(vals_list)
		for item in self:
			if not item.env.su:
				if item.user_ids != item.group_id.users:
					item.group_id.write({
						'users': [(6, 0, [user.id for user in item.user_ids])]
					})
		return res
