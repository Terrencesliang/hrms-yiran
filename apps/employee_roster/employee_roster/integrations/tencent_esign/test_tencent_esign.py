from __future__ import annotations

import base64
import hashlib
import hmac
import json
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

from employee_roster.hr_roster.api import contract as contract_api
from employee_roster.integrations.tencent_esign import callback, client, service


class TestTencentESignConfiguration(unittest.TestCase):
	def test_missing_configuration_fails_before_sdk_call(self):
		with patch.dict(client.os.environ, {}, clear=True), patch.object(client.frappe, "conf", {}):
			status = client.configuration_status()
			self.assertFalse(status["configured"])
			self.assertIn("secret_id", status["message"])
			with self.assertRaises(client.ConfigurationError):
				client.TencentESignClient()


class TestTencentESignStatus(unittest.TestCase):
	def test_vendor_status_mapping(self):
		self.assertEqual(service.map_vendor_status("FINISHED"), "Completed")
		self.assertEqual(service.map_vendor_status("CANCELED"), "Cancelled")
		self.assertEqual(service.map_vendor_status("REJECTED"), "Rejected")
		self.assertEqual(service.map_vendor_status("unexpected-new-status"), "Pending")

	def test_contract_fields_are_resolved_without_trusting_employee_payload(self):
		employee = SimpleNamespace(
			name="HR-EMP-00001",
			employee_name="张三",
			cell_number="13800000000",
			meta=SimpleNamespace(has_field=lambda name: name in {"employee_name", "cell_number"}),
		)
		template = SimpleNamespace(
			template_name="劳动合同",
			seal_id="",
			field_mapping=json.dumps(
				{"员工姓名": "$employee.employee_name", "合同开始日期": "$contract.contract_start"}
			),
			actor_config="{}",
			sign_config="{}",
		)
		payload = service.build_template_payload(
			template,
			employee,
			"request-1",
			{"contract_start": "2026-09-08"},
		)
		self.assertEqual(
			payload["form_fields"],
			[
				{"ComponentName": "员工姓名", "ComponentValue": "张三"},
				{"ComponentName": "合同开始日期", "ComponentValue": "2026-09-08"},
			],
		)


class TestTencentESignPermissionAndIdempotency(unittest.TestCase):
	def test_manager_permission_is_required(self):
		with patch.object(contract_api.frappe, "session", SimpleNamespace(user="Guest")):
			with patch.object(contract_api.frappe, "get_roles", return_value=[]):
				with patch.object(contract_api.frappe, "throw") as throw:
					contract_api._require_manager()
					throw.assert_called_once()

	def test_existing_trans_reference_does_not_call_vendor(self):
		existing = object()
		fake_db = SimpleNamespace(exists=Mock(return_value="CSIGN-2026-00001"))
		with patch.object(service.frappe, "db", fake_db):
			with patch.object(service.frappe, "get_doc", return_value=existing) as get_doc:
				with patch.object(service, "TencentESignClient") as vendor:
					result = service.create_contract_signing(
						"入职合同", "HR-EMP-00001", "request-1"
					)
					self.assertIs(result, existing)
					get_doc.assert_called_once_with("Contract Signing", "CSIGN-2026-00001")
					vendor.assert_not_called()


class TestTencentESignCallback(unittest.TestCase):
	def test_signed_encrypted_callback_is_verified_and_decrypted(self):
		from cryptography.hazmat.primitives import padding
		from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

		key = b"TencentEssEncryptTestKey12345678"
		token = "callback-signature-token"
		message = {
			"MsgId": "message-1",
			"MsgType": "FlowStatusChange",
			"MsgData": {"FlowId": "flow-1", "FlowCallbackStatus": 4},
		}
		padder = padding.PKCS7(128).padder()
		padded = padder.update(json.dumps(message).encode()) + padder.finalize()
		encryptor = Cipher(algorithms.AES(key), modes.CBC(key[:16])).encryptor()
		encrypted = encryptor.update(padded) + encryptor.finalize()
		raw_body = json.dumps({"encrypt": base64.b64encode(encrypted).decode()}).encode()
		signature = "sha256=" + hmac.new(token.encode(), raw_body, hashlib.sha256).hexdigest()

		with patch.dict(
			callback.os.environ,
			{
				"TENCENT_ESIGN_CALLBACK_KEY": key.decode(),
				"TENCENT_ESIGN_CALLBACK_TOKEN": token,
			},
		):
			verified, payload = callback.verify_and_decrypt_callback(
				{"Content-Signature": signature}, raw_body
			)
		self.assertTrue(verified)
		self.assertEqual(payload, message)

	def test_invalid_callback_signature_is_rejected(self):
		with patch.dict(
			callback.os.environ,
			{"TENCENT_ESIGN_CALLBACK_TOKEN": "callback-signature-token"},
		):
			with self.assertRaises(callback.CallbackVerificationError):
				callback.verify_and_decrypt_callback(
					{"Content-Signature": "sha256=invalid"}, b'{"MsgId":"message-1"}'
				)
