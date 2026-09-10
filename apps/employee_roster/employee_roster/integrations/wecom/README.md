# 企业微信阶段 1/2 配置

在站点 `site_config.json` 配置（不要提交 Secret）：

```json
{
  "wecom_corp_id": "wwxxxxxxxx",
  "wecom_agent_id": 1000002,
  "wecom_app_secret": "...",
  "wecom_contact_secret": "...",
  "wecom_default_company": "公司全称",
  "wecom_robot_webhook": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=..."
}
```

- `wecom_contact_secret`：通讯录同步 Secret，阶段 1 全量部门和成员 ID 必需。
- `wecom_app_secret`：自建应用 Secret；应用须覆盖需要同步/通知的成员。
- 打卡使用自建应用 Secret；管理员须在「打卡 → 可调用接口的应用」中授权该应用。
- 如果另有专用打卡 Secret，可配置 `wecom_checkin_secret`。
- `wecom_create_missing_employees` 默认关闭；打开后才会为企微中未匹配的成员创建 Employee。

管理接口（均要求 HR Manager，写操作仅接受 POST）：

- 配置诊断：`employee_roster.integrations.wecom.api.get_configuration_status`
- 部门/成员同步：`employee_roster.integrations.wecom.api.run_contact_sync`
- 存量手机号绑定：`employee_roster.integrations.wecom.api.bind_existing_employees`
- 考勤与月报同步：`employee_roster.integrations.wecom.api.run_attendance_sync`
- 应用消息测试：`employee_roster.integrations.wecom.api.send_test_message`
- 群机器人测试：`employee_roster.integrations.wecom.api.send_test_robot_message`

手机号绑定单次默认最多 100 人，且只请求格式正确的大陆手机号，以降低企微错误率封禁风险。
考勤同步不会覆盖人工创建的 Attendance；月度扣款只生成草稿，须由 HR 复核后提交。
