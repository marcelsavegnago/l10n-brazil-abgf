# -*- coding: utf-8 -*-
# Copyright 2018 - ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import pysped
from openerp import api, fields, models
from pybrasil.inscricao.cnpj_cpf import limpa_formatacao

from .sped_registro_intermediario import SpedRegistroIntermediario


class SpedAfastamentoTemporario(models.Model, SpedRegistroIntermediario):
    _name = "sped.esocial.afastamento.temporario"
    _rec_name = "name"
    _order = "company_id"

    name = fields.Char(
        string='name',
        compute='_compute_display_name',
        store=True,
    )
    company_id = fields.Many2one(
        string='Empresa',
        comodel_name='res.company',
    )
    hr_holiday_id = fields.Many2one(
        string='Afastamento',
        comodel_name='hr.holidays',
        required=True,
    )
    sped_afastamento = fields.Many2many(
        string='Registro Afastamento',
        comodel_name='sped.registro',
    )
    situacao_esocial = fields.Selection(
        selection=[
            ('1', 'Precisa Transmitir'),
            ('2', 'Transmitida'),
            ('3', 'Erro(s)'),
            ('4', 'Sucesso'),
        ],
        string='Situação no e-Social',
        compute='compute_situacao_esocial',
    )

    @api.depends('hr_holiday_id')
    def _compute_display_name(self):
        for record in self:
            record.name = 'S-2230 - Afastamento Temporário {}'.format(
                record.hr_holiday_id.display_name or '')

    @api.depends('sped_afastamento')
    def compute_situacao_esocial(self):
        for afastamento in self:
            situacao_esocial = '1'

            for afastamento in afastamento.sped_afastamento:
                situacao_esocial = afastamento.situacao

            # Popula na tabela
            afastamento.situacao_esocial = situacao_esocial

    # Roda a atualização do e-Social (não transmite ainda)
    @api.multi
    def gerar_registro(self):
        self.ensure_one()

        # Criar o registro S-2230 de alteração, se for necessário
        if not self.sped_afastamento:
            values = {
                'tipo': 'esocial',
                'registro': 'S-2230',
                'ambiente': self.company_id.esocial_tpAmb,
                'company_id': self.company_id.id,
                'operacao': 'I',
                'evento': 'evtAfastTemp',
                'origem': ('hr.holidays,%s' % self.hr_holiday_id.id),
                'origem_intermediario': (
                        'sped.esocial.afastamento.temporario,%s' % self.id),
            }

            sped_afastamento = self.env['sped.registro'].create(values)
            self.sped_afastamento = [(4, sped_afastamento.id)]

    @api.multi
    def popula_xml(self, ambiente='2', operacao='I'):
        """
        Função para popular o xml com os dados referente ao afastamento
        temporário de um trabalhador
        """
        pass
        # Cria o registro
        S2230 = pysped.esocial.leiaute.S2230_2()
        holiday_id = self.hr_holiday_id

        S2230.tpInsc = '1'
        S2230.nrInsc = limpa_formatacao(self.company_id.cnpj_cpf)[0:8]

        S2230.evento.ideEvento.indRetif.valor = '1'
        S2230.evento.ideEvento.tpAmb.valor = \
            holiday_id.contrato_id.company_id.esocial_tpAmb
        S2230.evento.ideEvento.procEmi.valor = '1'
        S2230.evento.ideEvento.verProc.valor = '8.0'

        # Popula ideEmpregador
        S2230.evento.ideEmpregador.tpInsc.valor = '1'
        S2230.evento.ideEmpregador.nrInsc.valor = limpa_formatacao(
            holiday_id.contrato_id.company_id.cnpj_cpf)[0:8]

        # Popula ideVinculo
        S2230.evento.ideVinculo.cpfTrab.valor = limpa_formatacao(
            holiday_id.contrato_id.employee_id.cpf)
        S2230.evento.ideVinculo.nisTrab.valor = limpa_formatacao(
            holiday_id.contrato_id.employee_id.pis_pasep)
        S2230.evento.ideVinculo.matricula.valor = \
            holiday_id.contrato_id.matricula

        # Popula infoAfastamento
        # Popula iniAfastamento
        inicio_afastamento = pysped.esocial.leiaute.S2230_IniAfastamento_2()
        inicio_afastamento.dtIniAfast.valor = holiday_id.data_inicio
        inicio_afastamento.codMotAfast.valor = \
            holiday_id.holiday_status_id.esocial_evento_afastamento_id.codigo

        S2230.evento.infoAfastamento.iniAfastamento.append(inicio_afastamento)

        # Popula fimAfastamento
        fim_afastamento = pysped.esocial.leiaute.S2230_FimAfastamento_2()
        fim_afastamento.dtTermAfast.valor = holiday_id.data_fim

        S2230.evento.infoAfastamento.fimAfastamento.append(fim_afastamento)

        return S2230

    @api.multi
    def retorno_sucesso(self, evento):
        self.ensure_one()