# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
import warnings
from abc import ABC
from contextlib import suppress
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from airflow.models.connection import Connection


class BaseSecretsBackend(ABC):
    """Abstract base class to retrieve Connection object given a conn_id or Variable given a key"""

    @staticmethod
    def build_path(path_prefix: str, secret_id: str, sep: str = "/") -> str:
        """
        Given conn_id, build path for Secrets Backend

        :param path_prefix: Prefix of the path to get secret
        :param secret_id: Secret id
        :param sep: separator used to concatenate connections_prefix and conn_id. Default: "/"
        """
        return f"{path_prefix}{sep}{secret_id}"

    def get_conn_value(self, conn_id: str) -> Optional[str]:
        """
        Retrieve from Secrets Backend a string value representing the Connection object.

        If the client your secrets backend uses already returns a python dict, you should override
        ``get_connection`` instead.

        :param conn_id: connection id
        """
        raise NotImplementedError

    def deserialize_connection(self, conn_id: str, value: str) -> 'Connection':
        """
        Given a serialized representation of the airflow Connection, return an instance.
        Looks at first character to determine how to deserialize.

        :param conn_id: connection id
        :param value: the serialized representation of the Connection object
        :return: the deserialized Connection
        """
        from airflow.models.connection import Connection

        value = value.strip()
        if value[0] == '{':
            return Connection.from_json(conn_id=conn_id, value=value)
        else:
            return Connection(conn_id=conn_id, uri=value)

    def get_conn_uri(self, conn_id: str) -> Optional[str]:
        """
        Get conn_uri from Secrets Backend

        This method is deprecated and will be removed in a future release; implement ``get_conn_value``
        instead.

        :param conn_id: connection id
        """
        raise NotImplementedError()

    def get_connection(self, conn_id: str) -> Optional['Connection']:
        """
        Return connection object with a given ``conn_id``.

        Tries ``get_conn_value`` first and if not implemented, tries ``get_conn_uri``

        :param conn_id: connection id
        """
        value = None

        # TODO: after removal of ``get_conn_uri`` we should not catch NotImplementedError here
        with suppress(NotImplementedError):
            value = self.get_conn_value(conn_id=conn_id)

        if not value:
            with suppress(NotImplementedError):
                value = self.get_conn_uri(conn_id=conn_id)
                warnings.warn(
                    "Method `get_conn_uri` is deprecated. Please use `get_conn_value`.",
                    PendingDeprecationWarning,
                    stacklevel=2,
                )

        if value:
            return self.deserialize_connection(conn_id=conn_id, value=value)
        else:
            return None

    def get_connections(self, conn_id: str) -> List['Connection']:
        """
        Return connection object with a given ``conn_id``.

        :param conn_id: connection id
        """
        warnings.warn(
            "This method is deprecated. Please use "
            "`airflow.secrets.base_secrets.BaseSecretsBackend.get_connection`.",
            PendingDeprecationWarning,
            stacklevel=2,
        )
        conn = self.get_connection(conn_id=conn_id)
        if conn:
            return [conn]
        return []

    def get_variable(self, key: str) -> Optional[str]:
        """
        Return value for Airflow Variable

        :param key: Variable Key
        :return: Variable Value
        """
        raise NotImplementedError()

    def get_config(self, key: str) -> Optional[str]:
        """
        Return value for Airflow Config Key

        :param key: Config Key
        :return: Config Value
        """
        return None
