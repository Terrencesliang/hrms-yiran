/**
 * Attendance Deduction Rule — custom edit shell (参考 WorkBuddy 表单主内容区)
 * 仅绑定真实字段：rule_name / is_active / description / rule_items / rule_tiers
 */
frappe.provide("employee_roster.adr_form");

(function () {
	const CSS = "/assets/employee_roster/css/attendance_deduction_rule_form.css?v=20260303b";

	const TYPE_LABEL = {
		"Late Entry": "迟到",
		"Early Exit": "早退",
		"Missing Punch": "缺卡",
		Absent: "旷工",
	};
	const MODE_LABEL = {
		Tiered: "按阶梯计算",
		"Per Minute": "按分钟",
		None: "不扣款",
		"Salary Percent": "薪资比例",
	};
	const UNIT_LABEL = {
		"Per Occurrence Minutes": "分钟/次",
		"Monthly Count": "次/月",
		"Occurrence Hours": "小时/次",
	};
	const DEDUCT_LABEL = {
		"Fixed Amount": "固定金额",
		"Per Unit Amount": "按单位金额",
	};

	const TIER_BOXES = [
		{
			key: "Late Entry",
			title: "迟到阶梯（按单次迟到时长）",
			default_unit: "Per Occurrence Minutes",
		},
		{
			key: "Early Exit",
			title: "早退阶梯（按单次早退时长）",
			default_unit: "Per Occurrence Minutes",
		},
		{
			key: "Missing Punch",
			title: "缺卡阶梯（按月次数）",
			default_unit: "Monthly Count",
		},
		{
			key: "Absent",
			title: "旷工阶梯（按时长/小时）",
			default_unit: "Occurrence Hours",
		},
	];

	function ensure_css() {
		const href = CSS;
		if (document.querySelector(`link[href="${href}"]`)) return;
		const link = document.createElement("link");
		link.rel = "stylesheet";
		link.href = href;
		document.head.appendChild(link);
	}

	function hide_frappe_chrome(frm) {
		document.body.classList.add("adr-form-active");
		const $wrap = frm.page && frm.page.wrapper ? $(frm.page.wrapper) : $(document);
		$wrap
			.find(
				".page-head, .layout-side-section, .form-dashboard, .form-comments, .form-footer, .comment-box, .new-timeline"
			)
			.attr("style", "display:none !important");
		$(".layout-main.layout-two-column").removeClass("layout-two-column");
	}

	function go_rules_list() {
		frappe.set_route("attendance-rules");
	}

	function fmt_num(v) {
		const n = parseFloat(v);
		if (isNaN(n)) return "0.00";
		return n.toFixed(2);
	}

	function range_text(row) {
		const min = parseFloat(row.min_value) || 0;
		const max = parseFloat(row.max_value) || 0;
		if (!max) return `>${min || 0}`;
		return `${min}-${max}`;
	}

	function find_tier_amount(tiers, item_type, value) {
		const list = (tiers || [])
			.filter((t) => t.item_type === item_type)
			.sort((a, b) => (a.min_value || 0) - (b.min_value || 0));
		for (const t of list) {
			const min = parseFloat(t.min_value) || 0;
			const max = parseFloat(t.max_value) || 0;
			if (value >= min && (!max || value <= max)) {
				return { amount: t.amount, mode: "阶梯" };
			}
		}
		return null;
	}

	function item_preview_amount(frm, item_type, sample) {
		const item = (frm.doc.rule_items || []).find((r) => r.item_type === item_type);
		if (!item || !cint(item.enabled)) return null;
		if (item.calc_mode === "None") return { amount: 0, mode: "不扣款" };
		if (item.calc_mode === "Per Minute") {
			const rate = parseFloat(item.rate_per_minute) || 0;
			return { amount: rate * sample, mode: "按分钟" };
		}
		if (item.calc_mode === "Salary Percent") {
			return { amount: null, mode: `薪资 ${item.salary_percent || 0}%` };
		}
		if (item.calc_mode === "Tiered") {
			return find_tier_amount(frm.doc.rule_tiers, item_type, sample);
		}
		return null;
	}

	function restore_fields(frm) {
		const $layout = $(frm.layout.wrapper).closest(".form-layout");
		if (!$layout.length) return;
		["rule_name", "is_active", "description", "rule_items", "rule_tiers"].forEach((fn) => {
			const fd = frm.fields_dict[fn];
			if (fd && fd.$wrapper && fd.$wrapper.length) {
				$layout.append(fd.$wrapper);
			}
		});
	}

	function build_shell(frm) {
		const $body = $(frm.layout.wrapper).closest(".form-layout").parent();
		if (!$body.length) return null;

		if (frm.__adr_shell && frm.__adr_shell.length && frm.__adr_shell.closest("body").length) {
			restore_fields(frm);
			frm.__adr_shell.remove();
			frm.__adr_shell = null;
		} else {
			$body.find(".adr-form-page").each(function () {
				$(this).remove();
			});
		}

		const is_new = frm.is_new();
		const title = is_new ? "新建考勤扣款规则" : "编辑考勤扣款规则";
		const chip = is_new ? "新文档" : `ID: ${frappe.utils.escape_html(frm.doc.name || "")}`;

		const $shell = $(`
			<div class="adr-form-page">
				<div class="adr-head">
					<div class="adr-head-top">
						<div class="adr-head-title">
							<button type="button" class="adr-back" data-act="back" title="返回列表">←</button>
							<h1>${title}</h1>
							<span class="adr-chip">${chip}</span>
						</div>
						<div class="adr-head-actions">
							<button type="button" class="adr-btn ghost" data-act="cancel">取消</button>
							<button type="button" class="adr-btn danger" data-act="delete">删除</button>
							<button type="button" class="adr-btn" data-act="draft">保存草稿</button>
							<button type="button" class="adr-btn primary" data-act="save-enable">保存并启用</button>
						</div>
					</div>
					<div class="adr-head-sub">定义不同考勤异常类型的扣款标准，系统将根据规则自动计算员工扣款金额。</div>
				</div>
				<div class="adr-grid">
					<div class="adr-left">
						<div class="adr-card" data-card="basic">
							<div class="adr-card-title">基本信息</div>
							<div class="adr-frow">
								<label>规则名称 <span class="req">*</span></label>
								<div class="adr-ctl adr-field-host" data-field="rule_name"></div>
							</div>
							<div class="adr-frow">
								<label>状态</label>
								<div class="adr-ctl adr-status-row">
									<div class="adr-field-host" data-field="is_active"></div>
									<span class="adr-status-text" data-role="status-text">停用</span>
								</div>
							</div>
							<div class="adr-frow is-top">
								<label>规则描述</label>
								<div class="adr-ctl adr-field-host" data-field="description"></div>
							</div>
							<div class="adr-frow" style="opacity:.72">
								<label>适用范围</label>
								<div class="adr-ctl" style="font-size:13px;color:#8c8c8c">
									由「考勤分组」关联本规则后生效（表单无此字段）
								</div>
							</div>
						</div>

						<div class="adr-card" data-card="items">
							<div class="adr-card-title">
								<span>扣款规则明细 (Items)</span>
								<button type="button" class="adr-act" data-act="add-item">＋ 添加规则</button>
							</div>
							<div class="adr-grid-host adr-field-host" data-field="rule_items"></div>
						</div>

						<div class="adr-card" data-card="tiers">
							<div class="adr-card-title">阶梯规则配置 (Tiers)</div>
							<div class="adr-tiers" data-role="tier-boxes"></div>
						</div>
					</div>
					<div class="adr-side">
						<div class="adr-side-card">
							<h4>规则预览（按默认参数估算）</h4>
							<div data-role="preview"></div>
							<div class="adr-disclaimer">* 预估结果仅供参考，实际扣款以考勤数据与规则计算结果为准</div>
						</div>
						<div class="adr-side-card">
							<h4>规则说明</h4>
							<p data-role="desc-side">当单次异常满足对应条件时，按阶梯或固定金额扣款。</p>
						</div>
						<div class="adr-side-card">
							<h4>计算单位</h4>
							<div class="adr-unit-row">按时长（分钟）</div>
							<div class="adr-unit-row">按次数（次）</div>
							<div class="adr-unit-row">按天数 / 小时</div>
						</div>
						<div class="adr-side-card">
							<h4>帮助文档</h4>
							<a class="adr-help-link" data-act="goto-rules">返回考勤规则列表</a>
							<a class="adr-help-link" data-act="goto-groups">查看考勤分组</a>
						</div>
					</div>
				</div>
			</div>
		`);

		$body.prepend($shell);
		return $shell;
	}

	function park_native(frm) {
		const $layout = $(frm.layout.wrapper).closest(".form-layout");
		$layout.addClass("adr-native-parked");
	}

	function move_fields(frm, $shell) {
		["rule_name", "is_active", "description", "rule_items"].forEach((fn) => {
			const fd = frm.fields_dict[fn];
			if (!fd || !fd.$wrapper) return;
			const $host = $shell.find(`.adr-field-host[data-field="${fn}"]`);
			if (!$host.length) return;
			fd.$wrapper.find(".clearfix, .help-box").hide();
			if (["rule_name", "is_active", "description"].includes(fn)) {
				fd.$wrapper.find(".control-label, label.control-label").hide();
			}
			if (fn === "is_active") {
				fd.$wrapper.find(".label-area, .checkbox .label-area").hide();
			}
			if (fn === "rule_items") {
				fd.$wrapper.children(".control-label, .form-group > .control-label").hide();
				fd.$wrapper.find("> .form-group > .control-label").hide();
			}
			$host.empty().append(fd.$wrapper);
		});
	}

	function bind_actions(frm, $shell) {
		$shell.off("click.adr").on("click.adr", "[data-act]", function (e) {
			e.preventDefault();
			const act = $(this).attr("data-act");
			if (act === "back" || act === "cancel" || act === "goto-rules") {
				go_rules_list();
				return;
			}
			if (act === "goto-groups") {
				frappe.set_route("List", "Attendance Group");
				return;
			}
			if (act === "delete") {
				if (frm.is_new()) {
					frappe.msgprint("尚未保存，无需删除");
					return;
				}
				frappe.confirm(`确定删除规则「${frm.doc.name}」？`, () => {
					frappe.call({
						method: "frappe.client.delete",
						args: { doctype: frm.doctype, name: frm.doc.name },
						callback: () => {
							frappe.show_alert({ message: "已删除", indicator: "red" });
							go_rules_list();
						},
					});
				});
				return;
			}
			if (act === "draft") {
				frm.set_value("is_active", 0).then(() => frm.save());
				return;
			}
			if (act === "save-enable") {
				frm.set_value("is_active", 1).then(() => frm.save());
				return;
			}
			if (act === "add-item") {
				const row = frm.add_child("rule_items");
				row.item_type = "Late Entry";
				row.enabled = 1;
				row.calc_mode = "Tiered";
				frm.refresh_field("rule_items");
				frm.dirty();
				refresh_preview(frm, $shell);
				return;
			}
			if (act === "add-tier") {
				const item_type = $(this).attr("data-type");
				const box = TIER_BOXES.find((b) => b.key === item_type) || TIER_BOXES[0];
				const row = frm.add_child("rule_tiers");
				row.item_type = item_type;
				row.min_value = 0;
				row.max_value = 0;
				row.tier_unit = box.default_unit;
				row.deduction_type = "Fixed Amount";
				row.amount = 0;
				frm.refresh_field("rule_tiers");
				frm.dirty();
				render_tier_boxes(frm, $shell);
				refresh_preview(frm, $shell);
			}
		});
	}

	function render_tier_boxes(frm, $shell) {
		const $wrap = $shell.find("[data-role=tier-boxes]");
		$wrap.empty();
		TIER_BOXES.forEach((box) => {
			const rows = (frm.doc.rule_tiers || [])
				.filter((r) => r.item_type === box.key)
				.sort((a, b) => (a.min_value || 0) - (b.min_value || 0));

			const $box = $(`
				<div class="adr-tier-box" data-type="${box.key}">
					<div class="tb-title">
						<span>${frappe.utils.escape_html(box.title)}</span>
						<button type="button" class="adr-act" data-act="add-tier" data-type="${box.key}">＋ 添加阶梯</button>
					</div>
					<table>
						<thead>
							<tr>
								<th>阶段</th>
								<th>范围</th>
								<th>金额(元)</th>
								<th></th>
							</tr>
						</thead>
						<tbody></tbody>
					</table>
				</div>
			`);
			const $tb = $box.find("tbody");
			if (!rows.length) {
				$tb.append(
					`<tr><td colspan="4"><div class="adr-tier-empty">暂无阶梯，点击上方添加</div></td></tr>`
				);
			} else {
				rows.forEach((r, idx) => {
					const name = r.name;
					$tb.append(`
						<tr data-row="${frappe.utils.escape_html(name || "")}" data-idx="${r.idx}">
							<td>${idx + 1}</td>
							<td>${frappe.utils.escape_html(range_text(r))} <span style="color:#8c8c8c;font-size:11px">${frappe.utils.escape_html(UNIT_LABEL[r.tier_unit] || r.tier_unit || "")}</span></td>
							<td><input type="number" step="0.01" min="0" value="${fmt_num(r.amount)}" data-edit="amount" /></td>
							<td><button type="button" class="adr-act" data-act="del-tier" data-name="${frappe.utils.escape_html(name || "")}" data-idx="${r.idx}" style="color:#e5484d">删除</button></td>
						</tr>
					`);
				});
			}
			$wrap.append($box);
		});

		$wrap
			.off("change.adr input.adr")
			.on("change.adr input.adr", "input[data-edit=amount]", function () {
				const $tr = $(this).closest("tr");
				const idx = cint($tr.attr("data-idx"));
				const row = (frm.doc.rule_tiers || []).find((r) => cint(r.idx) === idx);
				if (!row) return;
				row.amount = flt($(this).val());
				frm.dirty();
				refresh_preview(frm, $shell);
			});

		$wrap.off("click.adr-del").on("click.adr-del", "[data-act=del-tier]", function (e) {
			e.preventDefault();
			e.stopPropagation();
			const idx = cint($(this).attr("data-idx"));
			const row = (frm.doc.rule_tiers || []).find((r) => cint(r.idx) === idx);
			if (!row) return;
			const grid = frm.get_field("rule_tiers").grid;
			const gr =
				(row.name && grid.grid_rows_by_docname && grid.grid_rows_by_docname[row.name]) ||
				(grid.grid_rows || []).find((r) => r.doc && cint(r.doc.idx) === idx);
			if (gr && gr.remove) {
				gr.remove();
			} else {
				frm.doc.rule_tiers = (frm.doc.rule_tiers || []).filter((r) => cint(r.idx) !== idx);
				frm.refresh_field("rule_tiers");
			}
			frm.dirty();
			render_tier_boxes(frm, $shell);
			refresh_preview(frm, $shell);
		});
	}

	function refresh_status(frm, $shell) {
		const on = cint(frm.doc.is_active);
		const $t = $shell.find("[data-role=status-text]");
		$t.text(on ? "启用" : "停用").toggleClass("is-on", !!on);
	}

	function refresh_preview(frm, $shell) {
		const samples = [
			{ type: "Late Entry", label: "迟到 15 分钟", sample: 15, color: "green" },
			{ type: "Early Exit", label: "早退 45 分钟", sample: 45, color: "orange" },
			{ type: "Early Exit", label: "早退 30 分钟", sample: 30, color: "orange" },
			{ type: "Missing Punch", label: "缺卡 1 次", sample: 1, color: "red" },
			{ type: "Absent", label: "旷工 1 单位", sample: 1, color: "red" },
		];
		const $pv = $shell.find("[data-role=preview]").empty();
		samples.forEach((s) => {
			const hit = item_preview_amount(frm, s.type, s.sample);
			let amt = "—";
			let mode = "未配置";
			if (hit) {
				mode = hit.mode || MODE_LABEL[(frm.doc.rule_items || []).find((i) => i.item_type === s.type)?.calc_mode] || "";
				amt = hit.amount == null ? mode : `扣款 ${fmt_num(hit.amount)} 元`;
			}
			$pv.append(`
				<div class="adr-preview-item">
					<span class="adr-dot ${s.color}"></span>
					<span class="adr-pv-left">${frappe.utils.escape_html(s.label)}</span>
					<span class="adr-pv-amt">${frappe.utils.escape_html(amt)}</span>
				</div>
			`);
		});

		const desc = (frm.doc.description || "").trim();
		$shell
			.find("[data-role=desc-side]")
			.text(desc || "当单次异常满足对应条件时，按阶梯或固定金额扣款。");
	}

	function localize_labels(frm) {
		frm.set_df_property("rule_name", "label", "规则名称");
		frm.set_df_property("is_active", "label", "启用");
		frm.set_df_property("description", "label", "规则描述");
		frm.set_df_property("rule_items", "label", "扣款规则明细");
		frm.set_df_property("rule_tiers", "label", "阶梯规则");
	}

	function remount_content(frm) {
		const $shell = frm.__adr_shell;
		if (!$shell || !$shell.length) return;
		$shell.find(".adr-chip").text(
			frm.is_new() ? "新文档" : `ID: ${frappe.utils.escape_html(frm.doc.name || "")}`
		);
		$shell.find(".adr-head-title h1").text(frm.is_new() ? "新建考勤扣款规则" : "编辑考勤扣款规则");
		render_tier_boxes(frm, $shell);
		refresh_status(frm, $shell);
		refresh_preview(frm, $shell);
	}

	function mount(frm) {
		ensure_css();
		localize_labels(frm);
		hide_frappe_chrome(frm);

		if (frm.__adr_shell && frm.__adr_shell.length && document.body.contains(frm.__adr_shell[0])) {
			remount_content(frm);
			return;
		}

		park_native(frm);
		const $shell = build_shell(frm);
		if (!$shell) return;
		frm.__adr_shell = $shell;
		move_fields(frm, $shell);
		bind_actions(frm, $shell);
		render_tier_boxes(frm, $shell);
		refresh_status(frm, $shell);
		refresh_preview(frm, $shell);

		document.body.classList.add("adr-form-active");
		try {
			frm.page.clear_primary_action();
			frm.page.clear_secondary_action();
			frm.page.set_secondary_action(__("返回"), go_rules_list);
		} catch (e) {
			/* ignore */
		}
	}

	frappe.ui.form.on("Attendance Deduction Rule", {
		onload(frm) {
			ensure_css();
		},
		refresh(frm) {
			mount(frm);
		},
		after_save(frm) {
			if (frm.__adr_shell) remount_content(frm);
		},
		is_active(frm) {
			if (frm.__adr_shell) refresh_status(frm, frm.__adr_shell);
		},
		description(frm) {
			if (frm.__adr_shell) refresh_preview(frm, frm.__adr_shell);
		},
		rule_name(frm) {
			if (!frm.__adr_shell) return;
			frm.__adr_shell.find(".adr-chip").text(
				frm.is_new() ? "新文档" : `ID: ${frm.doc.name || frm.doc.rule_name || ""}`
			);
		},
		rule_items_on_form_rendered(frm) {
			if (frm.__adr_shell) refresh_preview(frm, frm.__adr_shell);
		},
	});

	frappe.ui.form.on("Attendance Deduction Rule Item", {
		item_type(frm) {
			if (frm.__adr_shell) refresh_preview(frm, frm.__adr_shell);
		},
		enabled(frm) {
			if (frm.__adr_shell) refresh_preview(frm, frm.__adr_shell);
		},
		calc_mode(frm) {
			if (frm.__adr_shell) refresh_preview(frm, frm.__adr_shell);
		},
		rate_per_minute(frm) {
			if (frm.__adr_shell) refresh_preview(frm, frm.__adr_shell);
		},
		salary_percent(frm) {
			if (frm.__adr_shell) refresh_preview(frm, frm.__adr_shell);
		},
	});

	frappe.ui.form.on("Attendance Deduction Rule Tier", {
		item_type(frm) {
			if (frm.__adr_shell) {
				render_tier_boxes(frm, frm.__adr_shell);
				refresh_preview(frm, frm.__adr_shell);
			}
		},
		min_value(frm) {
			if (frm.__adr_shell) {
				render_tier_boxes(frm, frm.__adr_shell);
				refresh_preview(frm, frm.__adr_shell);
			}
		},
		max_value(frm) {
			if (frm.__adr_shell) {
				render_tier_boxes(frm, frm.__adr_shell);
				refresh_preview(frm, frm.__adr_shell);
			}
		},
		amount(frm) {
			if (frm.__adr_shell) {
				render_tier_boxes(frm, frm.__adr_shell);
				refresh_preview(frm, frm.__adr_shell);
			}
		},
	});

	if (!window.__adr_form_route_hook) {
		window.__adr_form_route_hook = true;
		frappe.router.on("change", () => {
			const route = frappe.get_route() || [];
			if (route[0] !== "Form" || route[1] !== "Attendance Deduction Rule") {
				document.body.classList.remove("adr-form-active");
			}
		});
	}
})();
