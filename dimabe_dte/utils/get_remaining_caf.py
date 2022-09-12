from odoo.http import request
from .generate_notification import send_notification

def get_remaining_caf(dte_type):
    document_type_id = request.env['l10n_latam.document.type'].search([('id', '=', dte_type), ('active', '=', True)])
    if document_type_id.remaining_caf <= document_type_id.env.user.company_id.notification_remaining_caf:
        user_group = request.env.ref('dimabe_dte.custom_remaining_caf_notification')

        body = f'<p>Estimados.<br/><br/> Quedan {document_type_id.remaining_caf} folios de {document_type_id.name}'
        subject = f'Folios disponibles - {document_type_id.name}'

        send_notification(subject, body, 2, user_group.users, 'l10n_latam.document.type', document_type_id.id)

