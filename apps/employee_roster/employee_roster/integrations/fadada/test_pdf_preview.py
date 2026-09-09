from __future__ import annotations

import io
import unittest

from pypdf import PdfReader
from reportlab.pdfgen import canvas

from employee_roster.integrations.fadada.pdf_preview import render_filled_preview


class TestFilledPdfPreview(unittest.TestCase):
	def test_renders_values_on_the_configured_page(self):
		base = io.BytesIO()
		pdf = canvas.Canvas(base, pagesize=(595.32, 841.92))
		pdf.drawString(30, 810, "base")
		pdf.showPage()
		pdf.save()
		result = render_filled_preview(
			base.getvalue(),
			{
				"docs": [
					{
						"docFields": [
							{
								"fieldId": "mobile",
								"fieldType": "text_single_line",
								"position": {
									"positionPageNo": 1,
									"positionX": 100,
									"positionY": 200,
								},
							}
						]
					}
				]
			},
			[{"fillFields": [{"fieldId": "mobile", "fieldValue": "13800138000"}]}],
		)
		reader = PdfReader(io.BytesIO(result))
		self.assertEqual(len(reader.pages), 1)
		self.assertIn("13800138000", reader.pages[0].extract_text())
