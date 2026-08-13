from cmr_pipe_laying_master.api.entries import _build_purchase_receipt, _build_stock_entry, get_entry_options
from cmr_pipe_laying_master.api.masters import _project


def build_drafts_without_insert():
	options = get_entry_options()
	company = options["companies"][0]["name"]
	supplier = options["suppliers"][0]["name"]
	warehouse = options["warehouses"][0]["name"]
	item = options["items"][0]
	item_code = item.get("item_code") or item["name"]
	project = _project({"project_name": "CMR DIAGNOSTIC NOT SAVED", "company": company})
	inward = _build_purchase_receipt({
		"company": company,
		"supplier": supplier,
		"posting_date": "2026-08-12",
		"site": "CMR DIAGNOSTIC NOT SAVED",
		"warehouse": warehouse,
		"items": [{"item_code": item_code, "qty": 1, "rate": 1}],
	})
	transfer = _build_stock_entry({
		"company": company,
		"posting_date": "2026-08-12",
		"site": "CMR DIAGNOSTIC NOT SAVED",
		"source_warehouse": warehouse,
		"target_warehouse": warehouse,
		"items": [{"item_code": item_code, "qty": 1}],
	}, False)
	return {
		"database_writes": 0,
		"project_doctype": project.doctype,
		"inward_doctype": inward.doctype,
		"inward_items": len(inward.items),
		"issue_doctype": transfer.doctype,
		"issue_type": transfer.stock_entry_type,
		"issue_items": len(transfer.items),
	}
