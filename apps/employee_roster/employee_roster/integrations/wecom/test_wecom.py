# Copyright (c) 2026 stillgroup
# License: MIT
from datetime import date
from unittest import TestCase
from unittest.mock import MagicMock, patch

from employee_roster.integrations.wecom.attendance import (
	_day_datetime,
	_log_type,
	_record_id,
)
from employee_roster.integrations.wecom.oauth import (
	DEFAULT_NEXT_PATH,
	build_web_login_url,
	decode_oauth_state,
	encode_oauth_state,
	sanitize_next_path,
	web_login_panel_params,
)
from employee_roster.integrations.wecom.service import (
	_approval_action_path,
	notify_system_users,
	send_textcard,
)


class TestWeComAttendanceMapping(TestCase):
	def test_log_type_mapping(self):
		self.assertEqual(_log_type("上班打卡"), "IN")
		self.assertEqual(_log_type("下班打卡"), "OUT")
		self.assertEqual(_log_type("外出打卡"), "")

	def test_record_id_is_stable_and_sensitive_to_time(self):
		row = {
			"userid": "zhangsan",
			"checkin_time": 1789002000,
			"checkin_type": "上班打卡",
			"deviceid": "device-1",
			"groupid": 1,
		}
		self.assertEqual(_record_id(row), _record_id(dict(row)))
		changed = {**row, "checkin_time": row["checkin_time"] + 1}
		self.assertNotEqual(_record_id(row), _record_id(changed))

	def test_day_datetime_uses_seconds_from_midnight(self):
		value = _day_datetime(date(2026, 9, 10), 9 * 3600 + 30 * 60)
		self.assertEqual(value.isoformat(), "2026-09-10T09:30:00")


class TestWeComOAuthState(TestCase):
	def test_sanitize_rejects_open_redirect(self):
		self.assertEqual(sanitize_next_path("https://evil.example"), DEFAULT_NEXT_PATH)
		self.assertEqual(sanitize_next_path("//evil.example"), DEFAULT_NEXT_PATH)
		self.assertEqual(sanitize_next_path("/login"), DEFAULT_NEXT_PATH)
		self.assertEqual(
			sanitize_next_path("/app/approval-workspace?instance=A-1"),
			"/app/approval-workspace?instance=A-1",
		)

	def test_state_roundtrip(self):
		config = MagicMock(
			corp_id="wwtest",
			app_secret="secret",
			agent_id=1000002,
			oauth_base_url="https://hr.example.com",
		)
		state = encode_oauth_state("/app/hr-home", config=config)
		self.assertEqual(decode_oauth_state(state, config=config), "/app/hr-home")
		self.assertEqual(decode_oauth_state("tampered.state", config=config), DEFAULT_NEXT_PATH)

	def test_web_login_url_and_panel(self):
		config = MagicMock(
			corp_id="wwtest",
			app_secret="secret",
			agent_id=1000002,
			oauth_base_url="https://hr.example.com",
		)
		url = build_web_login_url(next_path="/app/hr-home", config=config)
		self.assertIn("login.work.weixin.qq.com/wwlogin/sso/login", url)
		self.assertIn("login_type=CorpApp", url)
		self.assertIn("appid=wwtest", url)
		panel = web_login_panel_params(next_path="/app/hr-home", config=config)
		self.assertEqual(panel["login_type"], "CorpApp")
		self.assertEqual(panel["appid"], "wwtest")
		self.assertEqual(panel["agentid"], "1000002")
		self.assertEqual(panel["redirect_uri"], "https://hr.example.com/wecom_login")
		self.assertEqual(panel["redirect_type"], "callback")


class TestWeComNotifyCard(TestCase):
	def test_approval_action_path(self):
		self.assertEqual(
			_approval_action_path("Approval Instance", "AI-1"),
			"/app/approval-workspace?instance=AI-1",
		)
		self.assertEqual(
			_approval_action_path("Approval Task", "AT-1"),
			"/app/approval-workspace?task=AT-1",
		)

	@patch("employee_roster.integrations.wecom.service.WeComClient")
	def test_send_textcard_payload(self, client_cls):
		client = client_cls.return_value
		client.config.agent_id = 1000002
		client.send_message.return_value = {"errcode": 0}
		send_textcard(
			"zhangsan",
			title="待审批",
			description="请处理",
			url="https://hr.example.com/wecom_login",
			btntxt="打开处理",
		)
		payload = client.send_message.call_args.args[0]
		self.assertEqual(payload["msgtype"], "textcard")
		self.assertEqual(payload["textcard"]["title"], "待审批")
		self.assertEqual(payload["textcard"]["url"], "https://hr.example.com/wecom_login")

	@patch("employee_roster.integrations.wecom.service.send_text")
	@patch("employee_roster.integrations.wecom.service.send_textcard")
	@patch("employee_roster.integrations.wecom.service.frappe")
	def test_notify_falls_back_to_text(self, frappe_mod, send_card, send_text_fn):
		frappe_mod.get_all.return_value = ["wx-1"]
		send_card.side_effect = RuntimeError("card failed")
		with patch(
			"employee_roster.integrations.wecom.oauth.build_authorize_url",
			return_value="https://open.weixin.qq.com/x",
		):
			notify_system_users(
				["user@example.com"],
				subject="待审批：请假",
				message="你有一条新的审批待办",
				document_type="Approval Instance",
				document_name="AI-1",
			)
		send_text_fn.assert_called_once()

	@patch("employee_roster.integrations.wecom.service.frappe")
	def test_notify_skips_when_no_wecom_id(self, frappe_mod):
		frappe_mod.get_all.return_value = []
		# 不应抛错
		notify_system_users(["user@example.com"], subject="x", message="y")
