# -*- coding: utf-8 -*-
# Copyright 2018 ABGF
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


{
    'name': 'ABGF Contabilidade',
    'category': 'ABGF',
    'license': 'AGPL-3',
    'author': 'ABGF, Odoo Community Association (OCA)',
    'maintainer': 'ABGF',
    'website': 'http://www.abgf.com.br',
    'version': '8.0.0.0.0',
    'depends': [
        'l10n_br_account_product',
    ],
    'data': [
        'security/ir.model.access.csv',

        'data/natureza_conta_data.xml',

        'views/account_account.xml',
        'views/account_natureza.xml',
        'views/account_centro_custo.xml',
    ],
    'demo': [
    ],
}