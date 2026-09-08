# Copyright (c) 2026 stillgroup
# License: MIT
from __future__ import annotations

import json

import frappe
from frappe.model.document import Document


class ContractSignTemplate(Document):
	def validate(self) -> None:
		for fieldname in ("field_mapping", "actor_config", "sign_config"):
			value = self.get(fieldname)
			if not value:
				continue
			try:
				json.loads(value)
			except (TypeError, ValueError) as exc:
				raise frappe.ValidationError(f"{fieldname} 必须是有效 JSON") from exc
