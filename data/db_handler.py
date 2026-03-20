import json
import os
from typing import Tuple

import requests

from model.base_db_model import BaseDBModel
from model.channel_config import ChannelConfig
from model.channel_message import ChannelMessage
from model.workspace_config import WorkspaceConfig


class DBHandler:
    # Public
    @staticmethod
    def setup_db():
        DBHandler._setup_db()
        DBHandler._setup_views()

    @staticmethod
    def write_model(model: BaseDBModel) -> None:
        if isinstance(model, ChannelConfig):
            return DBHandler._write_channel_config(model)
        if isinstance(model, WorkspaceConfig):
            return DBHandler._write_workspace_config(model)
        if isinstance(model, ChannelMessage):
            return DBHandler._write_channel_message(model)

        return DBHandler._write_generic_model(model)

    @staticmethod
    def get_workspace_config(team_id: str) -> WorkspaceConfig | None:
        url = f"{DBHandler._get_db_url()}/{os.getenv('DB_NAME')}/{team_id}"
        response = requests.get(
            url=url,
            auth=DBHandler._get_db_auth(),
        )

        if response.status_code == 404:
            return None
        if response.status_code != 200:
            raise Exception(
                f"Failed to get channel config: {response.status_code} - {response.text}"
            )

        return WorkspaceConfig.model_validate(response.json())

    @staticmethod
    def get_channel_config(channel_id: str) -> ChannelConfig | None:
        url = f"{DBHandler._get_db_url()}/{os.getenv('DB_NAME')}/{channel_id}"
        response = requests.get(
            url=url,
            auth=DBHandler._get_db_auth(),
        )

        if response.status_code == 404:
            return None
        if response.status_code != 200:
            raise Exception(
                f"Failed to get channel config: {response.status_code} - {response.text}"
            )

        return ChannelConfig.model_validate(response.json())

    @staticmethod
    def get_channel_messages(channel_id: str) -> list[ChannelMessage]:
        url = f"{DBHandler._get_db_url()}/{os.getenv('DB_NAME')}/_design/channel_messages/_view/by_channel"
        response = requests.post(
            url=url,
            auth=DBHandler._get_db_auth(),
            json={
                "startkey": [channel_id, ""],
                "endkey": [channel_id, {}],  # {} is "higher" than any string / number
                "include_docs": True,
            },
        )

        if response.status_code != 200:
            raise Exception(
                f"Failed to get channel messages: {response.status_code} - {response.text}"
            )

        rows = response.json().get("rows", [])
        return [ChannelMessage.model_validate(row["doc"]) for row in rows]

    @staticmethod
    def delete_channel_message(message_id: str) -> None:
        base_url = f"{DBHandler._get_db_url()}/{os.getenv('DB_NAME')}"

        # First get the document to retrieve its _rev
        get_response = requests.get(
            url=f"{base_url}/{message_id}",
            auth=DBHandler._get_db_auth(),
        )

        if get_response.status_code == 404:
            return  # Already deleted
        if get_response.status_code != 200:
            raise Exception(f"Failed to get message: {get_response.status_code}")

        rev = get_response.json()["_rev"]

        # Delete with the _rev
        delete_response = requests.delete(
            url=f"{base_url}/{message_id}",
            auth=DBHandler._get_db_auth(),
            params={"rev": rev},
        )

        if delete_response.status_code not in (200, 202):
            raise Exception(f"Failed to delete message: {delete_response.status_code}")

    @staticmethod
    def delete_messages_by_trigger(triggering_message_id: str) -> None:
        """Delete all messages associated with a triggering Slack message."""
        base_url = f"{DBHandler._get_db_url()}/{os.getenv('DB_NAME')}"

        # Query the view to get all related docs
        view_url = f"{base_url}/_design/channel_messages_by_trigger/_view/by_trigger"
        response = requests.post(
            url=view_url,
            auth=DBHandler._get_db_auth(),
            json={
                "key": triggering_message_id,
                "include_docs": True,
            },
        )

        if response.status_code != 200:
            raise Exception(f"Failed to query view: {response.status_code}")

        rows = response.json().get("rows", [])
        if len(rows) == 0:
            return

        # Build bulk delete payload
        docs_to_delete = [
            {"_id": row["doc"]["_id"], "_rev": row["doc"]["_rev"], "_deleted": True}
            for row in rows
        ]

        # Bulk delete
        bulk_response = requests.post(
            url=f"{base_url}/_bulk_docs",
            auth=DBHandler._get_db_auth(),
            json={"docs": docs_to_delete},
        )

        if bulk_response.status_code not in (200, 201):
            raise Exception(f"Failed to bulk delete: {bulk_response.status_code}")

    @staticmethod
    def update_channel_message(message_id: str, new_body: str) -> None:
        base_url = f"{DBHandler._get_db_url()}/{os.getenv('DB_NAME')}"

        # First get the document to retrieve its _rev
        get_response = requests.get(
            url=f"{base_url}/{message_id}",
            auth=DBHandler._get_db_auth(),
        )

        if get_response.status_code == 404:
            return  # Doesn't exist
        if get_response.status_code != 200:
            raise Exception(f"Failed to get message: {get_response.status_code}")

        doc = get_response.json()
        doc["body"] = new_body

        # PUT the updated doc with the _rev
        update_response = requests.put(
            url=f"{base_url}/{message_id}",
            auth=DBHandler._get_db_auth(),
            json=doc,  # Include the full doc with _rev
        )

        if update_response.status_code not in (200, 201, 202):
            raise Exception(f"Failed to update message: {update_response.status_code}")

    @staticmethod
    def archive_channel_messages(channel_id: str) -> None:
        base_url = f"{DBHandler._get_db_url()}/{os.getenv('DB_NAME')}"
        get_url = f"{base_url}/_design/channel_messages/_view/by_channel"
        get_response = requests.post(
            url=get_url,
            auth=DBHandler._get_db_auth(),
            json={
                "startkey": [channel_id, ""],
                "endkey": [channel_id, {}],  # {} is "higher" than any string / number
                "include_docs": True,
            },
        )

        if get_response.status_code != 200:
            raise Exception(
                f"Failed to get channel messages: {get_response.status_code} - {get_response.text}"
            )

        rows = get_response.json().get("rows", [])
        if len(rows) == 0:
            return

        # Build bulk update payload
        docs_to_update = [
            {
                **row["doc"],
                "archived": True,
            }
            for row in rows
        ]

        # Bulk delete
        bulk_response = requests.post(
            url=f"{base_url}/_bulk_docs",
            auth=DBHandler._get_db_auth(),
            json={"docs": docs_to_update},
        )

        if bulk_response.status_code not in (200, 201, 202):
            raise Exception(f"Failed to update message: {bulk_response.status_code}")

    # Private
    @staticmethod
    def _get_db_url() -> str:
        return f"http://{os.getenv('DB_URL')}"

    @staticmethod
    def _get_db_auth() -> Tuple[str, str]:
        return os.getenv("DB_USER", ""), os.getenv("DB_PASSWORD", "")

    @staticmethod
    def _setup_db() -> None:
        url = f"{DBHandler._get_db_url()}/{os.getenv('DB_NAME')}"
        exists_response = requests.head(
            url=url,
            auth=DBHandler._get_db_auth(),
        )
        if exists_response.status_code == 200:
            # db exists
            return
        elif exists_response.status_code != 404:
            raise Exception(
                f"Got error checking DB exists: {exists_response.status_code}"
            )
        else:
            create_response = requests.put(
                url=url,
                auth=DBHandler._get_db_auth(),
            )
            if create_response.status_code != 201:
                raise Exception(f"Got error creating DB: {create_response.status_code}")

    @staticmethod
    def _setup_views() -> None:
        DBHandler._setup_view("couchdb/views/channel_message_view.json")
        DBHandler._setup_view("couchdb/views/channel_messages_by_trigger.json")

    @staticmethod
    def _setup_view(path: str) -> None:
        with open(path, "r") as f:
            view_doc = json.load(f)

        doc_id = view_doc["_id"]
        url = f"{DBHandler._get_db_url()}/{os.getenv('DB_NAME')}/{doc_id}"

        # Check if view already exists
        existing = requests.get(
            url=url,
            auth=DBHandler._get_db_auth(),
        )

        if existing.status_code == 200:
            # exists
            return
        elif existing.status_code != 404:
            raise Exception(f"Error checking view exists: {existing.status_code}")

        response = requests.put(
            url=url,
            auth=DBHandler._get_db_auth(),
            json=view_doc,
        )

        if response.status_code not in (201, 202):
            raise Exception(
                f"Failed to create view: {response.status_code} - {response.text}"
            )

    @staticmethod
    def _write_channel_config(config: ChannelConfig) -> None:
        url = f"{DBHandler._get_db_url()}/{os.getenv('DB_NAME')}/{config.channel_id}"

        response = requests.put(
            url=url,
            auth=DBHandler._get_db_auth(),
            json=config.model_dump(mode="json"),
        )

        if response.status_code not in (201, 202):
            raise Exception(
                f"Failed to create channel config: {response.status_code} - {response.text}"
            )

    @staticmethod
    def _write_workspace_config(config: WorkspaceConfig) -> None:
        url = f"{DBHandler._get_db_url()}/{os.getenv('DB_NAME')}/{config.team_id}"

        response = requests.put(
            url=url,
            auth=DBHandler._get_db_auth(),
            json=config.model_dump(mode="json"),
        )

        if response.status_code not in (201, 202):
            raise Exception(
                f"Failed to create workspace config: {response.status_code} - {response.text}"
            )

    @staticmethod
    def _write_channel_message(message: ChannelMessage) -> None:
        url = f"{DBHandler._get_db_url()}/{os.getenv('DB_NAME')}/{message.message_id}"

        response = requests.put(
            url=url,
            auth=DBHandler._get_db_auth(),
            json=message.model_dump(mode="json"),
        )

        if response.status_code not in (201, 202):
            raise Exception(
                f"Failed to create channel message: {response.status_code} - {response.text}"
            )

    @staticmethod
    def _write_generic_model(model: BaseDBModel) -> None:
        url = f"{DBHandler._get_db_url()}/{os.getenv('DB_NAME')}"

        response = requests.post(
            url=url,
            auth=DBHandler._get_db_auth(),
            json=model.model_dump(mode="json"),
        )

        if response.status_code not in (201, 202):
            raise Exception(
                f"Failed to create model: {response.status_code} - {response.text}"
            )
