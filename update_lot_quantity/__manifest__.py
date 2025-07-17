# -*- coding: utf-8 -*-
{
    "name": "UPDATE LOT QUANTITY IN TRANSFERS - 18.0.0.1",
    "summary": """ Allows updating lot to their full available quantities in respective transactions """,
    "description": """
        This module enhances Odoo's inventory management by adding a "Update Lot Quantity" button for internal transfer operations. 

        When working with lot-tracked products in receipt operations, Odoo typically reserves exactly the demanded quantity. 
        However, in some cases, you may want to update quantities to match the complete available quantities in each picked lot.

        Key features:
        - Button in stock picking header to update lot quantities
        - Automatically adjusts quantities based on full lot availability
    """,
    "author": "Prixgen Tech Solutions Pvt. Ltd.",
    "company": "Prixgen Tech Solutions Pvt. Ltd.",
    "website": "https://www.prixgen.com",
    "module_type": "official",
    "app_origin": "project",
    "category": "Inventory",
    "version": "18.0.0.1",
    "license": "LGPL-3",
    "depends": [
        "base",
        "stock",
        "sale",
        "purchase",
        "stock_account",
        "inventory_base",
    ],
    "data": [
        "views/stock_picking_type_view.xml",
        "views/product_template_view.xml",
        "views/stock_picking_view.xml",
        # "views/product_category_view.xml",
    ],
}
