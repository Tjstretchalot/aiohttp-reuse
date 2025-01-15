import asyncio
import io
from types import SimpleNamespace

import aiohttp
import aiohttp.web


async def hello(_request: aiohttp.web.Request) -> aiohttp.web.Response:
    body = await _request.read()
    print(f"server received: {body!r}")
    await asyncio.sleep(0.1)
    return aiohttp.web.Response(body=b"")


async def main() -> None:
    app = aiohttp.web.Application()
    app.router.add_post("/hello", hello)
    server_task = asyncio.create_task(aiohttp.web._run_app(app, port=3003))
    # wait for server to startup
    await asyncio.sleep(1)

    reused = 0
    num_tests = 5

    async def on_connection_reuseconn(
        __client_session: aiohttp.ClientSession,
        __trace_config_ctx: SimpleNamespace,
        params: aiohttp.tracing.TraceConnectionReuseconnParams,
    ) -> None:
        nonlocal reused
        reused += 1

    tracer = aiohttp.TraceConfig()
    tracer.on_connection_reuseconn.append(on_connection_reuseconn)

    for _ in range(num_tests):
        async with aiohttp.ClientSession(trace_configs=[tracer]) as session:
            async with session.post(
                "http://127.0.0.1:3003/hello",
                data=b"test",
            ) as response:
                response.raise_for_status()

            assert reused == 0, f"{reused=}"

            async with session.post(
                "http://127.0.0.1:3003/hello",
                data=b"test",
            ) as response:
                response.raise_for_status()

            assert reused == 1, f"{reused=}"
            reused = 0

    reused = 0
    test_failed_ctr = 0
    for _ in range(num_tests):
        async with aiohttp.ClientSession(trace_configs=[tracer]) as session:
            async with session.post(
                "http://127.0.0.1:3003/hello",
                data=io.BytesIO(b"test"),
            ) as response:
                response.raise_for_status()

            assert reused == 0, f"{reused=}"

            async with session.post(
                "http://127.0.0.1:3003/hello",
                data=io.BytesIO(b"test"),
            ) as response:
                response.raise_for_status()

            if reused != 1:
                print("===============TEST FAILED===============")
                test_failed_ctr += 1

            reused = 0

    for _ in range(num_tests):
        async with aiohttp.ClientSession(trace_configs=[tracer]) as session:
            async with session.post(
                "http://127.0.0.1:3003/hello",
                data=b"test",
            ) as response:
                response.raise_for_status()

            assert reused == 0, f"{reused=}"

            async with session.post(
                "http://127.0.0.1:3003/hello",
                data=b"test",
            ) as response:
                response.raise_for_status()

            assert reused == 1, f"{reused=}"
            reused = 0

    server_task.cancel()
    try:
        await server_task
    except asyncio.CancelledError:
        ...

    assert test_failed_ctr == 0, f"test failed {test_failed_ctr}/{num_tests} times"
    print("===============TEST PASSED===============")


if __name__ == "__main__":
    asyncio.run(main())
