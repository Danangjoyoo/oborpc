# OBORPC
[![Downloads](https://static.pepy.tech/personalized-badge/oborpc?period=total&units=international_system&left_color=black&right_color=orange&left_text=Downloads)](https://pepy.tech/project/oborpc)

# Description
An easy to build RPC based on Object Oriented Programming. Build your RPC in seconds. Built-in setup for FastAPI and Flask.

# Installation
```bash
pip install oborpc
```

# Basic Examples
1. Create `calculator.py` as your base
```
from oborpc.base import meta
from oborpc.decorator import procedure

class Calculator(meta.RPCBase):
    @procedure
    def add(self, a: int, b: int):
        pass

    @procedure
    def subtract(self, a: int, b: int):
        pass

class CalculatorServer(Calculator):
    def add(self, a: int, b: int):
        print(f"adding {a} and {b}")
        return a+b

    def subtract(self, a: int, b: int):
        print(f"subtracting {a} and {b}")
        return a - b
```

2. Create your App, below we give 2 examples how to do it with Flask or FastAPI

    - using Flask
    ```
    from oborpc.builder import FlaskServerBuilder
    from calculator import CalculatorServer
    from flask import Flask

    calculator_server = CalculatorServer()

    server_builder = FlaskServerBuilder("http://localhost", 9000)
    calculator_blueprint = server_builder.build_blueprint_from_instance(
        calculator_server, "calculator", "calculator"
    )

    app = Flask(__name__)
    app.register_blueprint(calculator_blueprint)

    app.run(port=8000)
    ```

    - using FastAPI
    ```
    from oborpc.builder import FastAPIServerBuilder
    from calculator import CalculatorServer

    calculator_server = CalculatorServer()

    server_builder = FastAPIServerBuilder("http://localhost", 8000)
    calculator_router = server_builder.build_router_from_instance(
        calculator_server, prefix=""
    )


    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(calculator_router)
    ```

3. Create client, you can create a simple `client.py` or a client application
    - simple `client.py`
    ```
    from oborpc.builder import ClientBuilder
    from calculator import Calculator

    calculator = Calculator()

    client_builder = ClientBuilder("http://localhost", 8000)
    client_builder.build_client_rpc(calculator)

    print(calculator.add(1,2))
    ```

    - client application
    ```
    from calculator import Calculator
    from fastapi import FastAPI
    from oborpc.builder import ClientBuilder, FastAPIServerBuilder

    ## RPC setup
    calculator = Calculator()

    clientBuilder = ClientBuilder("http://localhost", 9000)
    clientBuilder.build_client_rpc(calculator)

    ## application
    app = FastAPI()

    @app.get("/calculator/add")
    def get_add_results(a: float, b: float):
        return calculator.add(a, b)
    ```

4. Your RPC is ready to go!
