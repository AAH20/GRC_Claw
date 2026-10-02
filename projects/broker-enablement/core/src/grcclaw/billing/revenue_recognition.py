"""
Revenue Recognition Engine for GRC_Claw.

Implements ASC 606 / IFRS 15 compliant revenue recognition.
Supports multiple recognition methods: point-in-time, over-time,
milestone-based, and usage-based recognition.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Optional
import calendar

from .models import (
    BillingCycle,
    Invoice,
    RevenueRecognitionEntry,
    RevenueRecognitionMethod,
    PaymentStatus,
)


class RevenueRecognitionEngine:
    """
    Revenue recognition engine implementing ASC 606 / IFRS 15.

    Supports:
    - Point-in-time recognition (upon delivery/completion)
    - Over-time recognition (straight-line over service period)
    - Milestone-based recognition (upon milestone achievement)
    - Usage-based recognition (as usage occurs)
    """

    def __init__(self):
        self._entries: list[RevenueRecognitionEntry] = []
        self._milestones: dict[str, list[dict]] = {}

    def create_recognition_entry(
        self,
        tenant_id: str,
        amount: float,
        method: RevenueRecognitionMethod,
        performance_obligation: str,
        recognition_start: str,
        recognition_end: str,
        invoice_id: Optional[str] = None,
        billing_cycle_id: Optional[str] = None,
        currency: str = "USD",
    ) -> RevenueRecognitionEntry:
        """
        Create a revenue recognition entry.

        Args:
            tenant_id: The tenant identifier.
            amount: Total amount to recognize.
            method: Recognition method.
            performance_obligation: Description of the performance obligation.
            recognition_start: ISO format start date.
            recognition_end: ISO format end date.
            invoice_id: Optional associated invoice.
            billing_cycle_id: Optional associated billing cycle.
            currency: Currency code.

        Returns:
            The created RevenueRecognitionEntry.
        """
        entry = RevenueRecognitionEntry(
            tenant_id=tenant_id,
            invoice_id=invoice_id,
            billing_cycle_id=billing_cycle_id,
            amount=amount,
            currency=currency,
            method=method,
            performance_obligation=performance_obligation,
            recognition_start=recognition_start,
            recognition_end=recognition_end,
            remaining_to_recognize=amount,
        )

        self._entries.append(entry)
        return entry

    def recognize_revenue(
        self,
        entry_id: str,
        period_start: str,
        period_end: str,
    ) -> float:
        """
        Recognize revenue for a specific period.

        Args:
            entry_id: The recognition entry ID.
            period_start: Period start date.
            period_end: Period end date.

        Returns:
            Amount recognized in this period.
        """
        entry = self.get_entry(entry_id)
        if not entry:
            raise ValueError(f"Entry not found: {entry_id}")

        if entry.is_fully_recognized:
            return 0.0

        if entry.method == RevenueRecognitionMethod.POINT_IN_TIME:
            return self._recognize_point_in_time(entry, period_start, period_end)
        elif entry.method == RevenueRecognitionMethod.OVER_TIME:
            return self._recognize_over_time(entry, period_start, period_end)
        elif entry.method == RevenueRecognitionMethod.MILESTONE:
            return self._recognize_milestone(entry, period_start, period_end)
        elif entry.method == RevenueRecognitionMethod.USAGE_BASED:
            return self._recognize_usage_based(entry, period_start, period_end)
        else:
            return 0.0

    def recognize_all(self, period_start: str, period_end: str) -> dict:
        """
        Recognize revenue for all entries in a period.

        Returns:
            Summary of recognized revenue.
        """
        total_recognized = 0.0
        by_method = {}
        by_tenant = {}

        for entry in self._entries:
            if entry.is_fully_recognized:
                continue

            amount = self.recognize_revenue(entry.entry_id, period_start, period_end)
            if amount > 0:
                total_recognized += amount
                method = entry.method.value
                by_method[method] = by_method.get(method, 0) + amount
                by_tenant[entry.tenant_id] = by_tenant.get(entry.tenant_id, 0) + amount

        return {
            "period_start": period_start,
            "period_end": period_end,
            "total_recognized": total_recognized,
            "by_method": by_method,
            "by_tenant": by_tenant,
        }

    def get_entry(self, entry_id: str) -> Optional[RevenueRecognitionEntry]:
        """Get a recognition entry by ID."""
        for e in self._entries:
            if e.entry_id == entry_id:
                return e
        return None

    def get_entries(
        self,
        tenant_id: Optional[str] = None,
        invoice_id: Optional[str] = None,
        method: Optional[RevenueRecognitionMethod] = None,
        active_only: bool = False,
    ) -> list[RevenueRecognitionEntry]:
        """Query recognition entries with filters."""
        results = self._entries

        if tenant_id:
            results = [e for e in results if e.tenant_id == tenant_id]
        if invoice_id:
            results = [e for e in results if e.invoice_id == invoice_id]
        if method:
            results = [e for e in results if e.method == method]
        if active_only:
            results = [e for e in results if not e.is_fully_recognized]

        return results

    def get_recognition_schedule(
        self,
        entry_id: str,
    ) -> list[dict]:
        """
        Generate a recognition schedule for an entry.

        Returns:
            List of scheduled recognition amounts by period.
        """
        entry = self.get_entry(entry_id)
        if not entry:
            raise ValueError(f"Entry not found: {entry_id}")

        try:
            start = datetime.fromisoformat(entry.recognition_start.replace("Z", "+00:00"))
            end = datetime.fromisoformat(entry.recognition_end.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return []

        schedule = []

        if entry.method == RevenueRecognitionMethod.POINT_IN_TIME:
            schedule.append({
                "date": entry.recognition_end,
                "amount": entry.amount,
                "cumulative": entry.amount,
            })
        elif entry.method == RevenueRecognitionMethod.OVER_TIME:
            # Monthly straight-line recognition
            current = start
            cumulative = 0.0
            months = self._months_between(start, end)
            monthly_amount = entry.amount / max(months, 1)

            for i in range(months):
                month_end = self._add_months(start, i + 1)
                if month_end > end:
                    month_end = end

                amount = monthly_amount
                if i == months - 1:
                    # Adjust last period for rounding
                    amount = entry.amount - cumulative

                cumulative += amount
                schedule.append({
                    "date": month_end.isoformat(),
                    "amount": round(amount, 2),
                    "cumulative": round(cumulative, 2),
                })
        elif entry.method == RevenueRecognitionMethod.MILESTONE:
            milestones = self._milestones.get(entry_id, [])
            for ms in milestones:
                schedule.append({
                    "date": ms["date"],
                    "amount": ms["amount"],
                    "cumulative": sum(m["amount"] for m in milestones[:milestones.index(ms) + 1]),
                    "milestone": ms.get("name", ""),
                })

        return schedule

    def get_deferred_revenue(self, tenant_id: Optional[str] = None) -> dict:
        """
        Get deferred revenue (unrecognized) balance.

        Returns:
            Deferred revenue summary.
        """
        entries = self.get_entries(tenant_id=tenant_id, active_only=True)
        total_deferred = sum(e.remaining_to_recognize for e in entries)
        total_recognized = sum(e.recognized_to_date for e in entries)
        total_contract_value = sum(e.amount for e in entries)

        return {
            "tenant_id": tenant_id,
            "total_contract_value": total_contract_value,
            "total_recognized": total_recognized,
            "total_deferred": total_deferred,
            "entry_count": len(entries),
            "entries": [
                {
                    "entry_id": e.entry_id,
                    "performance_obligation": e.performance_obligation,
                    "method": e.method.value,
                    "total_amount": e.amount,
                    "recognized_to_date": e.recognized_to_date,
                    "remaining": e.remaining_to_recognize,
                    "recognition_start": e.recognition_start,
                    "recognition_end": e.recognition_end,
                }
                for e in entries
            ],
        }

    def get_revenue_report(
        self,
        period_start: str,
        period_end: str,
        tenant_id: Optional[str] = None,
    ) -> dict:
        """
        Generate a revenue recognition report for a period.

        Returns:
            Comprehensive revenue report.
        """
        entries = self.get_entries(tenant_id=tenant_id)
        period_recognized = 0.0
        period_details = []

        for entry in entries:
            # Check if entry overlaps with period
            if entry.recognition_end < period_start or entry.recognition_start > period_end:
                continue

            # Calculate recognized amount for this period
            try:
                entry_start = datetime.fromisoformat(entry.recognition_start.replace("Z", "+00:00"))
                entry_end = datetime.fromisoformat(entry.recognition_end.replace("Z", "+00:00"))
                report_start = datetime.fromisoformat(period_start.replace("Z", "+00:00"))
                report_end = datetime.fromisoformat(period_end.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                continue

            # Calculate overlap
            overlap_start = max(entry_start, report_start)
            overlap_end = min(entry_end, report_end)

            if entry.method == RevenueRecognitionMethod.OVER_TIME:
                total_days = (entry_end - entry_start).days
                overlap_days = (overlap_end - overlap_start).days
                if total_days > 0:
                    period_amount = entry.amount * (overlap_days / total_days)
                else:
                    period_amount = entry.amount
            elif entry.method == RevenueRecognitionMethod.POINT_IN_TIME:
                period_amount = entry.amount if entry.recognition_end <= period_end else 0.0
            else:
                period_amount = entry.period_recognized

            period_recognized += period_amount
            period_details.append({
                "entry_id": entry.entry_id,
                "tenant_id": entry.tenant_id,
                "performance_obligation": entry.performance_obligation,
                "method": entry.method.value,
                "period_amount": round(period_amount, 2),
                "total_amount": entry.amount,
            })

        return {
            "period_start": period_start,
            "period_end": period_end,
            "tenant_id": tenant_id,
            "total_recognized": round(period_recognized, 2),
            "entry_count": len(period_details),
            "details": period_details,
        }

    def add_milestone(
        self,
        entry_id: str,
        name: str,
        date: str,
        amount: float,
    ) -> None:
        """Add a milestone for milestone-based recognition."""
        if entry_id not in self._milestones:
            self._milestones[entry_id] = []
        self._milestones[entry_id].append({
            "name": name,
            "date": date,
            "amount": amount,
        })

    def _recognize_point_in_time(
        self,
        entry: RevenueRecognitionEntry,
        period_start: str,
        period_end: str,
    ) -> float:
        """Point-in-time recognition: recognize all at end date."""
        if entry.recognition_end <= period_end and entry.remaining_to_recognize > 0:
            amount = entry.remaining_to_recognize
            entry.recognized_to_date += amount
            entry.remaining_to_recognize = 0.0
            entry.period_recognized = amount
            entry.is_fully_recognized = True
            return amount
        return 0.0

    def _recognize_over_time(
        self,
        entry: RevenueRecognitionEntry,
        period_start: str,
        period_end: str,
    ) -> float:
        """Over-time recognition: straight-line over service period."""
        try:
            start = datetime.fromisoformat(entry.recognition_start.replace("Z", "+00:00"))
            end = datetime.fromisoformat(entry.recognition_end.replace("Z", "+00:00"))
            p_start = datetime.fromisoformat(period_start.replace("Z", "+00:00"))
            p_end = datetime.fromisoformat(period_end.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            return 0.0

        total_days = (end - start).days
        if total_days <= 0:
            return 0.0

        # Calculate overlap
        overlap_start = max(start, p_start)
        overlap_end = min(end, p_end)

        if overlap_start >= overlap_end:
            return 0.0

        overlap_days = (overlap_end - overlap_start).days
        daily_rate = entry.amount / total_days
        amount = min(daily_rate * overlap_days, entry.remaining_to_recognize)

        entry.recognized_to_date += amount
        entry.remaining_to_recognize -= amount
        entry.period_recognized = amount

        if entry.remaining_to_recognize <= 0.01:
            entry.remaining_to_recognize = 0.0
            entry.is_fully_recognized = True

        return amount

    def _recognize_milestone(
        self,
        entry: RevenueRecognitionEntry,
        period_start: str,
        period_end: str,
    ) -> float:
        """Milestone-based recognition: recognize when milestone is achieved."""
        milestones = self._milestones.get(entry.entry_id, [])
        amount = 0.0

        for ms in milestones:
            ms_date = ms["date"]
            if period_start <= ms_date <= period_end:
                if ms["amount"] <= entry.remaining_to_recognize:
                    amount += ms["amount"]
                    entry.remaining_to_recognize -= ms["amount"]
                    entry.recognized_to_date += ms["amount"]

        entry.period_recognized = amount
        if entry.remaining_to_recognize <= 0.01:
            entry.remaining_to_recognize = 0.0
            entry.is_fully_recognized = True

        return amount

    def _recognize_usage_based(
        self,
        entry: RevenueRecognitionEntry,
        period_start: str,
        period_end: str,
    ) -> float:
        """Usage-based recognition: recognize based on usage in period."""
        # For usage-based, the period_recognized is set externally
        # based on actual usage data
        amount = entry.period_recognized
        if amount > 0:
            amount = min(amount, entry.remaining_to_recognize)
            entry.recognized_to_date += amount
            entry.remaining_to_recognize -= amount
            entry.period_recognized = 0.0  # Reset after recognition

            if entry.remaining_to_recognize <= 0.01:
                entry.remaining_to_recognize = 0.0
                entry.is_fully_recognized = True

        return amount

    def _months_between(self, start: datetime, end: datetime) -> int:
        """Calculate number of months between two dates."""
        return max(1, (end.year - start.year) * 12 + (end.month - start.month) + 1)

    def _add_months(self, dt: datetime, months: int) -> datetime:
        """Add months to a datetime."""
        month = dt.month + months
        year = dt.year + (month - 1) // 12
        month = ((month - 1) % 12) + 1
        day = min(dt.day, calendar.monthrange(year, month)[1])
        return dt.replace(year=year, month=month, day=day)
