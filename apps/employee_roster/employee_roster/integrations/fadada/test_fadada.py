from __future__ import annotations

import json
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch

from employee_roster.integrations.fadada import callback, client, service
from employee_roster.tasks import contracts


def config() -> client.FadadaConfig:
	return client.FadadaConfig(
		app_id="app-id",
		app_secret="app-secret",
		server_url="https://example.invalid",
		corp_open_id="corp-open-id",
	)


class TestFadadaSignature(unittest.TestCase):
	def test_signature_matches_official_sdk_algorithm_vector(self):
		parameters = {
			"X-FASC-App-Id": "app-id",
			"X-FASC-Sign-Type": "HMAC-SHA256",
			"X-FASC-Timestamp": "1660000000123",
			"X-FASC-Nonce": "0123456789abcdef0123456789abcdef",
			"X-FASC-Api-SubVersion": "5.1",
			"X-FASC-AccessToken": "token",
			"bizContent": "Alice",
		}
		self.assertEqual(
			client.calculate_signature(parameters, "1660000000123", "app-secret"),
			"37e2dd3277c7fd3618257b09a7cde544f7d07208fb2791666738236dd3aeabde",
		)


class TestFadadaTokenCache(unittest.TestCase):
	def test_cached_token_avoids_http_request(self):
		cache = SimpleNamespace(
			get_value=Mock(return_value=b"cached-token"), set_value=Mock()
		)
		api = client.FadadaClient(config(), session=Mock())
		with patch.object(api, "_cache", return_value=cache):
			self.assertEqual(api.get_access_token(), "cached-token")
		api.session.post.assert_not_called()

	def test_new_token_is_cached_with_safety_margin(self):
		cache = SimpleNamespace(get_value=Mock(return_value=None), set_value=Mock())
		response = Mock()
		response.json.return_value = {
			"code": "100000",
			"data": {"accessToken": "new-token", "expiresIn": 7200},
		}
		response.headers = {}
		session = Mock()
		session.post.return_value = response
		api = client.FadadaClient(config(), session=session)
		with patch.object(api, "_cache", return_value=cache):
			self.assertEqual(api.get_access_token(), "new-token")
		cache.set_value.assert_called_once_with(
			api._token_cache_key(), "new-token", expires_in_sec=6900
		)
		request = session.post.call_args.kwargs
		self.assertEqual(request["data"], {})
		headers = dict(request["headers"])
		signature = headers.pop("X-FASC-Sign")
		self.assertEqual(
			signature,
			client.calculate_signature(
				headers, headers["X-FASC-Timestamp"], "app-secret"
			),
		)

	def test_token_cache_is_scoped_by_app_and_environment(self):
		first = client.FadadaClient(config())
		other = client.FadadaClient(
			client.FadadaConfig(
				app_id="other-app",
				app_secret="secret",
				server_url="https://sandbox.invalid",
				corp_open_id="corp",
			)
		)
		self.assertNotEqual(first._token_cache_key(), other._token_cache_key())

	def test_auth_failure_refreshes_token_only_once(self):
		expired = Mock(status_code=200, headers={})
		expired.json.return_value = {"code": "401", "msg": "expired"}
		success = Mock(status_code=200, headers={})
		success.json.return_value = {"code": "100000", "data": {"value": 1}}
		api = client.FadadaClient(
			config(), session=SimpleNamespace(post=Mock(side_effect=[expired, success]))
		)
		with patch.object(
			api, "get_access_token", side_effect=["old-token", "new-token"]
		) as token:
			self.assertEqual(api._request("/test", {}), {"value": 1})
		self.assertEqual(token.call_count, 2)

	def test_actor_list_falls_back_to_task_detail(self):
		api = client.FadadaClient(config())
		with patch.object(api, "_request", return_value={}), patch.object(
			api,
			"get_detail",
			return_value={"actors": [{"actorInfo": {"actorId": "employee"}}]},
		):
			self.assertEqual(
				api.list_actors("task-1")["actors"][0]["actorInfo"]["actorId"],
				"employee",
			)


class TestFadadaMappingAndIdempotency(unittest.TestCase):
	def test_real_employee_and_contract_values_map_to_actor_and_field_ids(self):
		employee = SimpleNamespace(
			name="HR-EMP-00001",
			employee_name="张三",
			cell_number="13800000000",
			meta=SimpleNamespace(
				has_field=lambda name: name in {"employee_name", "cell_number"}
			),
		)
		template = SimpleNamespace(
			template_name="劳动合同",
			template_id="",
			provider_template_id="template-1",
			field_mapping=json.dumps(
				{
					"employee-name-field": {
						"source": "$employee.employee_name",
						"actor_id": "employee-actor",
						"required": True,
					},
					"start-date-field": {
						"source": "$contract.start_date",
						"actor_id": "employee-actor",
						"required": True,
					},
				}
			),
			actor_config=json.dumps(
				{
					"employee_actor_id": "employee-actor",
					"actors": [
						{
							"actor_id": "employee-actor",
							"name": "$employee.employee_name",
							"mobile": "$employee.cell_number",
						}
					],
				}
			),
			sign_config="{}",
		)
		with patch.object(
			service.FadadaConfig, "load", return_value=config()
		), patch.object(
			service, "now_datetime", return_value=datetime(2026, 9, 9, 10, 0)
		):
			payload = service.build_template_payload(
				template, employee, "request-1", {"start_date": "2026-09-01"}
			)
		actor = payload["actors"][0]
		self.assertEqual(actor["actor"]["actorName"], "张三")
		self.assertEqual(
			actor["actor"]["notification"]["notifyAddress"], "13800000000"
		)
		self.assertEqual(
			actor["fillFields"],
			[
				{"fieldId": "employee-name-field", "fieldValue": "张三"},
				{"fieldId": "start-date-field", "fieldValue": "2026-09-01"},
			],
		)
		self.assertEqual(payload["transReferenceId"], "request-1")
		self.assertNotIn("businessScene", payload)

	def test_required_field_is_validated_before_vendor_call(self):
		employee = SimpleNamespace(
			employee_name="张三",
			cell_number="13800000000",
			meta=SimpleNamespace(has_field=lambda _name: True),
		)
		with self.assertRaisesRegex(Exception, "必填模板控件"):
			service._normalise_field(
				"start-date",
				{"source": "$contract.start_date", "required": True},
				employee,
				{},
			)

	def test_existing_trans_reference_does_not_call_vendor(self):
		existing = SimpleNamespace(
			employee="HR-EMP-00001",
			sign_template="入职合同",
			provider="Fadada",
			sign_task_id="task-1",
			status="Completed",
		)
		with patch.object(
			service.frappe,
			"db",
			SimpleNamespace(exists=Mock(return_value="CSIGN-2026-00001")),
		), patch.object(service.frappe, "get_doc", return_value=existing), patch.object(
			service, "FadadaClient"
		) as vendor:
			result = service.create_contract_signing(
				"入职合同", "HR-EMP-00001", "request-1"
			)
		self.assertIs(result, existing)
		vendor.assert_not_called()


class TestFadadaStatusAndCallback(unittest.TestCase):
	def test_status_mapping(self):
		self.assertEqual(service.map_vendor_status("task_finished"), "Completed")
		self.assertEqual(service.map_vendor_status("sign_completed"), "Pending")
		self.assertEqual(service.map_vendor_phase("sign_completed"), "Finishing")
		self.assertEqual(service.map_vendor_status("sign_progress"), "Signing")
		self.assertEqual(
			service.map_vendor_status("task_terminated", "sign_rejected"), "Rejected"
		)

	def test_callback_rejects_invalid_signature(self):
		biz_content = '{"signTaskId":"task-1","signTaskStatus":"task_finished"}'
		headers = {
			"X-FASC-App-Id": "app-id",
			"X-FASC-Sign-Type": "HMAC-SHA256",
			"X-FASC-Timestamp": "1660000000123",
			"X-FASC-Nonce": "nonce",
			"X-FASC-Event": "sign-task-signed",
			"X-FASC-Sign": "invalid",
		}
		with self.assertRaises(callback.CallbackVerificationError):
			callback.verify_callback(headers, biz_content.encode(), config())

	def test_callback_uses_exact_biz_content_for_signature(self):
		biz_content = '{ "signTaskId": "task-1", "signTaskStatus": "task_finished" }'
		timestamp = str(int(callback.time.time() * 1000))
		headers = {
			"X-FASC-App-Id": "app-id",
			"X-FASC-Sign-Type": "HMAC-SHA256",
			"X-FASC-Timestamp": timestamp,
			"X-FASC-Nonce": "nonce",
			"X-FASC-Event": "sign-task-signed",
		}
		parameters = dict(headers)
		parameters["bizContent"] = biz_content
		headers["X-FASC-Sign"] = client.calculate_signature(
			parameters, headers["X-FASC-Timestamp"], "app-secret"
		)
		with patch.object(callback.frappe, "cache") as cache:
			cache.get_value.return_value = None
			event, payload = callback.verify_callback(
				headers, biz_content.encode(), config()
			)
			cache.set_value.assert_called_once()
		self.assertEqual(event, "sign-task-signed")
		self.assertEqual(payload["signTaskId"], "task-1")

	def test_callback_event_key_is_stable_for_retries(self):
		payload = {
			"signTaskId": "task-1",
			"eventTime": "2026-09-09 10:00:00",
			"signTaskStatus": "task_finished",
		}
		self.assertEqual(
			callback._event_key("sign-task-signed", payload),
			callback._event_key("sign-task-signed", dict(payload)),
		)


class TestFadadaProductionClosure(unittest.TestCase):
	def test_employee_first_company_seal_payload(self):
		employee = SimpleNamespace(
			employee_name="张三",
			cell_number="13800000000",
			meta=SimpleNamespace(has_field=lambda _name: True),
		)
		template = SimpleNamespace(
			template_name="劳动合同",
			template_id="",
			provider_template_id="template-1",
			field_mapping="{}",
			employee_actor_id="employee",
			corp_actor_id="company",
			seal_id="1788917204318166024",
			business_id="hrms_labor_contract",
			actor_config=json.dumps(
				{
					"actors": [
						{
							"actor": {
								"actorId": "employee",
								"actorType": "person",
								"actorName": "$employee.employee_name",
								"actorOpenId": "person-open-id",
							},
							"signConfigInfo": {"orderNo": 1},
						},
						{
							"actor": {
								"actorId": "company",
								"actorType": "corp",
								"actorName": "依然集团",
							},
							"signConfigInfo": {"orderNo": 2},
							"signFields": [{"fieldId": "company-seal"}],
						},
					]
				}
			),
			sign_config="{}",
		)
		with patch.object(
			service.FadadaConfig, "load", return_value=config()
		), patch.object(
			service, "now_datetime", return_value=datetime(2026, 9, 9, 10, 0)
		):
			payload = service.build_template_payload(
				template,
				employee,
				"request-1",
				{},
				enable_company_free_sign=True,
			)
		self.assertTrue(payload["signInOrder"])
		self.assertEqual(payload["businessId"], "hrms_labor_contract")
		self.assertEqual(payload["freeSignType"], "business")
		self.assertTrue(payload["actors"][1]["signConfigInfo"]["requestVerifyFree"])
		self.assertEqual(
			payload["actors"][1]["signFields"][0]["sealId"],
			1788917204318166024,
		)
		template.business_id = ""
		manual_payload = service.build_template_payload(
			template, employee, "request-2", {}
		)
		self.assertNotIn("businessId", manual_payload)
		self.assertNotIn("freeSignType", manual_payload)
		self.assertFalse(
			manual_payload["actors"][1]["signConfigInfo"]["requestVerifyFree"]
		)
		service.assert_signing_ready(template, manual_payload)

	def test_free_sign_authorization_must_match_seal_and_business(self):
		template = SimpleNamespace(seal_id="100", business_id="labor")
		api = SimpleNamespace(
			config=config(),
			list_seals=Mock(
				return_value={
					"sealInfos": [
						{
							"sealId": "100",
							"sealStatus": "enable",
							"freeSignInfos": [
								{"businessId": "labor", "grantStatus": "effective"}
							],
						}
					]
				}
			),
		)
		self.assertTrue(service._free_sign_authorized(template, api))
		template.business_id = "other"
		self.assertFalse(service._free_sign_authorized(template, api))

	def test_remote_template_must_enforce_employee_before_company(self):
		valid = {
			"signInOrder": True,
			"actors": [
				{"actorInfo": {"actorId": "employee"}, "signOrderNo": 1},
				{"actorInfo": {"actorId": "company"}, "signOrderNo": 2},
			],
		}
		service.assert_remote_sign_order(valid, "employee", "company")
		with self.assertRaisesRegex(Exception, "未启用顺序签署"):
			service.assert_remote_sign_order(
				{**valid, "signInOrder": False}, "employee", "company"
			)

	def test_same_signed_callback_retry_is_allowed(self):
		biz_content = '{"signTaskId":"task-1"}'
		timestamp = str(int(callback.time.time() * 1000))
		headers = {
			"X-FASC-App-Id": "app-id",
			"X-FASC-Sign-Type": "HMAC-SHA256",
			"X-FASC-Timestamp": timestamp,
			"X-FASC-Nonce": "retry-nonce",
			"X-FASC-Event": "sign-task-signed",
		}
		parameters = dict(headers)
		parameters["bizContent"] = biz_content
		headers["X-FASC-Sign"] = client.calculate_signature(
			parameters, timestamp, "app-secret"
		)
		cache = Mock()
		nonce_value = callback.hashlib.sha256(
			f"sign-task-signed|{biz_content}|{headers['X-FASC-Sign']}".encode()
		).hexdigest()
		cache.get_value.side_effect = [None, nonce_value]
		with patch.object(callback.frappe, "cache", cache):
			callback.verify_callback(headers, biz_content.encode(), config())
			callback.verify_callback(headers, biz_content.encode(), config())

	def test_scheduler_continues_after_one_sync_failure(self):
		with patch.object(
			contracts.frappe,
			"get_all",
			return_value=["CSIGN-1", "CSIGN-2"],
		), patch.object(
			contracts.frappe,
			"get_doc",
			side_effect=[RuntimeError("boom"), SimpleNamespace(next_retry_on=None)],
		), patch.object(
			contracts, "_log_failure"
		) as log_failure, patch.object(
			service, "sync_contract_status"
		) as sync:
			contracts.reconcile_contracts()
		self.assertEqual(log_failure.call_count, 1)
		self.assertEqual(sync.call_count, 1)
