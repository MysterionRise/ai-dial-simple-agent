from typing import Any

from task.tools.users.base import BaseUserServiceTool


class SearchUsersTool(BaseUserServiceTool):

    @property
    def name(self) -> str:
        return "search_users"

    @property
    def description(self) -> str:
        return "Search users by name, surname, email, or gender"

    @property
    def input_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "User name to search by"
                },
                "surname": {
                    "type": "string",
                    "description": "User surname to search by"
                },
                "email": {
                    "type": "string",
                    "description": "User email to search by"
                },
                "gender": {
                    "type": "string",
                    "description": "User gender to search by"
                }
            }
        }

    def execute(self, arguments: dict[str, Any]) -> str:
        try:
            return self._user_client.search_users(**arguments)
        except Exception as e:
            return f"Error while searching users: {str(e)}"
