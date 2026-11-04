"""Seam the pending-operation owner uses to hold the current item.

``PendingOperationFlow`` owns the FSM and implements this protocol.
This protocol is not a second domain model.
"""

from typing import Protocol

from pi.pending_operation.view import PendingOperationView


class PendingOperationSlot(Protocol):
    """The single current pending operation, as seen by the application policy.

    Only ``PendingOperationGateway`` may call ``clear``, and only while it
    holds its resolution lock. The owner must not mutate the slot from another
    thread.
    """

    def current(self) -> PendingOperationView | None:
        """Return the current snapshot, or None when nothing is pending."""

    def clear(self, operation_id: str) -> bool:
        """Drop the pending operation when its id still matches.

        Return False when there is none or the id differs. Do not execute
        inventory logic here.
        """
