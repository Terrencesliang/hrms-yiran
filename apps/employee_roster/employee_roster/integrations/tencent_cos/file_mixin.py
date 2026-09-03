from html import escape

from employee_roster.integrations.tencent_cos.config import is_enabled
from employee_roster.integrations.tencent_cos.storage import (
	get_object_content,
	is_cos_file_url,
	object_exists,
	should_store_in_cos,
)


class TencentCOSFileMixin:
	"""Keep Frappe File behavior while replacing the physical storage backend."""

	def before_insert(self):
		if is_enabled() and not self.is_folder and self.get("content") and should_store_in_cos(self):
			self.is_private = 1
		return super().before_insert()

	def validate(self):
		if is_enabled() and is_cos_file_url(self.file_url):
			self.is_private = 1
		return super().validate()

	def exists_on_disk(self):
		if is_cos_file_url(self.file_url):
			return object_exists(self.file_url)
		return super().exists_on_disk()

	def get_content(self, encodings=None):
		if is_cos_file_url(self.file_url) and not self.get("content"):
			self._content = get_object_content(self.file_url)
			return self._content
		return super().get_content(encodings=encodings)

	@property
	def unique_url(self):
		if is_cos_file_url(self.file_url):
			return self.file_url
		return super().unique_url

	def create_attachment_record(self):
		if not is_cos_file_url(self.file_url):
			return super().create_attachment_record()
		icon = ' <i class="fa fa-lock text-warning"></i>'
		file_url = escape(self.file_url, quote=True)
		file_name = escape(self.file_name or self.file_url)
		self.add_comment_in_reference_doc(
			"Attachment",
			f"<a href='{file_url}' target='_blank' rel='noopener noreferrer'>{file_name}</a>{icon}",
		)
