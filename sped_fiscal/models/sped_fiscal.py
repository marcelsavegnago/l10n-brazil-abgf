# -*- coding: utf-8 -*-
# Copyright 2017 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class SpedFiscal(models.Model):

    _name = 'sped.fiscal'
    _description = 'Sped Fiscal'  # TODO

    name = fields.Char()
