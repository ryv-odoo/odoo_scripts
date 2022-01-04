#!/usr/bin/env python3
import sys
import ast
import networkx as nx
import os

# import matplotlib.pyplot as plt
# import json


root_module = len(sys.argv) > 1 and sys.argv[1:] or ['stock', 'purchase']


G = nx.DiGraph()

# Browse all __manifest__ files in odoo addons (+enterprise)
addons = [
    './odoo/addons',
    './enterprise',
]

addons_paths = []
for addon in addons:
    addons_paths += [(a, os.path.join(addon, a)) for a in os.listdir(addon) if os.path.isdir(os.path.join(addon, a))]

manifest_by_module = dict()

for addon in addons_paths:
    if os.path.exists(addon[1] + '/__manifest__.py'):
        f = open(addon[1] + '/__manifest__.py')
        m = ast.literal_eval(f.read())
        manifest_by_module[addon[0]] = m
        for module in m.get('depends', []):
            G.add_edge(module, addon[0])
        f.close()

print(G.number_of_nodes())
print(G.number_of_edges())
# website_sale_delivery,purchase_mrp,product_expiry,hr_attendance,pos_epson_printer,stock,sale_coupon_delivery,delivery,quality_control,pos_blackbox_be,mrp_account,pos_restaurant,barcodes,purchase_stock,mrp,quality_mrp_workorder,event_barcode,point_of_sale,stock_barcode,stock_account,sale_purchase_stock,stock_dropshipping,mrp_subcontracting,repair,quality,l10n_in_stock,sale_amazon,quality_control_picking_batch,stock_picking_batch,website_sale_stock,mrp_workorder,stock_landed_costs,sale_stock
module_child = set(r for r in root_module)
for r in root_module:
    module_child |= set(nx.dfs_preorder_nodes(G, r))
print(",".join(module_child))

# G_stock = nx.subgraph(G, list(nx.all_neighbors(G, root_module)) + [root_module])
# options = {
#     'node_color': 'green',
#     'node_size': 30,
#     'width': 1,
# }
# nx.draw_shell(G_stock, with_labels=True, **options)
# plt.show()
