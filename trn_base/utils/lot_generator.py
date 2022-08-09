from datetime import date
from odoo.http import request


def add_zeros(init, to):
    return ''.join(['0' for i in range(init, to)])


def reset_series(now):
    return add_zeros(1, 5) + '1-' + now.strftime('%y%m%d')


def generate_lot(current_lot=None):
    now = date.today()

    if current_lot is None:
        return reset_series(now)

    if current_lot:
        lots = current_lot.split('-')
        year = lots[1]
        if year[0:2] != now.strftime('%y'):
            return reset_series(now)
        sequence = lots[0]
        sequence = int(sequence) + 1
        max_length = len(str(sequence)) + 1 if len(str(sequence)) > 5 else 5

        next_lot = add_zeros(len(str(sequence)), max_length)

        next_lot += f'{str(sequence)}-{now.strftime("%y%m%d")}'

        return next_lot


def get_last_lot():
    now = date.today()
    last_lot = \
        request.env['stock.production.lot'].sudo().search([('is_auto_lot', '=', True)]).sorted(key=lambda x: x.id,
                                                                                               reverse=True)
    if last_lot:
        last_lot = last_lot.filtered(
            lambda x: len(x.name.split('-')) == 2)[0]
        lot = last_lot.name
        if len(lot.split('-')) == 2:
            lot_id = request.env['stock.production.lot'].search([('name', '=', generate_lot(lot))])
            if lot_id:
                last_lot = request.env['stock.production.lot'].sudo().search([]).sorted(key=lambda x: x.id,
                                                                                        reverse=True).filtered(
                    lambda x: len(x.name.split('-')) == 2 and x.name != lot)[0]
                if last_lot:
                    lot = last_lot.name
                    if len(lot.split('-')) == 2:
                        return generate_lot(lot)
            else:
                return generate_lot(lot)
    return generate_lot()
