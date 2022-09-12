from odoo import models, api
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class L10nClDailySalesBook(models.Model):

    _inherit = 'l10n_cl.daily.sales.book'

    @api.model
    def _cron_run_sii_sales_book_report_process_by_date(self, date):
        for company in self.env['res.company'].search([('partner_id.country_id.code', '=', 'CL')]):
            self_skip = self.with_company(company=company.id).with_context(cron_skip_connection_errs=True)
            books = self_skip._create_month_calendar_report_by_date(date)
            self.env.cr.commit()
            books._l10n_cl_send_books_to_sii()
            self_skip._send_pending_sales_book_report_to_sii()


    def _create_month_calendar_report_by_date(self, date):
        if not date:
            raise models.ValidationError('Debe ingresar la fecha')
        now_date = datetime.strptime(date, '%d%m%Y').date()
        books = self.env['l10n_cl.daily.sales.book']
        # Create the month calendar report if not exists until the day before yesterday
        for day in range(1, now_date.day - 1):
            new_date = now_date.replace(day=day)
            if not self._get_report_by_date(new_date):
                books |= self._create_report(new_date)
        # Yesterday report must be created
        yesterday = now_date + timedelta(days=-1)
        yesterday_book = self._get_report_by_date(yesterday)
        if not yesterday_book:
            yesterday_book = self._create_report(yesterday)
        books |= yesterday_book

        return books

    @api.model
    def _create_report(self, date):
        move_ids = self._get_move_ids_without_daily_sales_book_by_date(date)
        report = self.create({'date': date})
        account_move_ids = self.env['account.move'].search([('id', 'in', move_ids)])
        for move in account_move_ids:
            move.write({
                'l10n_cl_daily_sales_book_id': report.id
            })
        report._create_dte()
        return report

    def _update_report(self):
        if self.l10n_cl_dte_status == 'ask_for_status':
            _logger.info(
                'Sales Book for day %s has not been updated due to the current status is ask for status.' % self.date)
            return None
        move_ids = self.move_ids.ids + self._get_move_ids_without_daily_sales_book_by_date(self.date)
        self.write({'send_sequence': self.send_sequence + 1, 'move_ids': [(6, 0, move_ids)]})
        self._create_dte()