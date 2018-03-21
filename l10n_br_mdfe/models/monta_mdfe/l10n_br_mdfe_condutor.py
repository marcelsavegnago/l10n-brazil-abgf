# -*- coding: utf-8 -*-
# Copyright 2018 KMEE INFORMATICA LTDA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from __future__ import division, print_function, unicode_literals


from odoo import api, fields, models, _
from odoo.addons.l10n_br_base.tools.misc import punctuation_rm

class L10nBrMdfeCondutor(models.Model):

    _inherit = 'l10n_br.mdfe.condutor'

    def monta_mdfe(self):
        self.ensure_one()
        return
