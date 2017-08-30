# -*- coding: utf-8 -*-
# Copyright 2017 KMEE
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Sped Vendas',
    'summary': """
        Vendas Brasileira""",
    'version': '10.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'KMEE,Odoo Community Association (OCA)',
    'website': 'www.kmee.com.br',
    'depends': [
        'sped_imposto',
        'sped',
        'sale',
    ],
    'data': [
        'views/inherited_sale_order_line_base_view.xml',
        'views/inherited_sale_order_line_produto_view.xml',
        'views/inherited_sale_order_line_servico_view.xml',
        'views/inherited_sale_order_orcamento_view.xml',
        'views/inherited_sale_order_pedido_view.xml',
        'views/inherited_sale_order_para_faturar_view.xml',
    ],
    'installable': True,
}
