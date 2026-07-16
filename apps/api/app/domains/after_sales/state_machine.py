from app.domains.after_sales.models import AfterSalesStatus


class AfterSalesStateMachineError(Exception):
    pass


TRANSITIONS: dict[AfterSalesStatus, set[AfterSalesStatus]] = {
    AfterSalesStatus.MERCHANT_REVIEW: {
        AfterSalesStatus.REJECTED,
        AfterSalesStatus.WAITING_BUYER_RETURN,
        AfterSalesStatus.REFUNDING,
        AfterSalesStatus.CUSTOMER_SERVICE,
        AfterSalesStatus.CLOSED,
    },
    AfterSalesStatus.REJECTED: {
        AfterSalesStatus.MERCHANT_REVIEW,
        AfterSalesStatus.CUSTOMER_SERVICE,
        AfterSalesStatus.CLOSED,
    },
    AfterSalesStatus.WAITING_BUYER_RETURN: {
        AfterSalesStatus.WAITING_MERCHANT_RECEIPT,
        AfterSalesStatus.CLOSED,
        AfterSalesStatus.CUSTOMER_SERVICE,
    },
    AfterSalesStatus.WAITING_MERCHANT_RECEIPT: {
        AfterSalesStatus.REFUNDING,
        AfterSalesStatus.CUSTOMER_SERVICE,
    },
    AfterSalesStatus.REFUNDING: {
        AfterSalesStatus.REFUNDED,
        AfterSalesStatus.REFUND_FAILED,
    },
    AfterSalesStatus.REFUND_FAILED: {
        AfterSalesStatus.REFUNDING,
        AfterSalesStatus.CUSTOMER_SERVICE,
    },
    AfterSalesStatus.CUSTOMER_SERVICE: {
        AfterSalesStatus.MERCHANT_REVIEW,
        AfterSalesStatus.WAITING_BUYER_RETURN,
        AfterSalesStatus.REFUNDING,
        AfterSalesStatus.CLOSED,
    },
    AfterSalesStatus.REFUNDED: set(),
    AfterSalesStatus.CLOSED: set(),
}


def assert_transition(from_status: AfterSalesStatus, to_status: AfterSalesStatus) -> None:
    if to_status not in TRANSITIONS[from_status]:
        raise AfterSalesStateMachineError(
            f"cannot transition after-sales from {from_status} to {to_status}"
        )
