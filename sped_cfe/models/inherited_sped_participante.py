# -*- coding: utf-8 -*-
#
# Copyright 2017 KMEE INFORMATICA LTDA
#   Luiz Felipe do Divino <luiz.divino@kmee.com.br>
# License AGPL-3 or later (http://www.gnu.org/licenses/agpl)
#

from __future__ import division, print_function, unicode_literals

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = b'res.partner'

    codigo_administradora_cartao = fields.Char(
        string="Código da Administradora"
    )

    eh_administradora_cartao = fields.Boolean(
        string="É Administradora de Cartão?"
    )
