# 企业微信阶段 1/2/3B/4 配置

在站点 `site_config.json` 配置（不要在本文档或 Git 中保存真实 Secret）：

```json
{
  "wecom_corp_id": "wwxxxxxxxx",
  "wecom_agent_id": 1000002,
  "wecom_app_secret": "<自建应用 Secret>",
  "wecom_contact_secret": "<通讯录同步 Secret>",
  "wecom_default_company": "公司全称",
  "wecom_robot_webhook": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=<机器人 Key>",
  "wecom_oauth_base_url": "https://hr.example.com"
}
```

- `wecom_contact_secret`：通讯录同步 Secret，阶段 1 全量部门和成员 ID 必需。
- `wecom_app_secret`：自建应用 Secret；应用须覆盖需要同步/通知的成员。
- 打卡使用自建应用 Secret；管理员须在「打卡 → 可调用接口的应用」中授权该应用。
- 如果另有专用打卡 Secret，可配置 `wecom_checkin_secret`。
- `wecom_create_missing_employees` 默认关闭；打开后才会为企微中未匹配的成员创建 Employee。
- `wecom_oauth_base_url`：免登/扫码回调使用的公网根地址（须在企微应用配置为「OAuth / Web 登录」可信域名，通常需 ICP 备案）。未配置时回退 `get_url()`；localhost 只能验证代码路径，无法完成真实企微授权。

## 阶段能力

| 阶段 | 内容 |
|------|------|
| 1 | 通讯录同步、手机号绑定、应用消息 / 群机器人 |
| 2 | 打卡流水 / 日报 / 月报回流、扣款草稿 |
| 3B | 自研审批引擎保留；企微发 textcard，深链走免登再进审批工作区 |
| 4 | 网页授权免登 + PC 扫码登录 |

### 免登 / 扫码登录

- 移动端免登入口：`/wecom_login`（可带 `?next=/app/hr-home`）
- PC 扫码：登录页内嵌 WwLogin 二维码；失败时回退「企业微信扫码登录」跳转按钮
- 回调（轻量 API，避免 Website 整页渲染）：
  `/api/method/employee_roster.integrations.wecom.api.wecom_sso_callback`
- 扫码成功默认直接进入 `/desk/hr-home`（与账密登录一致）；`/wecom_home` 仍可用作可选轻量入口，但不再作为默认跳转
- 登录后会异步预热该用户的 Desk boot 缓存，便于同会话内再次打开 Desk 页面
- Desk 首屏等待主要来自 `bootinfo` + 静态资源；生产请走 nginx + gunicorn（见 `deploy/`），开发/穿透环境也已对 JS/CSS/JSON/HTML 做 gzip
- 流程：`code` → `auth/getuserinfo` → `Employee.hr_wecom_id` → 关联 User 登录 → Desk 目标页
- 前提：员工已绑定 `hr_wecom_id`，且 Employee 已关联启用的系统 User；不会自动建号
- 企微「授权回调域名」仍配置主机（可含端口），例如 `xx.stillgroup.net:8088`；与回调路径无关

说明：扫码比账密「感觉更慢」，通常不是因为多了一层落地页，而是扫码每次都是新会话，第一次进 Desk 必须现算 `bootinfo`；账密登录若浏览器里已有静态资源缓存，体感会好一些。

管理接口（写操作仅接受 POST；标 * 的允许 Guest）：

- 配置诊断：`employee_roster.integrations.wecom.api.get_configuration_status`
- 连通性探测：`employee_roster.integrations.wecom.api.get_connection_status`
- 免登/扫码链接：`employee_roster.integrations.wecom.api.get_oauth_entry_url`
- * 登录页扫码配置：`employee_roster.integrations.wecom.api.get_web_login_config`
- * 扫码 code 换会话：`employee_roster.integrations.wecom.api.complete_wecom_login`
- 部门/成员同步：`employee_roster.integrations.wecom.api.run_contact_sync`
- 存量手机号绑定：`employee_roster.integrations.wecom.api.bind_existing_employees`
- 考勤与月报同步：`employee_roster.integrations.wecom.api.run_attendance_sync`
- 应用消息测试：`employee_roster.integrations.wecom.api.send_test_message`
- 卡片消息测试：`employee_roster.integrations.wecom.api.send_test_textcard`
- 群机器人测试：`employee_roster.integrations.wecom.api.send_test_robot_message`

手机号绑定单次默认最多 100 人，且只请求格式正确的大陆手机号，以降低企微错误率封禁风险。
考勤同步不会覆盖人工创建的 Attendance；月度扣款只生成草稿，须由 HR 复核后提交。
审批企微通知失败不会阻断审批主流程。
