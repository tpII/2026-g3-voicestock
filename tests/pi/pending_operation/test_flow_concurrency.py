"""The real slot stays consistent when confirm overlaps another request."""

import threading
from pathlib import Path

from fakes import BlockingExecutor
from test_flow import EnvelopeClient, _finish, _flow, _success, _wav

from pi.pending_operation import OperationPhase, ResolutionStatus
from pi.pending_operation.flow import PendingOperationFlow


def test_a_press_during_confirm_cannot_start_another_cycle(tmp_path: Path) -> None:
    executor = BlockingExecutor()
    flow = _flow(EnvelopeClient(_success()), executor=executor)
    try:
        _finish(flow, _wav(tmp_path / "take.wav"))
        current = flow.query_port.get_current()
        assert current is not None
        result: list[object] = []

        def confirm() -> None:
            result.append(flow.resolution_port.confirm(current.operation_id))

        worker = threading.Thread(target=confirm)
        worker.start()
        assert executor.entered.wait(2)
        assert flow.try_begin_recording() is False
        assert flow.get_status().phase is OperationPhase.WAIT_CONFIRMATION
        executor.release.set()
        worker.join(2)

        assert not worker.is_alive()
        assert result[0].status is ResolutionStatus.SUCCESS  # type: ignore[attr-defined]
        assert flow.get_status().phase is OperationPhase.IDLE
        assert flow.query_port.get_current() is None
        assert executor.calls == 1
    finally:
        executor.release.set()
        flow.close()


def test_overlapping_confirms_on_the_flow_execute_once(tmp_path: Path) -> None:
    executor = BlockingExecutor()
    flow = _flow(EnvelopeClient(_success()), executor=executor)
    try:
        _finish(flow, _wav(tmp_path / "take.wav"))
        current = flow.query_port.get_current()
        assert current is not None
        results: list[ResolutionStatus] = []
        results_lock = threading.Lock()

        def confirm() -> None:
            outcome = flow.resolution_port.confirm(current.operation_id)
            with results_lock:
                results.append(outcome.status)

        first = threading.Thread(target=confirm)
        second = threading.Thread(target=confirm)
        first.start()
        assert executor.entered.wait(2)
        second.start()
        executor.release.set()
        first.join(2)
        second.join(2)

        assert sorted(results) == sorted(
            [ResolutionStatus.SUCCESS, ResolutionStatus.ALREADY_RESOLVED]
        )
        assert executor.calls == 1
        assert flow.get_status().phase is OperationPhase.IDLE
    finally:
        executor.release.set()
        flow.close()


def test_cancel_waits_for_an_in_flight_confirm(tmp_path: Path) -> None:
    executor = BlockingExecutor()
    flow: PendingOperationFlow = _flow(
        EnvelopeClient(_success()),
        executor=executor,
    )
    try:
        _finish(flow, _wav(tmp_path / "take.wav"))
        current = flow.query_port.get_current()
        assert current is not None
        confirm_status: list[ResolutionStatus] = []
        cancel_status: list[ResolutionStatus] = []

        def confirm() -> None:
            confirm_status.append(
                flow.resolution_port.confirm(current.operation_id).status
            )

        def cancel() -> None:
            cancel_status.append(
                flow.resolution_port.cancel(current.operation_id).status
            )

        confirm_thread = threading.Thread(target=confirm)
        confirm_thread.start()
        assert executor.entered.wait(2)
        cancel_thread = threading.Thread(target=cancel)
        cancel_thread.start()
        executor.release.set()
        confirm_thread.join(2)
        cancel_thread.join(2)

        assert confirm_status == [ResolutionStatus.SUCCESS]
        assert cancel_status == [ResolutionStatus.CONFLICT]
        assert executor.calls == 1
        assert flow.get_status().phase is OperationPhase.IDLE
        assert flow.query_port.get_current() is None
    finally:
        executor.release.set()
        flow.close()
