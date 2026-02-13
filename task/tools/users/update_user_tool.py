from typing import Any

from task.tools.users.base import BaseUserServiceTool
from task.tools.users.models.user_info import UserUpdate


class UpdateUserTool(BaseUserServiceTool):

    @property
    def name(self) -> str:
        return "update_user"

    @property
    def description(self) -> str:
        return "Updates an existing user"

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "id": {
                    "type": "number",
                    "description": "User ID that should be updated"
                },
                "new_info": UserUpdate.model_json_schema()
            },
            "required": ["id", "new_info"]
        }

    def execute(self, arguments: dict[str, Any]) -> str:
        try:
            user_id = int(arguments["id"])
            new_info = arguments["new_info"]
            model = UserUpdate.model_validate(new_info)
            return self._user_client.update_user(user_id, model)
        except Exception as e:
            return f"Error while creating a new user: {str(e)}"
