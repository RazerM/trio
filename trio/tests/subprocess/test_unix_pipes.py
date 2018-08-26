import select

import os
import pytest

from ... import _core
from ..._subprocess.unix_pipes import (
    PipeSendStream, PipeReceiveStream, make_pipe
)
from ...testing import (wait_all_tasks_blocked, check_one_way_stream)

pytestmark = pytest.mark.skipif(
    os.name != "posix", reason="pipes are only supported on posix"
)


async def test_send_pipe():
    r, w = os.pipe()
    send = PipeSendStream(w)
    assert send.fileno() == w
    await send.send_all(b"123")
    assert (os.read(r, 8)) == b"123"

    os.close(r)
    os.close(w)


async def test_receive_pipe():
    r, w = os.pipe()
    recv = PipeReceiveStream(r)
    assert (recv.fileno()) == r
    os.write(w, b"123")
    assert (await recv.receive_some(8)) == b"123"

    os.close(r)
    os.close(w)


async def test_pipes_combined():
    write, read = await make_pipe()
    count = 2 ** 20

    async def sender():
        big = bytearray(count)
        await write.send_all(big)

    async def reader():
        await wait_all_tasks_blocked()
        received = 0
        while received < count:
            received += len(await read.receive_some(4096))

        assert received == count

    async with _core.open_nursery() as n:
        n.start_soon(sender)
        n.start_soon(reader)

    await read.aclose()
    await write.aclose()


async def test_send_on_closed_pipe():
    write, read = await make_pipe()
    await write.aclose()

    with pytest.raises(_core.ClosedResourceError):
        await write.send_all(b"123")

    await read.aclose()


async def test_pipe_errors():
    with pytest.raises(TypeError):
        PipeReceiveStream(None)

    with pytest.raises(ValueError):
        await PipeReceiveStream(0).receive_some(0)


async def make_clogged_pipe():
    s, r = await make_pipe()
    try:
        while True:
            # We want to totally fill up the pipe buffer.
            # This requires working around a weird feature that POSIX pipes
            # have.
            # If you do a write of <= PIPE_BUF bytes, then it's guaranteed
            # to either complete entirely, or not at all. So if we tried to
            # write PIPE_BUF bytes, and the buffer's free space is only
            # PIPE_BUF/2, then the write will raise BlockingIOError... even
            # though a smaller write could still succeed! To avoid this,
            # make sure to write >PIPE_BUF bytes each time, which disables
            # the special behavior.
            # For details, search for PIPE_BUF here:
            #   http://pubs.opengroup.org/onlinepubs/9699919799/functions/write.html
            os.write(s.fileno(), b"x" * select.PIPE_BUF * 2)
    except BlockingIOError:
        pass
    return s, r


async def test_pipe_fully():
    await check_one_way_stream(make_pipe, make_clogged_pipe)
