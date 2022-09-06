from odoo.http import request
from py_linq import Enumerable

def send_notification(subject, body, author_id, user_group, model, model_id):
    if Enumerable(user_group).any(lambda x: isinstance(x, int)):
        partner_list = user_group
    else:
        partner_list = [
            usr.partner_id.id for usr in user_group if usr.partner_id
        ]

    mail_message = request.env['mail.message'].sudo().create({
        'subject': subject,
        'author_id': author_id,
        'body': body,
        'partner_ids': partner_list,
        'message_type': 'notification',
        'model': model,
        'res_id': model_id,
    })

    for user in user_group:
        if isinstance(user, int):
            partner_id = user
            notification_type = request.env['res.users'].search([('partner_id', '=', user)]).notification_type
        else:
            partner_id = user.partner_id.id
            notification_type = user.notification_type
        request.env['mail.notification'].sudo().create({
            'mail_message_id': mail_message.id,
            'res_partner_id': partner_id,
            'notification_type': notification_type,
            'notification_status': 'ready'
        })


def get_followers(model_name, record_id):
    followers = request.env[model_name].sudo().search([('id', '=', record_id)]).message_follower_ids
    list_followers = []
    for follower in followers:
        user = request.env['res.users'].sudo().search([('partner_id', '=', follower.partner_id.id)])
        if user:
            list_followers.append(user)
    return list_followers
