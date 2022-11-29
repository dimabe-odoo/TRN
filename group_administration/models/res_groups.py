from odoo import models, fields


class ResGroups(models.Model):
	_inherit = 'res.groups'
	
	admin_group_id = fields.Many2one('group.administration', string='Administracion de Grupo')
	
	def write(self, vals_list):
		res = super(ResGroups, self).write(vals_list)
		for item in self:
			if not item.env.su and item.admin_group_id:
				if item.users != item.admin_group_id.user_ids:
					item.admin_group_id.write({
						'user_ids': [(6, 0, [user.id for user in item.users])]
					})
			if item.env.su and item.admin_group_id:
				if item.users != item.admin_group_id.user_ids:
					item.write({
						'users': [(6, 0, [user.id for user in item.admin_group_id.user_ids])]
					})
		return res
