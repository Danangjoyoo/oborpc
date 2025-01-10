"""
Flask Server Builder
"""
import functools
import json
import os
from typing import Callable, Union
from flask import request as flask_request, Blueprint
from ._server import ServerBuilder
from ..base.meta import RPCBase

class FlaskServerBuilder(ServerBuilder):
    """
    Dedicated RPC Server Builder for Flask
    """
    def create_remote_responder(
        self,
        instance: RPCBase,
        router: Blueprint,
        class_name: str,
        method_name: str,
        method: Callable
    ): # pylint: disable=too-many-arguments,too-many-positional-arguments
        def create_modified_func():
            @functools.wraps(method)
            def modified_func():
                request_body = flask_request.get_json()
                body = json.loads(flask_request.get_json()) if request_body else {}
                return self.dispatch_rpc_request(class_name, method_name, instance, method, body)
            return modified_func
        router.post(f"{router.url_prefix or ''}/{class_name}/{method_name}")(create_modified_func())

    def build_blueprint_from_instance(
        self,
        instance: RPCBase,
        blueprint_name: str,
        import_name: str,
        static_folder: Union[str, os.PathLike, None] = None,
        static_url_path: Union[str, None] = None,
        template_folder: Union[str, os.PathLike, None] = None,
        url_prefix: Union[str, None] = None,
        subdomain: Union[str, None] = None,
        url_defaults: Union[dict, None] = None,
        root_path: Union[str, None] = None,
        cli_group: Union[str, None] = object(),
        secure_build: bool = True,
    ): # pylint: disable=too-many-arguments,too-many-positional-arguments
        """
        build Flask blueprint from oborpc instance
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

        self.setup_server_rpc(instance, blueprint, secure_build)

        return blueprint
