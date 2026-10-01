"""
Cost Allocation and Showback for GRC_Claw.

Provides cost allocation across departments, projects, and teams
using multiple allocation methods. Supports showback reporting
for internal chargeback and cost transparency.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime, timezone
from collections import defaultdict
import statistics

from .models import (
    CostCategory,
    CostLineItem,
    ResourceType,
    AllocationMethod,
    CostAllocation,
)


@dataclass
class AllocationRule:
    """Rule for allocating shared costs."""

    name: str = ""
    source: str = ""  # cost pool name
    targets: list[str] = field(default_factory=list)  # department/project names
    method: AllocationMethod = AllocationMethod.EQUAL_SPLIT
    weights: dict[str, float] = field(default_factory=dict)
    filter_category: Optional[CostCategory] = None
    filter_resource: Optional[ResourceType] = None


@dataclass
class DepartmentMetrics:
    """Cost metrics for a department."""

    department: str = ""
    total_cost: float = 0.0
    direct_costs: float = 0.0
    shared_costs: float = 0.0
    overhead: float = 0.0
    headcount: int = 0
    cost_per_employee: float = 0.0
    cost_by_category: dict[str, float] = field(default_factory=dict)
    cost_by_resource: dict[str, float] = field(default_factory=dict)
    allocation_pct: float = 0.0


@dataclass
class ShowbackReport:
    """Complete showback report."""

    period: str = ""
    total_cost: float = 0.0
    total_direct: float = 0.0
    total_shared: float = 0.0
    total_overhead: float = 0.0
    departments: list[DepartmentMetrics] = field(default_factory=list)
    allocations: list[CostAllocation] = field(default_factory=list)
    unallocated: float = 0.0
    currency: str = "USD"
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


@dataclass
class AllocationSummary:
    """Summary of cost allocation results."""

    total_allocated: float = 0.0
    total_unallocated: float = 0.0
    allocation_rate: float = 0.0
    by_department: dict[str, float] = field(default_factory=dict)
    by_method: dict[str, float] = field(default_factory=dict)
    by_category: dict[str, float] = field(default_factory=dict)
    allocations: list[CostAllocation] = field(default_factory=list)


class CostAllocator:
    """
    Allocates costs across departments, projects, and teams.

    Supports multiple allocation methods:
    - Direct allocation (costs directly attributed)
    - Usage-based (proportional to resource usage)
    - Headcount-based (proportional to employee count)
    - Revenue-based (proportional to revenue contribution)
    - Equal split (evenly distributed)
    - Weighted (custom weights per target)
    """

    def __init__(self):
        self.line_items: list[CostLineItem] = []
        self.allocation_rules: list[AllocationRule] = []
        self.departments: dict[str, DepartmentMetrics] = {}
        self.allocations: list[CostAllocation] = []
        self.shared_cost_pools: dict[str, float] = defaultdict(float)
        self.overhead_rate: float = 0.0

    def add_line_item(self, item: CostLineItem) -> None:
        """Add a cost line item."""
        self.line_items.append(item)

    def add_allocation_rule(self, rule: AllocationRule) -> None:
        """Add an allocation rule."""
        self.allocation_rules.append(rule)

    def set_overhead_rate(self, rate: float) -> None:
        """Set overhead rate as percentage (e.g. 0.15 = 15%)."""
        self.overhead_rate = rate

    def register_department(
        self,
        name: str,
        headcount: int = 0,
        revenue: float = 0.0,
        usage: float = 0.0,
    ) -> None:
        """Register a department with optional metrics."""
        self.departments[name] = DepartmentMetrics(
            department=name,
            headcount=headcount,
        )
        # Store additional metrics in a separate dict for allocation calculations
        if not hasattr(self, "_dept_metrics"):
            self._dept_metrics: dict[str, dict] = {}
        self._dept_metrics[name] = {
            "headcount": headcount,
            "revenue": revenue,
            "usage": usage,
        }

    def allocate_all(self) -> list[CostAllocation]:
        """
        Run all allocation rules and direct allocations.

        Returns:
            List of CostAllocation objects.
        """
        self.allocations = []

        # First, handle direct allocations
        self._allocate_direct()

        # Then, handle shared cost pools
        self._allocate_shared_costs()

        # Apply overhead
        self._apply_overhead()

        return self.allocations

    def _allocate_direct(self) -> None:
        """Allocate costs that have a direct department assignment."""
        for item in self.line_items:
            if item.allocated_to and item.allocated_to in self.departments:
                allocation = CostAllocation(
                    department=item.allocated_to,
                    project=item.tags.get("project", ""),
                    team=item.tags.get("team", ""),
                    total_allocated=item.amount,
                    direct_costs=item.amount,
                    allocation_method=AllocationMethod.DIRECT,
                    period=item.period,
                    line_items=[item],
                    cost_center=item.tags.get("cost_center", ""),
                    business_unit=item.tags.get("business_unit", ""),
                )
                self.allocations.append(allocation)

                # Update department metrics
                dept = self.departments[item.allocated_to]
                dept.total_cost += item.amount
                dept.direct_costs += item.amount

    def _allocate_shared_costs(self) -> None:
        """Allocate shared costs using allocation rules."""
        # Build shared cost pools
        for item in self.line_items:
            if not item.allocated_to or item.allocated_to not in self.departments:
                # This is an unallocated cost - add to shared pool
                pool_key = item.category.value if isinstance(item.category, CostCategory) else str(item.category)
                self.shared_cost_pools[pool_key] += item.amount

        # Apply allocation rules
        for rule in self.allocation_rules:
            pool_cost = self.shared_cost_pools.get(rule.source, 0)
            if pool_cost <= 0:
                continue

            if rule.method == AllocationMethod.EQUAL_SPLIT:
                self._allocate_equal_split(rule, pool_cost)
            elif rule.method == AllocationMethod.WEIGHTED:
                self._allocate_weighted(rule, pool_cost)
            elif rule.method == AllocationMethod.HEADCOUNT:
                self._allocate_by_headcount(rule, pool_cost)
            elif rule.method == AllocationMethod.REVENUE:
                self._allocate_by_revenue(rule, pool_cost)
            elif rule.method == AllocationMethod.USAGE_BASED:
                self._allocate_by_usage(rule, pool_cost)

    def _allocate_equal_split(self, rule: AllocationRule, amount: float) -> None:
        """Allocate cost equally among targets."""
        if not rule.targets:
            return

        per_target = amount / len(rule.targets)
        for target in rule.targets:
            if target in self.departments:
                allocation = CostAllocation(
                    department=target,
                    total_allocated=per_target,
                    shared_costs=per_target,
                    allocation_method=AllocationMethod.EQUAL_SPLIT,
                    period="",
                )
                self.allocations.append(allocation)

                dept = self.departments[target]
                dept.total_cost += per_target
                dept.shared_costs += per_target

    def _allocate_weighted(self, rule: AllocationRule, amount: float) -> None:
        """Allocate cost based on custom weights."""
        if not rule.targets or not rule.weights:
            return

        total_weight = sum(rule.weights.get(t, 0) for t in rule.targets)
        if total_weight <= 0:
            return

        for target in rule.targets:
            weight = rule.weights.get(target, 0)
            allocated = amount * (weight / total_weight)

            if target in self.departments:
                allocation = CostAllocation(
                    department=target,
                    total_allocated=allocated,
                    shared_costs=allocated,
                    allocation_method=AllocationMethod.WEIGHTED,
                    period="",
                )
                self.allocations.append(allocation)

                dept = self.departments[target]
                dept.total_cost += allocated
                dept.shared_costs += allocated

    def _allocate_by_headcount(self, rule: AllocationRule, amount: float) -> None:
        """Allocate cost proportionally by headcount."""
        if not rule.targets:
            return

        total_headcount = sum(
            self._dept_metrics.get(t, {}).get("headcount", 0)
            for t in rule.targets
        )
        if total_headcount <= 0:
            return

        for target in rule.targets:
            hc = self._dept_metrics.get(target, {}).get("headcount", 0)
            allocated = amount * (hc / total_headcount)

            if target in self.departments:
                allocation = CostAllocation(
                    department=target,
                    total_allocated=allocated,
                    shared_costs=allocated,
                    allocation_method=AllocationMethod.HEADCOUNT,
                    period="",
                )
                self.allocations.append(allocation)

                dept = self.departments[target]
                dept.total_cost += allocated
                dept.shared_costs += allocated

    def _allocate_by_revenue(self, rule: AllocationRule, amount: float) -> None:
        """Allocate cost proportionally by revenue."""
        if not rule.targets:
            return

        total_revenue = sum(
            self._dept_metrics.get(t, {}).get("revenue", 0)
            for t in rule.targets
        )
        if total_revenue <= 0:
            return

        for target in rule.targets:
            rev = self._dept_metrics.get(target, {}).get("revenue", 0)
            allocated = amount * (rev / total_revenue)

            if target in self.departments:
                allocation = CostAllocation(
                    department=target,
                    total_allocated=allocated,
                    shared_costs=allocated,
                    allocation_method=AllocationMethod.REVENUE,
                    period="",
                )
                self.allocations.append(allocation)

                dept = self.departments[target]
                dept.total_cost += allocated
                dept.shared_costs += allocated

    def _allocate_by_usage(self, rule: AllocationRule, amount: float) -> None:
        """Allocate cost proportionally by resource usage."""
        if not rule.targets:
            return

        total_usage = sum(
            self._dept_metrics.get(t, {}).get("usage", 0)
            for t in rule.targets
        )
        if total_usage <= 0:
            return

        for target in rule.targets:
            usage = self._dept_metrics.get(target, {}).get("usage", 0)
            allocated = amount * (usage / total_usage)

            if target in self.departments:
                allocation = CostAllocation(
                    department=target,
                    total_allocated=allocated,
                    shared_costs=allocated,
                    allocation_method=AllocationMethod.USAGE_BASED,
                    period="",
                )
                self.allocations.append(allocation)

                dept = self.departments[target]
                dept.total_cost += allocated
                dept.shared_costs += allocated

    def _apply_overhead(self) -> None:
        """Apply overhead to all allocations."""
        if self.overhead_rate <= 0:
            return

        for dept in self.departments.values():
            overhead = dept.total_cost * self.overhead_rate
            dept.overhead = overhead
            dept.total_cost += overhead

    def get_allocation_summary(self) -> AllocationSummary:
        """
        Get summary of cost allocation results.

        Returns:
            AllocationSummary with aggregated metrics.
        """
        if not self.allocations:
            self.allocate_all()

        total_allocated = sum(a.total_allocated for a in self.allocations)
        total_line_items = sum(item.amount for item in self.line_items)
        total_unallocated = total_line_items - total_allocated

        by_department: dict[str, float] = defaultdict(float)
        by_method: dict[str, float] = defaultdict(float)
        by_category: dict[str, float] = defaultdict(float)

        for alloc in self.allocations:
            by_department[alloc.department] += alloc.total_allocated
            method_key = alloc.allocation_method.value if isinstance(alloc.allocation_method, AllocationMethod) else str(alloc.allocation_method)
            by_method[method_key] += alloc.total_allocated

        for item in self.line_items:
            cat_key = item.category.value if isinstance(item.category, CostCategory) else str(item.category)
            by_category[cat_key] += item.amount

        allocation_rate = (total_allocated / total_line_items * 100) if total_line_items > 0 else 0

        return AllocationSummary(
            total_allocated=round(total_allocated, 2),
            total_unallocated=round(total_unallocated, 2),
            allocation_rate=round(allocation_rate, 2),
            by_department=dict(by_department),
            by_method=dict(by_method),
            by_category=dict(by_category),
            allocations=list(self.allocations),
        )

    def generate_showback_report(self, period: str = "") -> ShowbackReport:
        """
        Generate a complete showback report.

        Args:
            period: Reporting period label.

        Returns:
            ShowbackReport with all department metrics.
        """
        if not self.allocations:
            self.allocate_all()

        departments = []
        total_cost = 0.0
        total_direct = 0.0
        total_shared = 0.0
        total_overhead = 0.0

        for dept in self.departments.values():
            # Calculate cost per employee
            metrics = self._dept_metrics.get(dept.department, {})
            hc = metrics.get("headcount", 0)
            dept.cost_per_employee = dept.total_cost / hc if hc > 0 else 0

            # Calculate allocation percentage
            dept.allocation_pct = (
                (dept.total_cost / sum(d.total_cost for d in self.departments.values()) * 100)
                if self.departments and sum(d.total_cost for d in self.departments.values()) > 0
                else 0
            )

            departments.append(dept)
            total_cost += dept.total_cost
            total_direct += dept.direct_costs
            total_shared += dept.shared_costs
            total_overhead += dept.overhead

        # Calculate unallocated
        total_line_items = sum(item.amount for item in self.line_items)
        unallocated = total_line_items - total_cost

        return ShowbackReport(
            period=period,
            total_cost=round(total_cost, 2),
            total_direct=round(total_direct, 2),
            total_shared=round(total_shared, 2),
            total_overhead=round(total_overhead, 2),
            departments=departments,
            allocations=list(self.allocations),
            unallocated=round(unallocated, 2),
        )

    def get_department_ranking(self) -> list[DepartmentMetrics]:
        """
        Get departments ranked by total cost (highest first).

        Returns:
            List of DepartmentMetrics sorted by total cost.
        """
        if not self.allocations:
            self.allocate_all()

        return sorted(
            self.departments.values(),
            key=lambda d: d.total_cost,
            reverse=True,
        )

    def get_cost_per_employee_ranking(self) -> list[DepartmentMetrics]:
        """
        Get departments ranked by cost per employee (highest first).

        Returns:
            List of DepartmentMetrics sorted by cost per employee.
        """
        if not self.allocations:
            self.allocate_all()

        return sorted(
            self.departments.values(),
            key=lambda d: d.cost_per_employee,
            reverse=True,
        )

    def export_chargeback_data(self, period: str = "") -> list[dict]:
        """
        Export chargeback data in a flat format suitable for billing systems.

        Args:
            period: Reporting period label.

        Returns:
            List of dictionaries with chargeback line items.
        """
        if not self.allocations:
            self.allocate_all()

        chargeback_items = []
        for alloc in self.allocations:
            chargeback_items.append({
                "period": period or alloc.period,
                "department": alloc.department,
                "project": alloc.project,
                "team": alloc.team,
                "cost_center": alloc.cost_center,
                "business_unit": alloc.business_unit,
                "allocation_method": alloc.allocation_method.value if isinstance(alloc.allocation_method, AllocationMethod) else str(alloc.allocation_method),
                "direct_costs": round(alloc.direct_costs, 2),
                "shared_costs": round(alloc.shared_costs, 2),
                "overhead": round(alloc.overhead, 2),
                "total": round(alloc.total_allocated, 2),
            })

        return chargeback_items
