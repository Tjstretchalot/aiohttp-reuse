import asyncio
import io
from types import SimpleNamespace

import aiohttp
import aiohttp.web


async def hello(_request: aiohttp.web.Request) -> aiohttp.web.Response:
    return aiohttp.web.Response(body=b"")


async def main() -> None:
    app = aiohttp.web.Application()
    app.router.add_post("/hello", hello)
    server_task = asyncio.create_task(aiohttp.web._run_app(app, port=3003))

    reused = 0

    async def on_connection_reuseconn(
        __client_session: aiohttp.ClientSession,
        __trace_config_ctx: SimpleNamespace,
        params: aiohttp.tracing.TraceConnectionReuseconnParams,
    ) -> None:
        nonlocal reused
        reused += 1

    tracer = aiohttp.TraceConfig()
    tracer.on_connection_reuseconn.append(on_connection_reuseconn)

    async with aiohttp.ClientSession(trace_configs=[tracer]) as session:
        async with session.post(
            "http://127.0.0.1:3003/hello",
            data=b"",
            headers={"Content-Length": "0"},
        ) as response:
            response.raise_for_status()

        assert reused == 0, f"{reused=}"

        async with session.post(
            "http://127.0.0.1:3003/hello",
            data=b"",
            headers={"Content-Length": "0"},
        ) as response:
            response.raise_for_status()

        assert reused == 1, f"{reused=}"

    reused = 0
    async with aiohttp.ClientSession(trace_configs=[tracer]) as session:
        async with session.post(
            "http://127.0.0.1:3003/hello",
            data=io.BytesIO(),
            headers={"Content-Length": "0"},
        ) as response:
            response.raise_for_status()

        assert reused == 0, f"{reused=}"

        async with session.post(
            "http://127.0.0.1:3003/hello",
            data=io.BytesIO(),
            headers={"Content-Length": "0"},
        ) as response:
            response.raise_for_status()

        assert reused == 1, f"{reused=}"

    server_task.cancel()
    await server_task


if __name__ == "__main__":
    asyncio.run(main())