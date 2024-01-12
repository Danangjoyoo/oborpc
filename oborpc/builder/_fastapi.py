"""
"""
import json
import asyncio
from enum import Enum
from fastapi import Request, Response, APIRouter, params
from fastapi.responses import JSONResponse
from fastapi.routing import BaseRoute, APIRoute, ASGIApp, Lifespan, Default, generate_unique_id
from typing import Optional, List, Dict, Union, Type, Any, Sequence, Callable
from ._server import ServerBuilder
from ..base.meta import OBORBase

class FastAPIServerBuilder(ServerBuilder):
    def __init__(self, host, port=None, timeout=1, retry=None):
        super().__init__(host, port, timeout, retry)

    def create_remote_responder(
        self,
        instance: OBORBase,
        router: APIRouter,
        class_name: str,
        method_name: str,
        method: Callable
    ):
        @router.post(f"{router.prefix}/{class_name}/{method_name}")
        def final_func(request: Request):
            request_body = asyncio.run(request.body())
            body = json.loads(json.loads(request_body.decode()))
            return self.dispatch_rpc_request(instance, method, body)

    def build_router_from_instance(
        self,
        instance: OBORBase,
        *,
        prefix: str,
        tags: Optional[List[Union[str, Enum]]] = None,
        dependencies: Optional[Sequence[params.Depends]] = None,
        default_response_class: Type[Response] = Default(JSONResponse),
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        callbacks: Optional[List[BaseRoute]] = None,
        routes: Optional[List[BaseRoute]] = None,
        redirect_slashes: bool = True,
        default: Optional[ASGIApp] = None,
        dependency_overrides_provider: Optional[Any] = None,
        route_class: Type[APIRoute] = APIRoute,
        on_startup: Optional[Sequence[Callable[[], Any]]] = None,
        on_shutdown: Optional[Sequence[Callable[[], Any]]] = None,
        lifespan: Optional[Lifespan[Any]] = None,
        deprecated: Optional[bool] = None,
        include_in_schema: bool = True,
        generate_unique_id_function: Callable[[APIRoute], str] = Default(generate_unique_id),
    ):
        """
        """
        router = APIRouter(
            prefix=prefix,
            tags=tags,
            dependencies=dependencies,
            default_response_class=default_response_class,
            responses=responses,
            callbacks=callbacks,
            routes=routes,
            redirect_slashes=redirect_slashes,
            default=default,
            dependency_overrides_provider=dependency_overrides_provider,
            route_class=route_class,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            lifespan=lifespan,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            generate_unique_id_function=generate_unique_id_function
        )

        self.setup_server_rpc(instance, router)

        return router