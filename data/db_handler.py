import json
import os
from typing import Tuple
from venv import logger

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
        response = requests.get(
            url=url,
            auth=DBHandler._get_db_auth(),
            params={
                "startkey": f'["{channel_id}", 0]',
                "endkey": f'["{channel_id}", {{}}]',  # {} is "higher" than any number
                "include_docs": "true",
            },
        )

        if response.status_code != 200:
            raise Exception(
                f"Failed to get channel messages: {response.status_code} - {response.text}"
            )

        rows = response.json().get("rows", [])
        return [ChannelMessage.model_validate(row["doc"]) for row in rows]

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
        DBHandler._setup_channel_messages_view()

    @staticmethod
    def _setup_channel_messages_view() -> None:
        with open("couchdb/views/channel_message_view.json", "r") as f:
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
                f"Failed to create channel config: {response.status_code} - {response.text}"
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
                f"Failed to create channel config: {response.status_code} - {response.text}"
            )
