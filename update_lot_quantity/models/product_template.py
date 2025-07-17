from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    
    
    y_update_lot_qty = fields.Boolean(string='Update Lot Quantity',help="If checked, allows updating lot to their full available quantities in respective transactions.")
