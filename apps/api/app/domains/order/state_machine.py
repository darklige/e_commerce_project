from app.domains.order.models import OrderStatus


class OrderStateMachineError(Exception):
    pass


TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.PENDING_PAYMENT: {
        OrderStatus.PAID_PENDING_SHIPMENT,
        OrderStatus.CLOSED,
    },
    OrderStatus.PAID_PENDING_SHIPMENT: set(),
    OrderStatus.CLOSED: set(),
}


def assert_transition(from_status: OrderStatus, to_status: OrderStatus) -> None:
    if to_status not in TRANSITIONS[from_status]:
        raise OrderStateMachineError(f"cannot transition order from {from_status} to {to_status}")
