"""企业微信通讯录、消息与考勤集成。"""

from .client import WeComAPIError, WeComClient, WeComConfig, WeComConfigurationError

__all__ = [
	"WeComAPIError",
	"WeComClient",
	"WeComConfig",
	"WeComConfigurationError",
]
