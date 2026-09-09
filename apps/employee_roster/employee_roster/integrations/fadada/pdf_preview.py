"""把法大大控件值叠加到底稿并生成仅供 HR 核对的本地 PDF 预览。"""
from __future__ import annotations

import io
from datetime import datetime
from typing import Any

from pypdf import PdfReader, PdfWriter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.pdfgen import canvas

FADADA_PAGE_WIDTH = 793.76
FADADA_PAGE_HEIGHT = 1122.56
FONT_NAME = "STSong-Light"


def _display_value(value: str, field: dict[str, Any]) -> str:
	field_type = str(field.get("fieldType") or "")
	if field_type not in {"fill_date", "date_sign"}:
		return value
	try:
		parsed = datetime.strptime(value[:10], "%Y-%m-%d")
	except (TypeError, ValueError):
		return value
	return f"{parsed.year}年{parsed.month:02d}月{parsed.day:02d}日"


def _font_size(field: dict[str, Any], scale_y: float) -> float:
	for key in (
		"fieldTextSingleLine",
		"fieldTextMultiLine",
		"fieldNumber",
		"fieldIdCard",
		"fieldFillDate",
	):
		if config := field.get(key):
			return max(7.0, float(config.get("fontSize") or 16) * scale_y)
	return max(7.0, 16 * scale_y)


def _field_width(field: dict[str, Any], scale_x: float) -> float:
	for key in (
		"fieldTextSingleLine",
		"fieldTextMultiLine",
		"fieldNumber",
		"fieldIdCard",
		"fieldFillDate",
	):
		if config := field.get(key):
			return max(12.0, float(config.get("width") or 160) * scale_x)
	return 120.0


def _field_height(field: dict[str, Any], scale_y: float) -> float:
	for key in (
		"fieldTextSingleLine",
		"fieldTextMultiLine",
		"fieldNumber",
		"fieldIdCard",
		"fieldFillDate",
	):
		if config := field.get(key):
			return max(12.0, float(config.get("height") or 30) * scale_y)
	return 22.5


def render_filled_preview(
	base_pdf: bytes,
	template_detail: dict[str, Any],
	actors: list[dict[str, Any]],
) -> bytes:
	values = {
		str(field.get("fieldId") or ""): str(field.get("fieldValue") or "")
		for actor in actors
		for field in actor.get("fillFields") or []
		if field.get("fieldId") and field.get("fieldValue") not in (None, "")
	}
	fields = {
		str(field.get("fieldId") or ""): field
		for doc in template_detail.get("docs") or []
		for field in doc.get("docFields") or []
		if field.get("fieldId")
	}
	reader = PdfReader(io.BytesIO(base_pdf))
	writer = PdfWriter()
	pdfmetrics.registerFont(UnicodeCIDFont(FONT_NAME))
	for page_index, page in enumerate(reader.pages, start=1):
		width = float(page.mediabox.width)
		height = float(page.mediabox.height)
		scale_x = width / FADADA_PAGE_WIDTH
		scale_y = height / FADADA_PAGE_HEIGHT
		page_values = [
			(field_id, value)
			for field_id, value in values.items()
			if int((fields.get(field_id) or {}).get("position", {}).get("positionPageNo") or 0)
			== page_index
		]
		if not page_values:
			writer.add_page(page)
			continue
		buffer = io.BytesIO()
		overlay = canvas.Canvas(buffer, pagesize=(width, height))
		for field_id, value in page_values:
			field = fields.get(field_id) or {}
			position = field.get("position") or {}
			text = _display_value(value, field)
			font_size = _font_size(field, scale_y)
			max_width = _field_width(field, scale_x)
			while font_size > 7 and pdfmetrics.stringWidth(text, FONT_NAME, font_size) > max_width:
				font_size -= 0.5
			x = (
				float(position.get("positionX") or 0) * scale_x
				- _field_width(field, scale_x) / 2
			)
			field_height = _field_height(field, scale_y)
			y = (
				height
				- float(position.get("positionY") or 0) * scale_y
				+ field_height / 2
				- font_size
			)
			overlay.setFont(FONT_NAME, font_size)
			overlay.setFillColorRGB(0, 0, 0)
			overlay.drawString(x, max(0, y), text)
		overlay.showPage()
		overlay.save()
		buffer.seek(0)
		page.merge_page(PdfReader(buffer).pages[0])
		writer.add_page(page)
	writer.add_metadata({"/Title": "合同已填字段预览", "/Producer": "HRMS"})
	output = io.BytesIO()
	writer.write(output)
	return output.getvalue()
