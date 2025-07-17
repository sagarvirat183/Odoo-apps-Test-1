# models/stock_picking.py
from odoo import models, fields, api, _

class StockPicking(models.Model):
    _inherit = 'stock.picking'
    
    def _compute_show_update_lot_button(self):
        for picking in self:
            picking.show_update_lot_button = picking.picking_type_id.y_update_lot_qty and picking.state == 'assigned'
    
    show_update_lot_button = fields.Boolean(
        string="Show Update Lot Quantity Button",
        compute='_compute_show_update_lot_button',
        store=False
    )

    def action_update_lot_quantity(self):
        """
        Update only the actual quantity in move lines based on the full quantity available in the lots
        without changing the original demand quantity.
        Only updates products that have the y_update_lot_qty boolean set to True.
        """
        for picking in self:
            # Skip if picking type doesn't allow lot quantity updates
            if not picking.picking_type_id.y_update_lot_qty:
                continue
                
            for move in picking.move_ids:
                # Skip products that don't have y_update_lot_qty=True
                if not move.product_id.y_update_lot_qty:
                    continue
                    
                # Only process moves with tracking
                if move.product_id.tracking in ('none', 'serial'):
                    continue
                
                lot_move_lines = move.move_line_ids.filtered(lambda ml: ml.lot_id)
                
                if not lot_move_lines:
                    continue
                
                # Group by lot to calculate total quantity
                lots_qty = {}
                for move_line in lot_move_lines:
                    lot_id = move_line.lot_id.id
                    if lot_id in lots_qty:
                        lots_qty[lot_id] += move_line.quantity
                    else:
                        lots_qty[lot_id] = move_line.quantity
                
                # Sum up the total lot quantities
                total_lot_qty = sum(lots_qty.values())
                
                # Update only the actual quantity in the move line based on the assigned lots' full quantity
                if total_lot_qty > 0:
                    move.quantity = total_lot_qty
                    
                    # Update the quantity in the move lines
                    quant_dict = {}
                    for move_line in lot_move_lines:
                        lot_id = move_line.lot_id.id
                        # Get the actual lot quantity from stock.quant
                        lot_quant = self.env['stock.quant'].search([
                            ('lot_id', '=', lot_id),
                            ('location_id', '=', move_line.location_id.id),
                            ('product_id', '=', move_line.product_id.id)
                        ], limit=1)
                        
                        if lot_id not in quant_dict and lot_quant:
                            quant_dict[lot_id] = lot_quant.quantity
                        
                        # Update quantity to the full lot quantity
                        if lot_id in quant_dict:
                            move_line.qty_done = quant_dict[lot_id]
            return True
        