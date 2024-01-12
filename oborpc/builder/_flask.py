"""
"""
import functools
import json
import os
from flask import request as flask_request, Blueprint
from ._server import ServerBuilder
from ..base.meta import OBORBase

class FlaskServerBuilder(ServerBuilder):
    def __init__(self, host, port=None, timeout=1, retry=None):
        super().__init__(host, port, timeout, retry)

    def create_remote_responder(
        self, instance: OBORBase, router: Blueprint, class_name, method_name, method
    ):
        def create_modified_func():
            @functools.wraps(method)
            def modified_func():
                body = json.loads(flask_request.get_json())
                return self.dispatch_rpc_request(
                    instance, method, body
                )
            return modified_func
        router.post(
            f"{router.url_prefix or ''}/{class_name}/{method_name}"
        )(create_modified_func())

    def build_blueprint_from_instance(
        self,
        instance: OBORBase,
        blueprint_name: str,
        import_name: str,
        static_folder: str | os.PathLike | None = None,
        static_url_path: str | None = None,
        template_folder: str | os.PathLike | None = None,
        url_prefix: str | None = None,
        subdomain: str | None = None,
        url_defaults: dict | None = None,
        root_path: str | None = None,
        cli_group: str | None = object()
    ):
        """
        """
        blueprint = Blueprint(
            blueprint_name,
            import_name,
            static_folder,
            static_url_path,
            template_folder,
            url_prefix,
            subdomain,
            url_defaults,
            root_path,
            cli_group
        )

        self.setup_server_rpc(instance, blueprint)

        return blueprint
