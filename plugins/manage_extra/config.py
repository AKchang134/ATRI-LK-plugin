from ATRI.configs import PluginConfig
from ATRI.utils.model import BaseModel

from typing import Any



class ManageExtra(BaseModel):
    special_perms: list[str] = []

    utils_config: dict[str, Any] = {
        "get_history_interval": 0
    }

    batch_recall_config: dict[str, Any] = {
        "message_limit": 256,
        "recall_interval": 0
    }

config: akCS_Extra = PluginConfig("Manage-Extra", ManageExtra).config()
