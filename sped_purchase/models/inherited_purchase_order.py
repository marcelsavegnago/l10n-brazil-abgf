# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.addons.sped_imposto.models.sped_calculo_imposto import (
    SpedCalculoImposto
)
from odoo.addons.sped_imposto.models.sped_calculo_imposto_produto_servico \
    import SpedCalculoImpostoProdutoServico
from odoo.addons.l10n_br_base.constante_tributaria \
    import SITUACAO_FISCAL_SPED_CONSIDERA_ATIVO


class PurchaseOrder(SpedCalculoImpostoProdutoServico, models.Model):
    _inherit = 'purchase.order'

    item_ids = fields.One2many(
        comodel_name='purchase.order.line',
        inverse_name='order_id',
        related='order_line',
    )

    operacao_id = fields.Many2one(
        comodel_name='sped.operacao',
        related='operacao_produto_id',
    )

    operacao_produto_id = fields.Many2one(
        comodel_name='sped.operacao'
    )

    operacao_servico_id = fields.Many2one(
        comodel_name='sped.operacao'
    )

    quantidade_documentos = fields.Integer(
        compute='_compute_invoice',
        string='# de documentos',
        copy=False,
        default=0,
        store=True
    )

    documento_ids = fields.Many2many(
        comodel_name='sped.documento',
        compute='_compute_documento',
        string='Faturas de Fornecedor',
        relation='purchase_order_sped_documento_rel',
        copy=False,
        store=True
    )

    state = fields.Selection(
        selection_add=[('invoiced', 'Faturado pelo Fornecedor'),
                       ('received', 'Recebido')],
        # group_expand='_read_group_stage_ids', FIXME: func. v11
        readonly=False,
    )

    order_line_count = fields.Integer(
        compute='_compute_order_line_count'
    )

    @api.depends('order_line')
    def _compute_order_line_count(self):
        for pedido in self:
            pedido.order_line_count = len(pedido.order_line)

    # @api.model FIXME: func. v11
    # def _read_group_stage_ids(self, values, domain, order):
    #     return ['draft', 'purchase', 'invoiced', 'received']

    @api.model
    def _prepare_picking(self):
        res = super(PurchaseOrder, self)._prepare_picking()
        res['operacao_id'] = self.operacao_produto_id.id
        res['state'] = 'confirmed'
        return res

    def _get_date(self):
        """
        Return the document date
        Used in _amount_all_wrapper
        """
        return self.date_order

    @api.one
    @api.depends(
        'order_line.price_total',
        #
        # Campos Brasileiros
        #
        'order_line.vr_nf',
        'order_line.vr_fatura',
    )
    def _amount_all(self):
        if not self.is_brazilian:
            return super(PurchaseOrder, self)._amount_all()
        dados = {
            'amount_untaxed': self.vr_operacao,
            'amount_tax': self.vr_nf - self.vr_operacao,
            'amount_total': self.vr_fatura,
        }
        self.update(dados)

    @api.depends('company_id', 'partner_id')
    def _compute_is_brazilian(self):
        for documento in self:
            if not documento.company_id:
                documento.is_brazilian = True
            else:
                super(PurchaseOrder, self)._compute_is_brazilian()

    def prepara_dados_documento(self):
        self.ensure_one()

        return {
            'purchase_order_ids': [(4, self.id)],
        }

    @api.depends('documento_ids.situacao_fiscal')
    def _compute_quantidade_documentos_fiscais(self):
        for purchase in self:
            documento_ids = self.env['sped.documento'].search(
                [('purchase_id', '=', purchase.id),
                 ('situacao_fiscal', 'in',
                  SITUACAO_FISCAL_SPED_CONSIDERA_ATIVO)])

            purchase.quantidade_documentos = len(documento_ids)

    @api.depends('order_line.documento_item_ids.documento_id')
    def _compute_documento(self):
        for ordem in self:
            documentos = self.env['sped.documento']
            for linha in ordem.order_line:
                documentos |= linha.documento_item_ids.mapped('documento_id')
            ordem.documento_ids = documentos

    @api.multi
    def visualizar_documentos(self):
        '''
        This function returns an action that display existing vendor
        bills of given purchase order ids.
        When only one found, show the vendor bill immediately.
        '''
        action = self.env.ref('sped.sped_documento_emissao_nfe_acao')
        result = action.read()[0]

        # override the context to get rid of the default filtering
        result['context'] = {
            'default_emissao': '1',
            'default_entrada_saida': '0',
            'default_modelo': '55',
            'manual': True,
            'default_purchase_order_id': self.id,
        }

        if len(self.documento_ids) > 1:
            result['domain'] = "[('id', 'in', " + \
                               str(self.documento_ids.ids) + ")]"
        elif len(self.documento_ids) == 1:
            res = self.env.ref('sped_purchase.sped_documento_'
                               'emissao_nfe_form_view', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = self.documento_ids.id
        return result

    @api.multi
    def button_confirm(self):
        if super(PurchaseOrder, self).button_confirm():
            for ordem in self:
                ordem.invoice_status = 'to invoice'
            return True
        return False
    
    @api.onchange('state')
    def _onchange_state(self):
        self.ensure_one()
        if self.state == 'draft' and self.state == 'purchase':
            return self.button_approve()
        elif self.state == 'purchase' and self.state == 'invoiced':
            return self.button_invoiced()

    @api.multi
    def button_approve(self, force=False):
        self.write({'state': 'purchase'})
        self._create_picking()
        if self.company_id.po_lock == 'lock':
            self.write({'state': 'done'})
        for picking in self.picking_ids:
            if picking.state != 'cancel':
                picking.write({'state': 'confirmed'})
        return {}

    @api.multi
    def button_invoiced(self):
        return {
            'name': 'Importar NF-e',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'sped_purchase.consulta_status_documento',
            'view_id': self.env.ref('sped_purchase.sped_consulta_status_documento_form').id,
            'type': 'ir.actions.act_window',
            'context': {
                'default_empresa_id': self.empresa_id.id,
            },
            'target': 'new'
        }

    @staticmethod
    def _valid_state_change(old, new):
        return (old, new) in [
            ('cancel', 'draft'),
            ('draft', 'cancel'),
            ('purchase', 'cancel'),
            ('invoiced', 'cancel'),
            ('draft', 'purchase'),
            ('purchase', 'invoiced'),
            ('invoiced', 'received'),
        ]

    @api.multi
    def write(self, vals):
        if vals.get('state', False):
            self.ensure_one()
            if not PurchaseOrder._valid_state_change(
                    self.state, vals['state']):
                raise UserError('Transição não permitida')
        return super(PurchaseOrder, self).write(vals)

    @api.multi
    def action_view_picking(self):
        res = super(PurchaseOrder, self).action_view_picking()
        if not (res.get('res_id') or res.get('domain')):
            res['domain'] = "[('purchase_id','=',%s)]" % self.id
        return res

    @api.depends('order_line.move_ids.returned_move_ids',
                 'order_line.move_ids.state',
                 'order_line.move_ids.picking_id',
                 'state')
    def _compute_picking(self):
        super(PurchaseOrder, self)._compute_picking()
        for order in self:
            if order.state == 'invoiced':
                for picking in order.picking_ids:
                    if picking.state != 'cancel':
                        picking.write({'state': 'assigned'})

    @api.depends('order_line.qty_invoiced',
                 'order_line.qty_received',
                 'order_line.product_qty')
    def _get_invoiced(self):
        super(PurchaseOrder, self)._get_invoiced()
        for order in self:
            if order.invoice_status == 'invoiced':
                order.state = 'invoiced'
            if all(line.quantidade == line.qty_received
                   for line in order.order_line) and order.documento_ids:
                order.state = 'received'