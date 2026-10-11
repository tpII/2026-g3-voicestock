"""One resolution lock: overlapping requests cannot both win."""

import threading

from fakes import (
    BlockingExecutor,
    MemorySlot,
    ScriptedExecutor,
    coca_cola_view,
)

from pi.pending_operation import (
    PendingOperationGateway,
    PendingOperationView,
    ResolutionResult,
    ResolutionStatus,
)


class BlockingClearSlot(MemorySlot):
    """Blocks inside clear so a second request overlaps cancellation."""

    def __init__(self, current_view: PendingOperationView | None) -> None:
        super().__init__(current_view)
        self.entered = threading.Event()
        self.release = threading.Event()

    def clear(self, operation_id: str) -> bool:
        self.entered.set()
        if not self.release.wait(2):
            raise TimeoutError("clear was not released")
        return super().clear(operation_id)


def _join(threads: list[threading.Thread]) -> None:
    for thread in threads:
        thread.join(2)
        assert not thread.is_alive()


def test_overlapping_confirms_execute_once() -> None:
    view = coca_cola_view()
    slot = MemorySlot(view)
    executor = BlockingExecutor()
    gateway = PendingOperationGateway(slot, executor)
    results: list[ResolutionResult] = []
    results_lock = threading.Lock()

    def confirm() -> None:
        result = gateway.confirm(view.operation_id)
        with results_lock:
            results.append(result)

    first = threading.Thread(target=confirm)
    second = threading.Thread(target=confirm)
    first.start()
    assert executor.entered.wait(2)
    second.start()
    executor.release.set()
    _join([first, second])

    statuses = sorted(result.status for result in results)
    assert statuses == sorted(
        [ResolutionStatus.SUCCESS, ResolutionStatus.ALREADY_RESOLVED]
    )
    assert executor.calls == 1
    assert slot.current_view is None


def test_cancel_waits_until_confirm_finishes_executing() -> None:
    view = coca_cola_view()
    slot = MemorySlot(view)
    executor = BlockingExecutor()
    gateway = PendingOperationGateway(slot, executor)
    confirm_result: list[ResolutionResult] = []
    cancel_result: list[ResolutionResult] = []

    def confirm() -> None:
        confirm_result.append(gateway.confirm(view.operation_id))

    def cancel() -> None:
        cancel_result.append(gateway.cancel(view.operation_id))

    confirm_thread = threading.Thread(target=confirm)
    confirm_thread.start()
    assert executor.entered.wait(2)
    cancel_thread = threading.Thread(target=cancel)
    cancel_thread.start()
    executor.release.set()
    _join([confirm_thread, cancel_thread])

    assert confirm_result[0].status is ResolutionStatus.SUCCESS
    assert cancel_result[0].status is ResolutionStatus.CONFLICT
    assert cancel_result[0].resolved_action is not None
    assert cancel_result[0].resolved_action.value == "confirm"
    assert executor.calls == 1
    assert slot.current_view is None


def test_confirm_waits_until_cancel_finishes() -> None:
    view = coca_cola_view()
    slot = BlockingClearSlot(view)
    executor = ScriptedExecutor()
    gateway = PendingOperationGateway(slot, executor)
    confirm_result: list[ResolutionResult] = []
    cancel_result: list[ResolutionResult] = []

    def cancel() -> None:
        cancel_result.append(gateway.cancel(view.operation_id))

    def confirm() -> None:
        confirm_result.append(gateway.confirm(view.operation_id))

    cancel_thread = threading.Thread(target=cancel)
    cancel_thread.start()
    assert slot.entered.wait(2)
    confirm_thread = threading.Thread(target=confirm)
    confirm_thread.start()
    slot.release.set()
    _join([cancel_thread, confirm_thread])

    assert cancel_result[0].status is ResolutionStatus.SUCCESS
    assert confirm_result[0].status is ResolutionStatus.CONFLICT
    assert confirm_result[0].resolved_action is not None
    assert confirm_result[0].resolved_action.value == "cancel"
    assert executor.calls == 0
    assert slot.current_view is None
