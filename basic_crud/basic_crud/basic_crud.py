"""Welcome to Reflex! This file outlines the steps to create a basic app."""
import asyncio
import json

import httpx
from sqlmodel import select

import reflex as rx

from .api import product_router
from .model import Product

DEFAULT_BODY = """{
    "code":"",
    "label":"",
    "image":"/favicon.ico",
    "quantity":0,
    "category":"",
    "seller":"",
    "sender":""
}"""

URL_OPTIONS = {
    "GET": "products",
    "POST": "products",
    "PUT": "products/{pr_id}",
    "DELETE": "products/{pr_id}",
}


class State(rx.State):
    """The app state."""

    products: list[Product]
    _db_updated: bool = False

    def load_product(self):
        with rx.session() as session:
            self.products = session.exec(select(Product)).all()
        yield State.reload_product

    @rx.background
    async def reload_product(self):
        while True:
            await asyncio.sleep(2)
            if self.db_updated:
                async with self:
                    with rx.session() as session:
                        self.products = session.exec(select(Product)).all()
                    self._db_updated = False

    @rx.var
    def db_updated(self):
        return self._db_updated

    @rx.var
    def total(self):
        return len(self.products)


class QueryState(State):
    body: str = DEFAULT_BODY
    response_code: str = ""
    response: str = ""
    method: str = "GET"
    url_query: str = URL_OPTIONS["GET"]
    query_options = list(URL_OPTIONS.keys())

    def update_method(self, value):
        if self.url_query == "":
            self.url_query = URL_OPTIONS[value]
        self.method = value

    @rx.var
    def need_body(self):
        return False

    @rx.var
    def f_response(self):
        return f"""```json\n{self.response}\n```"""

    def clear_query(self):
        self.url_query = URL_OPTIONS["GET"]
        self.method = "GET"
        self.body = DEFAULT_BODY

    async def send_query(self):
        url = f"http://localhost:8000/{self.url_query}"
        async with httpx.AsyncClient() as client:
            match self.method:
                case "GET":
                    res = await client.get(url)
                case "POST":
                    res = await client.post(url, data=self.body)
                case "PUT":
                    res = await client.put(url, data=self.body)
                case "DELETE":
                    res = await client.delete(url)
                case _:
                    res = None
        self.response_code = res.status_code
        if self.response_code == 200:
            self.response = json.dumps(res.json(), indent=2)
            self._db_updated = True
        else:
            self.response = res.content.decode()


def data_display():
    return rx.chakra.vstack(
        rx.chakra.heading(State.total, " products found"),
        rx.foreach(State.products, render_product),
        rx.chakra.spacer(),
        width="30vw",
        height="100%",
    )


def render_product(product: Product):
    return rx.chakra.hstack(
        rx.chakra.image(src=product.image, height="100%", width="3vw"),
        rx.chakra.text(f"({product.code}) {product.label}", width="10vw"),
        rx.chakra.vstack(
            rx.chakra.text("Stock:", product.quantity),
            rx.chakra.text("Category:", product.category),
            spacing="0",
            width="7vw",
        ),
        rx.chakra.vstack(
            rx.chakra.text("Seller:", product.seller),
            rx.chakra.text("Sender:", product.sender),
            spacing="0",
            width="7vw",
        ),
        rx.chakra.spacer(),
        border="solid black 1px",
        spcaing="5",
        width="100%",
    )


def query_form():
    return rx.chakra.vstack(
        rx.chakra.hstack(
            rx.chakra.text("Query:"),
            rx.chakra.select(
                ["GET", "POST", "PUT", "DELETE"],
                on_change=QueryState.update_method,
            ),
            rx.chakra.input(
                value=QueryState.url_query,
                on_change=QueryState.set_url_query,
                width="30vw",
            ),
        ),
        rx.chakra.text("Body:"),
        rx.chakra.text_area(
            value=QueryState.body, height="30vh", on_change=QueryState.set_body
        ),
        rx.chakra.hstack(
            rx.chakra.button("Clear", on_click=QueryState.clear_query),
            rx.chakra.button("Send", on_click=QueryState.send_query),
        ),
        rx.chakra.divider(orientation="horizontal", border="solid black 1px", width="100%"),
        rx.chakra.hstack(
            rx.chakra.text("Status: ", QueryState.response_code), rx.chakra.spacer(), width="100%"
        ),
        rx.chakra.container(
            rx.markdown(
                QueryState.f_response,
                language="json",
                height="30vh",
            )
        ),
        # width="50vw",
        width="100%",
    )


def index() -> rx.Component:
    return rx.chakra.hstack(
        rx.chakra.spacer(),
        data_display(),
        rx.chakra.spacer(),
        rx.chakra.divider(orientation="vertical", border="solid black 1px"),
        query_form(),
        rx.chakra.spacer(),
        height="100vh",
        width="100vw",
        spacing="0",
    )


app = rx.App()
app.add_page(index, on_load=State.load_product)

app.api.include_router(product_router)
