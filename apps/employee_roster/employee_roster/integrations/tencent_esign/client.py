"""腾讯云 ESS v20201111 SDK 的窄封装。

密钥只从 site_config 或环境变量读取, 不写入数据库。所有 SDK 导入均延迟到
实际调用时, 因此未安装依赖或未配置凭据的站点仍可安全加载应用。
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any

import frappe


class ConfigurationError(RuntimeError):
	"""腾讯电子签未正确配置。"""


@dataclass(frozen=True)
class TencentESignConfig:
	secret_id: str
	secret_key: str
	operator_user_id: str
	region: str = "ap-guangzhou"
	endpoint: str = "ess.tencentcloudapi.com"
	proxy_organization_id: str = ""
	callback_key: str = ""
	callback_token: str = ""

	@classmethod
	def load(cls) -> TencentESignConfig:
		def value(name: str, default: str = "") -> str:
			env_name = f"TENCENT_ESIGN_{name.upper()}"
			return str(os.getenv(env_name) or frappe.conf.get(f"tencent_esign_{name}") or default).strip()

		config = cls(
			secret_id=value("secret_id"),
			secret_key=value("secret_key"),
			operator_user_id=value("operator_user_id"),
			region=value("region", "ap-guangzhou"),
			endpoint=value("endpoint", "ess.tencentcloudapi.com"),
			proxy_organization_id=value("proxy_organization_id"),
			callback_key=value("callback_key"),
			callback_token=value("callback_token"),
		)
		missing = config.missing_fields()
		if missing:
			raise ConfigurationError(f"腾讯电子签配置缺失: {', '.join(missing)}")
		return config

	def missing_fields(self) -> list[str]:
		return [
			name
			for name, value in (
				("secret_id", self.secret_id),
				("secret_key", self.secret_key),
				("operator_user_id", self.operator_user_id),
			)
			if not value
		]


def configuration_status() -> dict[str, Any]:
	"""返回不含敏感值的配置状态。"""
	try:
		config = TencentESignConfig.load()
	except ConfigurationError as exc:
		return {"configured": False, "message": str(exc)}
	return {
		"configured": True,
		"region": config.region,
		"endpoint": config.endpoint,
		"proxy_organization_configured": bool(config.proxy_organization_id),
		"callback_encryption_configured": bool(config.callback_key),
		"callback_signature_configured": bool(config.callback_token),
	}


class TencentESignClient:
	"""只暴露本应用需要的 ESS v20201111 接口。"""

	def __init__(self, config: TencentESignConfig | None = None):
		self.config = config or TencentESignConfig.load()
		self._client: Any | None = None

	def _sdk_client(self) -> Any:
		if self._client is not None:
			return self._client
		try:
			from tencentcloud.common import credential
			from tencentcloud.common.profile.client_profile import ClientProfile
			from tencentcloud.common.profile.http_profile import HttpProfile
			from tencentcloud.ess.v20201111 import ess_client
		except ImportError as exc:
			raise ConfigurationError("腾讯电子签 SDK 未安装, 请安装项目依赖") from exc

		http_profile = HttpProfile(endpoint=self.config.endpoint)
		client_profile = ClientProfile(httpProfile=http_profile)
		cred = credential.Credential(self.config.secret_id, self.config.secret_key)
		self._client = ess_client.EssClient(cred, self.config.region, client_profile)
		return self._client

	def _operator(self) -> dict[str, str]:
		return {"UserId": self.config.operator_user_id}

	def _agent(self) -> dict[str, str] | None:
		if not self.config.proxy_organization_id:
			return None
		return {"ProxyOrganizationId": self.config.proxy_organization_id}

	def _base(self) -> dict[str, Any]:
		payload: dict[str, Any] = {"Operator": self._operator()}
		if agent := self._agent():
			payload["Agent"] = agent
		return payload

	def _invoke(self, method: str, request_class: str, payload: dict[str, Any]) -> dict[str, Any]:
		try:
			from tencentcloud.ess.v20201111 import models
		except ImportError as exc:
			raise ConfigurationError("腾讯电子签 SDK 未安装, 请安装项目依赖") from exc
		request = getattr(models, request_class)()
		request.from_json_string(json.dumps(payload, ensure_ascii=False))
		response = getattr(self._sdk_client(), method)(request)
		return json.loads(response.to_json_string())

	def create_flow(
		self,
		*,
		flow_name: str,
		approvers: list[dict[str, Any]],
		flow_type: str = "",
		description: str = "",
		deadline: int | None = None,
		unordered: bool = False,
		user_data: str = "",
	) -> dict[str, Any]:
		payload = self._base() | {
			"FlowName": flow_name,
			"Approvers": approvers,
			"Unordered": unordered,
		}
		if flow_type:
			payload["FlowType"] = flow_type
		if description:
			payload["FlowDescription"] = description
		if deadline:
			payload["DeadLine"] = deadline
		if user_data:
			payload["UserData"] = user_data
		return self._invoke("CreateFlow", "CreateFlowRequest", payload)

	def create_document(
		self,
		*,
		template_id: str,
		flow_id: str,
		form_fields: list[dict[str, Any]],
		need_preview: bool = False,
		file_name: str = "",
	) -> dict[str, Any]:
		payload = self._base() | {
			"TemplateId": template_id,
			"FlowId": flow_id,
			"FormFields": form_fields,
			"NeedPreview": need_preview,
			"PreviewType": 1,
		}
		if file_name:
			payload["FileNames"] = [file_name]
		return self._invoke("CreateDocument", "CreateDocumentRequest", payload)

	def start_flow(self, flow_id: str) -> dict[str, Any]:
		return self._invoke("StartFlow", "StartFlowRequest", self._base() | {"FlowId": flow_id})

	def create_sign_url(
		self,
		flow_id: str,
		approvers: list[dict[str, Any]],
		*,
		jump_url: str = "",
		expired_on: int = 1800,
		preview: bool = False,
	) -> dict[str, Any]:
		payload = self._base() | {
			"FlowId": flow_id,
			"FlowApproverInfos": approvers,
			"UrlType": 1 if preview else 0,
			"ExpiredOn": expired_on,
		}
		if jump_url:
			payload["JumpUrl"] = jump_url
		return self._invoke("CreateFlowSignUrl", "CreateFlowSignUrlRequest", payload)

	def create_scheme_url(self, payload: dict[str, Any]) -> dict[str, Any]:
		"""生成腾讯电子签小程序跳转链接; 调用方需传官方 CreateSchemeUrl 参数。"""
		return self._invoke("CreateSchemeUrl", "CreateSchemeUrlRequest", self._base() | payload)

	def describe_flow_info(self, flow_ids: list[str]) -> dict[str, Any]:
		return self._invoke(
			"DescribeFlowInfo", "DescribeFlowInfoRequest", self._base() | {"FlowIds": flow_ids}
		)

	def cancel_flow(self, flow_id: str, reason: str) -> dict[str, Any]:
		return self._invoke(
			"CancelFlow",
			"CancelFlowRequest",
			self._base() | {"FlowId": flow_id, "CancelMessage": reason[:200]},
		)

	def remind_flow(self, flow_id: str, remind_types: list[str] | None = None) -> dict[str, Any]:
		payload = self._base() | {"FlowIds": [flow_id]}
		if remind_types:
			payload["RemindTypes"] = remind_types
		return self._invoke("CreateFlowReminds", "CreateFlowRemindsRequest", payload)

	def describe_file_urls(
		self, flow_id: str, *, file_type: str = "PDF", url_ttl: int = 300
	) -> dict[str, Any]:
		return self._invoke(
			"DescribeFileUrls",
			"DescribeFileUrlsRequest",
			self._base()
			| {
				"BusinessType": "FLOW",
				"BusinessIds": [flow_id],
				"FileType": file_type,
				"UrlTtl": max(1, min(url_ttl, 86400)),
			},
		)
