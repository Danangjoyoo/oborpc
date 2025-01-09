"""
FastAPI Server Builder
"""
import json
import asyncio
from enum import Enum
from typing import Optional, List, Dict, Union, Type, Any, Sequence, Callable

import jsonref
from pydantic import BaseModel
from fastapi import Request, Response, APIRouter, params
from fastapi.responses import JSONResponse
from fastapi.routing import BaseRoute, APIRoute, ASGIApp, Lifespan, Default, generate_unique_id

from ._server import ServerBuilder
from ..base.meta import RPCBase



class FastAPIServerBuilder(ServerBuilder):
    """
    Dedicated RPC Server Builder for FastAPI
    """
    def generate_model_schema(self, model: Optional[BaseModel]) -> Dict[str, Any]:
        """
        Generate pydantic model schema
        """
        try:
            if not model:
                return {}
            schema = json.dumps(model.model_json_schema())
            openapi_schema = json.loads(json.dumps(jsonref.loads(schema), indent=2))
            if "$defs" in openapi_schema:
                openapi_schema.pop("$defs")
            return openapi_schema
        except: # pylint: disable=bare-except
            return {}

    def generate_openapi_extra_body(self, class_name: str, method_name: str) -> Dict[str, Any]:
        """
        Generate OpenAPI Extra Body for Schema
        """
        # request schema
        model = self.model_maps[class_name][method_name][2]
        request_schema = self.generate_model_schema(model)

        # response schema
        model = self.model_maps[class_name][method_name][3]
        response_schema = self.generate_model_schema(model)

        extra = {
            "summary": f"{class_name}.{method_name}",
            "requestBody": {
                "content": {
                    "application/json": {
                        "schema": request_schema
                    }
                },
                "required": True,
            },
            "responses": {
                "200": {
                    "description": "Successful Response",
                    "content": {
                        "application/json": {
                            "schema": response_schema
                        }
                    }
                }
            }
        }
        return extra

    def create_remote_responder(
        self,
        instance: RPCBase,
        router: APIRouter,
        class_name: str,
        method_name: str,
        method: Callable
    ): # pylint: disable=too-many-positional-arguments
        @router.post(
            f"{router.prefix}/{class_name}/{method_name}",
            tags=[class_name],
            openapi_extra=self.generate_openapi_extra_body(class_name, method_name)
        )
        def rpc_function(request: Request):
            request_body = asyncio.run(request.body())
            if request_body:
                decoded_request_body = json.loads(request_body.decode())
                if isinstance(decoded_request_body, str):
                    body = json.loads(decoded_request_body)
                else:
                    body = decoded_request_body
            else:
                body = {}
            return self.dispatch_rpc_request(class_name, method_name, instance, method, body)

    def create_remote_responder_async(
        self,
        instance: RPCBase,
        router: APIRouter,
        class_name: str,
        method_name: str,
        method: Callable
    ): # pylint: disable=too-many-positional-arguments,too-many-arguments,too-many-arguments
        @router.post(
            f"{router.prefix}/{class_name}/{method_name}",
            tags=[class_name],
            openapi_extra=self.generate_openapi_extra_body(class_name, method_name)
        )
        async def rpc_function(request: Request):
            request_body = await request.body()
            if request_body:
                decoded_request_body = json.loads(request_body.decode())
                if isinstance(decoded_request_body, str):
                    body = json.loads(decoded_request_body)
                else:
                    body = decoded_request_body
            else:
                body = {}
            return await self.dispatch_rpc_request_async(class_name, method_name, instance, method, body)

    def build_router_from_instance(
        self,
        instance: RPCBase,
        *,
        prefix: str = "",
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
        secure_build: bool = True,
    ): # pylint: disable=too-many-positional-arguments,too-many-arguments,too-many-locals
        """
        build FastAPI API Router from oborpc instance
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

        self.setup_server_rpc(instance, router, secure_build)

        return router
