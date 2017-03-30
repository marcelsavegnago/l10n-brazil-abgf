# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models

from ..models.financial_move import (
    FINANCIAL_MOVE,
)


class FinancialMoveCreate(models.TransientModel):
    _name = 'financial.move.create'
    _inherit = ['account.abstract.payment']

    @api.depends('amount', 'amount_discount')
    def _compute_totals(self):
        for record in self:
            record.amount_total = record.amount - record.amount_discount

    payment_type = fields.Selection(
        required=False,
    )
    payment_method_id = fields.Many2one(
        required=False,
    )
    line_ids = fields.One2many(
        comodel_name='financial.move.line.create',
        inverse_name='financial_move_id',
        # readonly=True,
    )
    financial_type = fields.Selection(
        selection=FINANCIAL_MOVE,
        required=True,
    )
    payment_mode_id = fields.Many2one(
        comodel_name='account.payment.mode', string="Payment Mode",
        ondelete='restrict',
    )
    payment_term_id = fields.Many2one(
        string='Payment Term',
        comodel_name='account.payment.term',
    )
    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string=u'Analytic account',
    )
    account_id = fields.Many2one(
        comodel_name='account.account',
        string=u'Account',
        required=True,
        domain=[('internal_type', '=', 'other')],
        help="The partner account used for this invoice."
    )
    document_number = fields.Char(
        string=u"Document Nº",
        required=True,
    )
    date = fields.Date(
        string=u'Financial date',
        default=fields.Date.context_today,
    )
    amount_total = fields.Monetary(
        string=u'Total',
        readonly=True,
        compute='_compute_totals',
    )
    amount_discount = fields.Monetary(
        string=u'Discount',
    )
    note = fields.Text(
        string="Note",
    )
    journal_id = fields.Many2one(
        required=False,
    )
    bank_id = fields.Many2one(
        'res.partner.bank',
        string=u'Bank Account',
    )
    payment_mode_domain = fields.Char(
        compute='_mount_domain'
    )
    payment_term_domain = fields.Char(
        compute='_mount_domain'
    )

    @api.onchange('payment_term_id', 'document_number',
                  'date', 'amount')
    def onchange_fields(self):
        res = {}
        if not (self.payment_term_id and self.document_number and self.date
                and self.amount > 0.00):
            return res

        computations = \
            self.payment_term_id.compute(self.amount, self.date)

        payment_ids = []
        for idx, item in enumerate(computations[0]):
            payment = dict(
                document_item=self.document_number + '/' + str(idx + 1),
                date_maturity=item[0],
                amount=item[1],
            )
            payment_ids.append((0, False, payment))
        self.line_ids = payment_ids

    @api.multi
    def compute(self):
        financial_move = self.env['financial.move'].create_contract(self)
        financial_type = financial_move and financial_move[0].financial_type
        return financial_move.action_view_financial(financial_type)

    @api.depends('payment_mode_id', 'payment_term_id', 'amount_total',
                 'partner_id', 'financial_type')
    def _mount_domain(self):
        if self.financial_type == 'receivable':
            payment_mode_ids = []
            payment_term_ids = []
            mode = self.env['account.payment.mode'].search([
                ('liquidity', '=', False)])
            payment_mode_ids.extend(mode.ids)

            term = self.env['account.payment.term'].search([
                ('installments', '=', False)])
            payment_term_ids.extend(term.ids)

            if self.amount_total <= self.partner_id.available_credit_limit:
                mode = self.env['account.payment.mode'].search([
                    ('liquidity', '=', True)])
                payment_mode_ids.extend(mode.ids)
                term = self.env['account.payment.term'].search([
                    ('installments', '=', True)])
                payment_term_ids.extend(term.ids)

            term_domain = "[('id','in',(%s))]" % ''.join(str(e) + ',' for e in
                                                         payment_term_ids)
            mode_domain = "[('id','in',(%s))]" % ''.join(str(e) + ',' for e in
                                                         payment_term_ids)

            # self.payment_term_domain = ''.join(str(e)+','
            # for e in payment_term_ids)
            # self.payment_mode_domain = ''.join(str(e)+','
            # for e in payment_mode_ids)
            payment_term_domain = term_domain
            payment_mode_domain = mode_domain

            for pay in payment_term_ids:
                pay.write(
                {'domain': payment_term_domain})
            for mode in payment_mode_ids:
                mode.write(
                {'domain': payment_mode_domain})
            return {'payment_term_id': payment_term_domain,
                    'payment_mode_id': payment_mode_domain}


class FinancialMoveLineCreate(models.TransientModel):
    _name = 'financial.move.line.create'

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string=u'Currency',
    )

    document_item = fields.Char(
        string=u"Document item",
    )

    date = fields.Date(
        string=u"Document date",
    )

    date_maturity = fields.Date(
        string=u"Due date",
    )

    amount = fields.Monetary(
        string=u"Document amount",
    )

    financial_move_id = fields.Many2one(
        comodel_name='financial.move.create',
        required=True
    )
