# Copyright (c) 2026 stillgroup
# License: MIT
"""考勤扣款指标业务定义（与计划一致）。"""

# 缺卡：排班日仅有上班或仅有下班打卡，或应出勤无有效打卡且未请假
MISSING_PUNCH_DEFINITION = (
	"scheduled_day_with_only_in_or_out_checkin_or_no_attendance_without_leave"
)

# 旷工：Attendance.status=Absent，工时不足阈值触发的 Absent 按标准工时计小时
ABSENT_STATUS = "Absent"

# 迟到/早退分钟：签到/签退时间相对班次起止减宽限期（与 shift_attendance 一致）

# 旷工默认不重复扣 payment_days（由 Attendance Deduction Settings 控制）
DEFAULT_ABSENT_AFFECTS_PAYMENT_DAYS = 0

ITEM_TYPES = ("Late Entry", "Early Exit", "Missing Punch", "Absent")
CALC_MODES = ("Tiered", "Per Minute", "None", "Salary Percent")
TIER_UNITS = ("Per Occurrence Minutes", "Monthly Count", "Occurrence Hours")
DEDUCTION_TYPES = ("Fixed Amount", "Per Unit Amount")

SALARY_COMPONENT_NAME = "Attendance Deduction"
