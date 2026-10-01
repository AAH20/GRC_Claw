"""
Payment Tracker for GRC_Claw.

Tracks payments, manages payment methods, handles refunds,
and monitors payment status across multiple payment processors.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
import threading

from .models import (
    Invoice,
    Payment,
    PaymentMethod,
    PaymentStatus,
    BillingStatus,
)


class PaymentTracker:
    """
    Tracks all payment-related activities.

    Manages payment records, payment methods, refunds, and
    reconciliation with invoices. Thread-safe for concurrent operations.
    """

    def __init__(self):
        self._payments: list[Payment] = []
        self._payment_methods: dict[str, list[PaymentMethod]] = {}
        self._lock = threading.Lock()
        self._processors: dict[str, callable] = {}

    def register_processor(self, name: str, processor: callable) -> None:
        """
        Register a payment processor callback.

        The processor should accept (amount, currency, method, metadata)
        and return a dict with 'success', 'transaction_id', and optionally 'error'.
        """
        self._processors[name] = processor

    def add_payment_method(self, method: PaymentMethod) -> PaymentMethod:
        """Add a payment method for a tenant."""
        with self._lock:
            if method.tenant_id not in self._payment_methods:
                self._payment_methods[method.tenant_id] = []

            # If this is the first method or marked as default, update defaults
            if method.is_default or not self._payment_methods[method.tenant_id]:
                for m in self._payment_methods[method.tenant_id]:
                    m.is_default = False
                method.is_default = True

            self._payment_methods[method.tenant_id].append(method)
        return method

    def get_payment_methods(self, tenant_id: str) -> list[PaymentMethod]:
        """Get all payment methods for a tenant."""
        return self._payment_methods.get(tenant_id, [])

    def get_default_method(self, tenant_id: str) -> Optional[PaymentMethod]:
        """Get the default payment method for a tenant."""
        methods = self._payment_methods.get(tenant_id, [])
        for m in methods:
            if m.is_default:
                return m
        return methods[0] if methods else None

    def remove_payment_method(self, tenant_id: str, method_id: str) -> bool:
        """Remove a payment method."""
        with self._lock:
            methods = self._payment_methods.get(tenant_id, [])
            for i, m in enumerate(methods):
                if m.method_id == method_id:
                    was_default = m.is_default
                    methods.pop(i)
                    # If removed was default, set first remaining as default
                    if was_default and methods:
                        methods[0].is_default = True
                    return True
        return False

    def process_payment(
        self,
        tenant_id: str,
        invoice_id: str,
        amount: float,
        method: str = "credit_card",
        method_id: Optional[str] = None,
        currency: str = "USD",
        metadata: Optional[dict] = None,
    ) -> Payment:
        """
        Process a payment for an invoice.

        Args:
            tenant_id: The tenant identifier.
            invoice_id: The invoice being paid.
            amount: The payment amount.
            method: Payment method type.
            method_id: Optional specific payment method ID.
            currency: Currency code.
            metadata: Additional payment metadata.

        Returns:
            The created Payment record.
        """
        if amount <= 0:
            raise ValueError("Payment amount must be > 0")

        payment = Payment(
            tenant_id=tenant_id,
            invoice_id=invoice_id,
            amount=amount,
            currency=currency,
            status=PaymentStatus.PENDING,
            method=method,
            method_id=method_id,
            metadata=metadata or {},
        )

        # Try to process with registered processor
        processor = self._processors.get(method)
        if processor:
            try:
                result = processor(
                    amount=amount,
                    currency=currency,
                    method=method,
                    metadata=metadata or {},
                )
                if result.get("success"):
                    payment.status = PaymentStatus.COMPLETED
                    payment.transaction_id = result.get("transaction_id")
                    payment.processed_at = datetime.now(timezone.utc).isoformat()
                else:
                    payment.status = PaymentStatus.FAILED
                    payment.failure_reason = result.get("error", "Unknown error")
            except Exception as e:
                payment.status = PaymentStatus.FAILED
                payment.failure_reason = str(e)
        else:
            # No processor registered - mark as completed for testing
            payment.status = PaymentStatus.COMPLETED
            payment.transaction_id = f"TXN-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
            payment.processed_at = datetime.now(timezone.utc).isoformat()

        with self._lock:
            self._payments.append(payment)

        return payment

    def process_refund(
        self,
        payment_id: str,
        amount: Optional[float] = None,
        reason: str = "",
    ) -> Payment:
        """
        Process a refund for a payment.

        Args:
            payment_id: The original payment ID.
            amount: Refund amount (defaults to full payment amount).
            reason: Reason for the refund.

        Returns:
            The refund Payment record.
        """
        original = self.get_payment(payment_id)
        if not original:
            raise ValueError(f"Payment not found: {payment_id}")

        if original.status != PaymentStatus.COMPLETED:
            raise ValueError(f"Cannot refund payment with status: {original.status.value}")

        refund_amount = amount or original.amount
        if refund_amount > original.amount - original.refund_amount:
            raise ValueError("Refund amount exceeds available refundable amount")

        refund = Payment(
            tenant_id=original.tenant_id,
            invoice_id=original.invoice_id,
            amount=-refund_amount,
            currency=original.currency,
            status=PaymentStatus.COMPLETED,
            method=original.method,
            transaction_id=f"REF-{original.transaction_id}",
            processed_at=datetime.now(timezone.utc).isoformat(),
            metadata={"refund_reason": reason, "original_payment": payment_id},
        )

        with self._lock:
            self._payments.append(refund)
            original.refund_amount += refund_amount

            if original.refund_amount >= original.amount:
                original.status = PaymentStatus.REFUNDED
            else:
                original.status = PaymentStatus.PARTIALLY_REFUNDED

        return refund

    def get_payment(self, payment_id: str) -> Optional[Payment]:
        """Get a payment by ID."""
        for p in self._payments:
            if p.payment_id == payment_id:
                return p
        return None

    def get_payments(
        self,
        tenant_id: Optional[str] = None,
        invoice_id: Optional[str] = None,
        status: Optional[PaymentStatus] = None,
    ) -> list[Payment]:
        """Query payments with filters."""
        results = self._payments

        if tenant_id:
            results = [p for p in results if p.tenant_id == tenant_id]
        if invoice_id:
            results = [p for p in results if p.invoice_id == invoice_id]
        if status:
            results = [p for p in results if p.status == status]

        return results

    def get_invoice_payments(self, invoice_id: str) -> list[Payment]:
        """Get all payments for an invoice."""
        return [p for p in self._payments if p.invoice_id == invoice_id]

    def get_invoice_balance(self, invoice: Invoice) -> float:
        """
        Get the remaining balance on an invoice.

        Args:
            invoice: The invoice to check.

        Returns:
            The remaining balance.
        """
        payments = self.get_invoice_payments(invoice.invoice_id)
        total_paid = sum(p.amount for p in payments if p.status == PaymentStatus.COMPLETED and p.amount > 0)
        total_refunded = sum(abs(p.amount) for p in payments if p.amount < 0)
        return invoice.total - total_paid + total_refunded

    def is_invoice_paid(self, invoice: Invoice) -> bool:
        """Check if an invoice is fully paid."""
        return self.get_invoice_balance(invoice) <= 0

    def get_tenant_balance(self, tenant_id: str) -> dict:
        """
        Get the total balance summary for a tenant.

        Returns:
            Dictionary with balance details.
        """
        payments = self.get_payments(tenant_id=tenant_id)
        total_paid = sum(p.amount for p in payments if p.status == PaymentStatus.COMPLETED and p.amount > 0)
        total_refunded = sum(abs(p.amount) for p in payments if p.amount < 0)
        total_pending = sum(p.amount for p in payments if p.status == PaymentStatus.PENDING)
        total_failed = sum(p.amount for p in payments if p.status == PaymentStatus.FAILED)

        return {
            "tenant_id": tenant_id,
            "total_paid": total_paid,
            "total_refunded": total_refunded,
            "total_pending": total_pending,
            "total_failed": total_failed,
            "net_payments": total_paid - total_refunded,
            "payment_count": len(payments),
        }

    def get_aging_report(
        self,
        invoices: list[Invoice],
        as_of_date: Optional[str] = None,
    ) -> dict:
        """
        Generate an aging report for outstanding invoices.

        Args:
            invoices: List of invoices to include.
            as_of_date: Date to calculate aging from (defaults to now).

        Returns:
            Aging report with buckets.
        """
        if as_of_date is None:
            as_of_date = datetime.now(timezone.utc).isoformat()

        try:
            as_of = datetime.fromisoformat(as_of_date.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            as_of = datetime.now(timezone.utc)

        buckets = {
            "current": {"amount": 0.0, "invoices": []},
            "1-30": {"amount": 0.0, "invoices": []},
            "31-60": {"amount": 0.0, "invoices": []},
            "61-90": {"amount": 0.0, "invoices": []},
            "90+": {"amount": 0.0, "invoices": []},
        }

        for inv in invoices:
            if inv.status in (BillingStatus.PAID, BillingStatus.REFUNDED, BillingStatus.CANCELLED):
                continue

            try:
                due = datetime.fromisoformat(inv.due_date.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                continue

            days_overdue = (as_of - due).days
            balance = self.get_invoice_balance(inv)

            if balance <= 0:
                continue

            if days_overdue <= 0:
                bucket = "current"
            elif days_overdue <= 30:
                bucket = "1-30"
            elif days_overdue <= 60:
                bucket = "31-60"
            elif days_overdue <= 90:
                bucket = "61-90"
            else:
                bucket = "90+"

            buckets[bucket]["amount"] += balance
            buckets[bucket]["invoices"].append({
                "invoice_id": inv.invoice_id,
                "invoice_number": inv.invoice_number,
                "balance": balance,
                "days_overdue": max(0, days_overdue),
            })

        return {
            "as_of_date": as_of_date,
            "buckets": buckets,
            "total_outstanding": sum(b["amount"] for b in buckets.values()),
        }

    def reconcile_invoice(self, invoice: Invoice) -> dict:
        """
        Reconcile an invoice with its payments.

        Returns:
            Reconciliation report.
        """
        payments = self.get_invoice_payments(invoice.invoice_id)
        completed = [p for p in payments if p.status == PaymentStatus.COMPLETED and p.amount > 0]
        refunds = [p for p in payments if p.amount < 0]
        pending = [p for p in payments if p.status == PaymentStatus.PENDING]
        failed = [p for p in payments if p.status == PaymentStatus.FAILED]

        total_paid = sum(p.amount for p in completed)
        total_refunded = sum(abs(p.amount) for p in refunds)
        net_paid = total_paid - total_refunded
        balance = invoice.total - net_paid

        return {
            "invoice_id": invoice.invoice_id,
            "invoice_total": invoice.total,
            "total_paid": total_paid,
            "total_refunded": total_refunded,
            "net_paid": net_paid,
            "balance_due": balance,
            "is_paid": balance <= 0,
            "payment_count": len(completed),
            "refund_count": len(refunds),
            "pending_count": len(pending),
            "failed_count": len(failed),
            "payments": [
                {
                    "payment_id": p.payment_id,
                    "amount": p.amount,
                    "status": p.status.value,
                    "method": p.method,
                    "processed_at": p.processed_at,
                }
                for p in payments
            ],
        }
