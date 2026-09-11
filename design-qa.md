# 组织架构页 Design QA

- Source visual truth: `/Users/fancy/Documents/YiRan/yiran-hrms/other/组织架构重构预览-v2.png`
- Browser implementation screenshot: `/Users/fancy/Documents/YiRan/yiran-hrms/other/组织架构满高布局-v4.jpg`
- Combined comparison: `/Users/fancy/Documents/YiRan/yiran-hrms/other/组织架构设计对比-v4.jpg`
- Route: `http://localhost:8080/desk/orgchart`
- State: 已登录、亮色主题、默认公司、总经办、全量组织树展开
- Source pixels: 1668 × 943 PNG
- Implementation pixels: 1470 × 653 JPEG
- Normalization: 源稿等比缩放到 653px 高后，与实现截图并排比较；实现根据用户后续反馈进一步减少操作层级，因此不把源稿独立标题/工具栏视为必须保留元素。

## Full-view comparison evidence

- 页面使用单一主卡片，左侧组织树、右侧组织详情和成员表保持清晰的 36/64 分栏关系。
- 独立标题统计条和独立工具栏均已移除，搜索/筛选收进左侧头部，当前组织及操作收进右侧头部。
- 主卡片高度跟随剩余视口延伸，实测底部仅保留 9px 页面安全间距，不再出现大块空白。

## Focused region comparison evidence

- 左侧树：当前验收视口可视高度 462px、`overflow-y: auto`，可独立浏览全公司组织。
- 右侧成员区：当前验收视口可视高度 390px、`overflow-y: auto`；少量成员时内容高度等于容器高度，不产生无意义滚动。
- 两侧头部高度均为 63px，视觉基线一致。
- 当前组织头部仅显示组织名、类型、成员数、负责人设置、新增和更多；编辑、批量、展开/收起、导出、刷新收纳进更多菜单。

## Interaction and accessibility

- 搜索、筛选、新增菜单、更多菜单和负责人设置均在浏览器实际点击验证。
- 新增菜单保留“新增当前下级”和“新增一级组织”；更多菜单保留编辑、批量、展开/收起、导出和刷新。
- 图标按钮具有中文 `aria-label` 和提示文本；主要操作仍有文字标签。
- 页面请求和组织树接口均返回 HTTP 200，未发现本次改造引入的运行时错误。

## Findings

- P0: none.
- P1: none.
- P2: none.
- P3: 与最初源稿相比，最终实现按用户反馈进一步减少了标题统计和按钮文字，是有意的简化差异。

## Comparison history

- Pass 1: 将列表重构为组织树 + 详情成员区。
- Pass 2: 修复左树滚动、两侧头部对齐和成员区自适应滚动。
- Pass 3: 工具栏并入主卡片。
- Pass 4: 移除冗余标题统计层，搜索/筛选和操作分别收纳到两侧头部，并将卡片延伸到底部。
- Pass 5: 修正视口高度扣减，卡片底部间距由约 80px 收紧至 9px。

## Verification

- [x] Vue 生产构建
- [x] 现有前端测试 3/3
- [x] Git diff whitespace 检查
- [x] 浏览器视觉与交互验证
- [x] 参考图与实现图同画面对照

final result: passed

---

# 员工花名册 Design QA

- Source visual truth: `/Users/fancy/Documents/YiRan/yiran-hrms/other/员工花名册平衡工具栏预览-v4.png`
- Browser implementation evidence: Codex CUA 当前轮次 Chrome 全页截图
- Route: `http://localhost:8080/desk/employee`
- State: 已登录、亮色主题、全部员工、搜索为空、首次懒加载批次
- Source pixels: 1584 × 992 PNG
- Implementation viewport: 1470 × 653 CSS pixels
- Normalization: 对照员工名录主卡片区域，忽略浏览器外壳与不同视口造成的可见行数差异。

## Full-view comparison evidence

- 原先分离的筛选条、状态卡片、表格卡片合并为一个 Arco 员工名录工作区，页面层级与原型一致。
- 标题、员工总数、新增入口位于首行；状态导航、适中宽度搜索框和单一筛选入口位于第二行。
- 已移除“停用”状态入口和原生分页，表格直接承接工具栏，整体密度与留白平衡。

## Focused region comparison evidence

- 搜索框未占满工具栏，保留明确的状态区和筛选入口边界。
- 员工姓名使用蓝色链接；行悬停出现浅蓝底色和链接下划线。
- 列表首次渲染 30 条，滚动到加载哨兵后追加到 60 条；不显示分页器。
- 表格保留员工、任职、组别、分支机构、雇佣类型、入职日期、联系方式和操作信息。

## Interaction and accessibility

- 搜索“安楷”得到 1 条记录，清空后恢复全部列表。
- 点击“安楷”进入 `/desk/employee/HR-EMP-00152#basic_details_tab`。
- 筛选按钮继续复用 Frappe 现有筛选能力；新增员工、刷新名录和状态筛选均接入现有业务逻辑。
- 删除入口只对已离职员工显示，继续执行“先离职、后删除”的既有约束。
- 状态筛选使用 tab 语义，按钮和搜索框均提供中文辅助标签。

## Findings

- P0: none.
- P1: none.
- P2: none.
- P3: 浏览器日志中仍有改造前已存在的 `apps_screen.js` 初始化错误和 Socket.IO 未授权信息；本次员工花名册资源未产生新增错误。

## Verification

- [x] Arco Vue 生产构建
- [x] 现有前端测试 4/4
- [x] Git diff whitespace 检查
- [x] 浏览器搜索、清空和状态恢复验证
- [x] 浏览器懒加载 30 → 60 条验证
- [x] 员工姓名跳转详情验证
- [x] 参考原型与实现主卡片区域视觉对照

final result: passed

---

# 人员角色分配 Design QA

- Source visual truth: `/Users/fancy/Documents/YiRan/yiran-hrms/other/人员角色分配原型-v5-可扩展角色列表.png`
- Browser implementation screenshot: `/Users/fancy/Documents/YiRan/yiran-hrms/other/人员角色分配页面-实现验证.jpg`
- Combined comparison: `/Users/fancy/Documents/YiRan/yiran-hrms/other/人员角色分配-原型与实现对比.jpg`
- Route: `http://localhost:8080/desk/role-assignment`
- State: 已登录、亮色主题、深圳市依然电商科技有限公司、AI部 / ITBP组、杨志武
- Source pixels: 1672 × 941 PNG
- Implementation viewport: 1440 × 900 CSS pixels

## Full-view comparison evidence

- 页面按组织架构、组织成员、角色分配三级联动排版，与选定原型一致。
- 使用现有 HR Pro 浅色顶栏、侧栏及 Arco Design 控件，中文标题、搜索、筛选、状态与提示完整。
- 三列工作区填满剩余视口，各列内容独立滚动；窄窗口通过横向滚动保留完整功能，不再裁切角色区。

## Interaction and accessibility

- 实际点击 ITBP组后，成员列表自动定位到已绑定账号的杨志武，并正确回显“普通员工”。
- 角色勾选后取消可恢复原值；成员复选和“批量分配”入口工作正常。
- 单人保存和批量保存接口均使用杨志武当前角色完成等值写入，返回成功且刷新后状态不变。
- 未绑定登录账号的员工显示“未绑定账号”并禁止选择；平台超级管理员不出现在企业可分配角色中。

## Findings

- P0: none.
- P1: none.
- P2: none.
- P3: none.

## Verification

- [x] Vue 类型检查与生产构建
- [x] 前端测试 4/4
- [x] 权限测试 7/7
- [x] 员工中心回归 4/4
- [x] 员工生命周期回归 2/2
- [x] 组织同级重名规则回归 2/2
- [x] 浏览器视觉、单选、批量选择和角色回显验证
- [x] 参考图与实现图同画面对照
- [x] Git diff whitespace 检查

final result: passed
