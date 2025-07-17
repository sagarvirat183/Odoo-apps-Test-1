from odoo import models, fields, api

class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'
    
    y_update_lot_qty = fields.Boolean(string='Update Lot Quantity',help="If checked, allows updating lot to their full available quantities in respective transactions.")