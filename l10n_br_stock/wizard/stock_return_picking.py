# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import netsvc
import time

from osv import osv,fields
from tools.translate import _

class stock_return_picking(osv.osv_memory):
    _inherit = 'stock.return.picking'

    def create_returns(self, cr, uid, ids, context=None):
        """ 
         Creates return picking.
         @param self: The object pointer.
         @param cr: A database cursor
         @param uid: ID of the user currently logged in
         @param ids: List of ids selected
         @param context: A standard dictionary
         @return: A dictionary which of fields with values.
        """
        
        result = super(stock_return_picking, self).create_returns(cr, uid, ids, context)
        
        data = self.read(cr, uid, ids[0])

        if data['invoice_state'] == 'none':
            return result
        
        pick_obj = self.pool.get('stock.picking')
        fiscal_operation_obj = self.pool.get('l10n_br_account.fiscal.operation')
        fiscal_position_obj = self.pool.get('account.fiscal.position')
        result_domain = eval(result['domain'])
        record_ids = result_domain and result_domain[0] and result_domain[0][2]
        picks = pick_obj.browse(cr, uid, record_ids, context=context)
    
        for pick in picks:
            
            vals = {
                    'fiscal_operation_category_id': False, 
                    'fiscal_operation_id': False,
                    'fiscal_position': False,
                    }
            
            fo_return_id = pick.fiscal_operation_id.refund_fiscal_operation_id and pick.fiscal_operation_id.refund_fiscal_operation_id.id
            
            if not fo_return_id:
                raise osv.except_osv(_('Error !'), _("This Fiscal Operation does not has Fiscal Operation for Returns!"))
            
            fiscal_operation = fiscal_operation_obj.browse(cr, uid, fo_return_id, context)
            
            obj_company = self.pool.get('res.company').browse(cr, uid, [pick.company_id.id])[0]
            
            company_addr = self.pool.get('res.partner').address_get(cr, uid, [obj_company.partner_id.id], ['default'])
            company_addr_default = self.pool.get('res.partner.address').browse(cr, uid, [company_addr['default']])[0]
    
            from_country = company_addr_default.country_id.id
            from_state = company_addr_default.state_id.id
    
            to_country = pick.address_id.country_id.id
            to_state = pick.address_id.state_id.id
    
            obj_partner = self.pool.get('res.partner').browse(cr, uid, [pick.address_id.partner_id.id])[0]
            partner_fiscal_type = obj_partner.partner_fiscal_type_id.id
            
            fsc_pos_id = self.pool.get('account.fiscal.position.rule').search(cr, uid, ['&',
                                                                                            ('company_id','=', obj_company.id),
                                                                                            ('use_picking','=',True),
                                                                                            ('fiscal_operation_category_id','=',fiscal_operation.fiscal_operation_category_id.id),
                                                                                        '|',
                                                                                        ('from_country','=',from_country),('from_country','=',False),
                                                                                        '|',
                                                                                        ('to_country','=',to_country), ('to_country','=',False),
                                                                                        '|',
                                                                                            ('from_state','=',from_state),('from_state','=',False),
                                                                                        '|',
                                                                                            ('to_state','=',to_state),('to_state','=',False),
                                                                                        '|',
                                                                                            ('partner_fiscal_type_id','=',False),('partner_fiscal_type_id','=',partner_fiscal_type)
                                                                                        ])
            
            vals['fiscal_operation_category_id'] = fiscal_operation.fiscal_operation_category_id.id
            vals['fiscal_operation_id'] = fo_return_id
            
            if fsc_pos_id:
                obj_fpo_rule = self.pool.get('account.fiscal.position.rule').browse(cr, uid, fsc_pos_id)[0]
                vals['fiscal_position'] = fiscal_position_obj.id
                
            pick_obj.write(cr, uid, pick.id, vals)

        return result

stock_return_picking()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: