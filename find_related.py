

modules_done = {
    'base',
    'base_address_extended',
    'base_automation',
    'base_geolocalize',
    'base_iban',
    'base_import',
    'base_import_module',
    'base_install_request',
    'base_setup',
    'base_sparse_field',
    'base_vat',
    'contacts',
    'product',
    'mail',
}

# delivery,delivery_stock_picking_batch,mrp,mrp_account,mrp_landed_costs,mrp_product_expiry,mrp_repair,mrp_subcontracting,mrp_subcontracting_account,mrp_subcontracting_dropshipping,mrp_subcontracting_landed_costs,mrp_subcontracting_purchase,mrp_subcontracting_repair,mrp_subonctracting_landed_costs,project_mrp,project_purchase,purchase,purchase_mrp,purchase_price_diff,purchase_product_matrix,purchase_requisition,purchase_requisition_sale,purchase_requisition_stock,purchase_stock,sale_mrp,sale_mrp_margin,sale_project_stock,sale_purchase,sale_purchase_stock,sale_stock,sale_stock_margin,stock,stock_account,stock_delivery,stock_dropshipping,stock_landed_costs,stock_picking_batch,stock_sms,website_sale_stock,website_sale_stock_product_configurator,website_sale_stock_wishlist,account_avatax_stock,account_invoice_extract_purchase,approvals_purchase,approvals_purchase_stock,helpdesk_stock,helpdesk_stock_account,industry_fsm_stock,mrp_accountant,mrp_account_enterprise,mrp_maintenance,mrp_mps,mrp_plm,mrp_subcontracting_account_enterprise,mrp_subcontracting_enterprise,mrp_subcontracting_quality,mrp_subcontracting_studio,mrp_workorder,mrp_workorder_expiry,mrp_workorder_hr,mrp_workorder_hr_account,mrp_workorder_iot,mrp_workorder_plm,purchase_enterprise,purchase_intrastat,purchase_mrp_workorder_quality,purchase_stock_enterprise,quality,quality_control,quality_control_iot,quality_control_picking_batch,quality_control_worksheet,quality_iot,quality_mrp,quality_mrp_workorder,quality_mrp_workorder_iot,quality_mrp_workorder_worksheet,sale_stock_renting,sale_subscription_stock,stock_accountant,stock_account_enterprise,stock_barcode,stock_barcode_mrp,stock_barcode_mrp_subcontracting,stock_barcode_picking_batch,stock_barcode_product_expiry,stock_barcode_quality_control,stock_barcode_quality_control_picking_batch,stock_barcode_quality_mrp,stock_enterprise,stock_intrastat,website_sale_stock_renting
target_modules = [
    'delivery',
    'delivery_stock_picking_batch',
    'mrp',
    'mrp_account',
    'mrp_landed_costs',
    'mrp_product_expiry',
    'mrp_repair',
    'mrp_subcontracting',
    'mrp_subcontracting_account',
    'mrp_subcontracting_dropshipping',
    'mrp_subcontracting_landed_costs',
    'mrp_subcontracting_purchase',
    'mrp_subcontracting_repair',
    'mrp_subonctracting_landed_costs',
    'project_mrp',
    'project_purchase',
    'purchase',
    'purchase_mrp',
    'purchase_price_diff',
    'purchase_product_matrix',
    'purchase_requisition',
    'purchase_requisition_sale',
    'purchase_requisition_stock',
    'purchase_stock',
    'sale_mrp',
    'sale_mrp_margin',
    'sale_project_stock',
    'sale_purchase',
    'sale_purchase_stock',
    'sale_stock',
    'sale_stock_margin',
    'stock',
    'stock_account',
    'stock_delivery',
    'stock_dropshipping',
    'stock_landed_costs',
    'stock_picking_batch',
    'stock_sms',
    'account_avatax_stock',
    'account_invoice_extract_purchase',
    'approvals_purchase',
    'approvals_purchase_stock',
    'helpdesk_stock',
    'helpdesk_stock_account',
    'industry_fsm_stock',
    'mrp_accountant',
    'mrp_account_enterprise',
    'mrp_maintenance',
    'mrp_mps',
    'mrp_plm',
    'mrp_subcontracting_account_enterprise',
    'mrp_subcontracting_enterprise',
    'mrp_subcontracting_quality',
    'mrp_subcontracting_studio',
    'mrp_workorder',
    'mrp_workorder_expiry',
    'mrp_workorder_hr',
    'mrp_workorder_hr_account',
    'mrp_workorder_iot',
    'mrp_workorder_plm',
    'purchase_enterprise',
    'purchase_intrastat',
    'purchase_mrp_workorder_quality',
    'purchase_stock_enterprise',
    'quality',
    'quality_control',
    'quality_control_iot',
    'quality_control_picking_batch',
    'quality_control_worksheet',
    'quality_iot',
    'quality_mrp',
    'quality_mrp_workorder',
    'quality_mrp_workorder_iot',
    'quality_mrp_workorder_worksheet',
    'sale_stock_renting',
    'sale_subscription_stock',
    'stock_accountant',
    'stock_account_enterprise',
    'stock_barcode',
    'stock_barcode_mrp',
    'stock_barcode_mrp_subcontracting',
    'stock_barcode_picking_batch',
    'stock_barcode_product_expiry',
    'stock_barcode_quality_control',
    'stock_barcode_quality_control_picking_batch',
    'stock_barcode_quality_mrp',
    'stock_enterprise',
    'stock_intrastat',
]

print(','.join(target_modules))


keep_it = {
    'mail.activity.res_model',
    'res.company.name',
    'res.company.email',
    'res.company.phone',
    'res.company.mobile',
    'mail.template.model',  # Not sure ?
    'discuss.channel.rtc.session.channel_id',  # Because of rtc_session_ids
    'stock.move.scrapped',  # Because it is used in a lot of query/code and the code seems minimal
    'stock.move.line.state',  # Use in multi index
    'stock.picking.group_id',  # Because travers a one2many
    'stock.picking.company_id',  # Because index + low cost
    'stock.picking.sale_id',  # Because index
    'stock.quant.company_id',  # Because multi company
    'mrp.bom.line.product_tmpl_id',  # Add for performance
    'mrp.bom.line.company_id',  # index + low cost
    'mrp.bom.byproduct.company_id  ',  # index + low cost
    'mrp.workcenter.name',  # ressource stuffs
    'mrp.workcenter.time_efficiency',
    'mrp.workcenter.active',
    'purchase.order.line.company_id',  # Multi company rules
    'purchase.requisition.line.company_id',  # Multi company rules
    'delivery.carrier.company_id',  # Multi company rules
}

remove_not_sure = {
    'product.template.attribute.value.product_tmpl_id',  # Not sure ? https://github.com/odoo/odoo/pull/35866
    'product.template.attribute.value.attribute_id',  # Not sure ? https://github.com/odoo/odoo/pull/35866
    'stock.move.order_finished_lot_id',  # use to group and index to unlink
    'stock.rule.route_sequence',  # cost low and use in order ?
}

# to get all modules
# ls -w 1 -d * | sed 's/$//'


for model in env.values():
    if model._transient:
        continue
    for field in model._fields.values():
        if not field.store or not field.related:
            continue
        if field.type == 'binary':
            continue

        if field._module not in target_modules:
            continue

        if str(field) in keep_it:
            continue

        print(f"{field} is store related='{field.related}' added in {field._module}")


