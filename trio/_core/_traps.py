# These are the only 2 functions that ever yield back to the task runner.

import types
import enum
from functools import wraps

import attr

__all__ = ["cancel_shielded_checkpoint", "Abort", "wait_task_rescheduled"]


# Helper for the bottommost 'yield'. You can't use 'yield' inside an async
# function, but you can inside a generator, and if you decorate your generator
# with @types.coroutine, then it's even awaitable. However, it's still not a
# real async function: in particular, it isn't recognized by
# inspect.iscoroutinefunction, and it doesn't trigger the unawaited coroutine
# tracking machinery. Since our traps are public APIs, we make them real async
# functions, and then this helper takes care of the actual yield:
@types.coroutine
def _async_yield(obj):
    return (yield obj)


# This class object is used as a singleton.
# Not exported in the trio._core namespace, but imported directly by _run.
class CancelShieldedCheckpoint:
    pass


async def cancel_shielded_checkpoint():
    """Introduce a schedule point, but not a cancel point.

    This is *not* a :ref:`checkpoint <checkpoints>`, but it is half of a
    checkpoint, and when combined with :func:`checkpoint_if_cancelled` it can
    make a full checkpoint.

    Equivalent to (but potentially more efficient than)::

        with trio.open_cancel_scope(shield=True):
            await trio.hazmat.checkpoint()

    """
    return (await _async_yield(CancelShieldedCheckpoint)).unwrap()


# Return values for abort functions
class Abort(enum.Enum):
    """:class:`enum.Enum` used as the return value from abort functions.

    See :func:`wait_task_rescheduled` for details.

    .. data:: SUCCEEDED
              FAILED

    """
    SUCCEEDED = 1
    FAILED = 2


# Not exported in the trio._core namespace, but imported directly by _run.
@attr.s(frozen=True)
class WaitTaskRescheduled:
    abort_func = attr.ib()


async def wait_task_rescheduled(abort_func):
    """Put the current task to sleep, with cancellation support.

    This is the lowest-level API for blocking in trio. Every time a
    :class:`~trio.hazmat.Task` blocks, it does so by calling this function
    (usually indirectly via some higher-level API).

    This is a tricky interface with no guard rails. If you can use
    :class:`ParkingLot` or the built-in I/O wait functions instead, then you
    should.

    Generally the way it works is that before calling this function, you make
    arrangements for "someone" to call :func:`reschedule` on the current task
    at some later point.

    Then you call :func:`wait_task_rescheduled`, passing in ``abort_func``, an
    "abort callback".

    (Terminology: in trio, "aborting" is the process of attempting to
    interrupt a blocked task to deliver a cancellation.)

    There are two possibilities for what happens next:

    1. "Someone" calls :func:`reschedule` on the current task, and
       :func:`wait_task_rescheduled` returns or raises whatever value or error
       was passed to :func:`reschedule`.

    2. The call's context transitions to a cancelled state (e.g. due to a
       timeout expiring). When this happens, the ``abort_func`` is called. It's
       interface looks like::

           def abort_func(raise_cancel):
               ...
               return trio.hazmat.Abort.SUCCEEDED  # or FAILED

       It should attempt to clean up any state associated with this call, and
       in particular, arrange that :func:`reschedule` will *not* be called
       later. If (and only if!) it is successful, then it should return
       :data:`Abort.SUCCEEDED`, in which case the task will automatically be
       rescheduled with an appropriate :exc:`~trio.Cancelled` error.

       Otherwise, it should return :data:`Abort.FAILED`. This means that the
       task can't be cancelled at this time, and still has to make sure that
       "someone" eventually calls :func:`reschedule`.

       At that point there are again two possibilities. You can simply ignore
       the cancellation altogether: wait for the operation to complete and
       then reschedule and continue as normal. (For example, this is what
       :func:`trio.run_sync_in_worker_thread` does if cancellation is disabled.)
       The other possibility is that the ``abort_func`` does succeed in
       cancelling the operation, but for some reason isn't able to report that
       right away. (Example: on Windows, it's possible to request that an
       async ("overlapped") I/O operation be cancelled, but this request is
       *also* asynchronous – you don't find out until later whether the
       operation was actually cancelled or not.)  To report a delayed
       cancellation, then you should reschedule the task yourself, and call
       the ``raise_cancel`` callback passed to ``abort_func`` to raise a
       :exc:`~trio.Cancelled` (or possibly :exc:`KeyboardInterrupt`) exception
       into this task. Either of the approaches sketched below can work::

          # Option 1:
          # Catch the exception from raise_cancel and inject it into the task.
          # (This is what trio does automatically for you if you return
          # Abort.SUCCEEDED.)
          trio.hazmat.reschedule(task, Result.capture(raise_cancel))

          # Option 2:
          # wait to be woken by "someone", and then decide whether to raise
          # the error from inside the task.
          outer_raise_cancel = None
          def abort(inner_raise_cancel):
              nonlocal outer_raise_cancel
              outer_raise_cancel = inner_raise_cancel
              TRY_TO_CANCEL_OPERATION()
              return trio.hazmat.Abort.FAILED
          await wait_task_rescheduled(abort)
          if OPERATION_WAS_SUCCESSFULLY_CANCELLED:
              # raises the error
              outer_raise_cancel()

       In any case it's guaranteed that we only call the ``abort_func`` at most
       once per call to :func:`wait_task_rescheduled`.

    .. warning::

       If your ``abort_func`` raises an error, or returns any value other than
       :data:`Abort.SUCCEEDED` or :data:`Abort.FAILED`, then trio will crash
       violently. Be careful! Similarly, it is entirely possible to deadlock a
       trio program by failing to reschedule a blocked task, or cause havoc by
       calling :func:`reschedule` too many times. Remember what we said up
       above about how you should use a higher-level API if at all possible?

    """
    return (await _async_yield(WaitTaskRescheduled(abort_func))).unwrap()
