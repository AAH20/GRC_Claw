"""Resource Allocation Agent — optimizes compute, storage, and API quota distribution."""

from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass
from enum import StrEnum

import structlog

logger = structlog.get_logger(__name__)


class AllocationStrategy(StrEnum):
    """Strategy for resource allocation."""

    WEIGHTED_FAIR = "weighted_fair"
    PRIORITY_BASED = "priority_based"
    ROUND_ROBIN = "round_robin"


@dataclass
class ResourceRequest:
    """Represents a resource request from a project."""

    project_id: str
    cpu_cores: float
    memory_gb: float
    storage_gb: float
    api_quota: int
    priority: int = 5  # 1 (highest) to 10 (lowest)


@dataclass
class ResourceAllocation:
    """Represents an allocated set of resources."""

    project_id: str
    allocated_cpu: float
    allocated_memory: float
    allocated_storage: float
    allocated_api_quota: int
    strategy_used: str


@dataclass
class ResourcePool:
    """Represents the total available resource pool."""

    total_cpu: float = 64.0
    total_memory: float = 256.0
    total_storage: float = 2048.0
    total_api_quota: int = 100_000
    overcommit_ratio: float = 1.2

    @property
    def effective_cpu(self) -> float:
        """Effective CPU after overcommit."""
        return self.total_cpu * self.overcommit_ratio

    @property
    def effective_memory(self) -> float:
        """Effective memory after overcommit."""
        return self.total_memory * self.overcommit_ratio

    @property
    def effective_storage(self) -> float:
        """Effective storage after overcommit."""
        return self.total_storage * self.overcommit_ratio

    @property
    def effective_api_quota(self) -> int:
        """Effective API quota after overcommit."""
        return int(self.total_api_quota * self.overcommit_ratio)


class ResourceAllocationAgent:
    """Optimizes compute, storage, and API quota distribution across projects.

    Uses a weighted fair sharing strategy by default, with support for
    priority-based preemption and round-robin distribution.
    """

    def __init__(
        self,
        strategy: AllocationStrategy = AllocationStrategy.WEIGHTED_FAIR,
        rebalance_interval: int = 600,
        pool: ResourcePool | None = None,
    ) -> None:
        """Initialize the Resource Allocation Agent.

        Args:
            strategy: Allocation strategy to use.
            rebalance_interval: Seconds between automatic rebalancing.
            pool: The resource pool to allocate from.
        """
        self._strategy = strategy
        self._rebalance_interval = rebalance_interval
        self._pool = pool or ResourcePool()
        self._requests: dict[str, ResourceRequest] = {}
        self._allocations: dict[str, ResourceAllocation] = {}
        self._running = False
        self._rebalance_task: asyncio.Task[None] | None = None

    @property
    def is_running(self) -> bool:
        """Check if the background rebalancing loop is active."""
        return self._running

    @property
    def allocations(self) -> dict[str, ResourceAllocation]:
        """Return current allocations."""
        return dict(self._allocations)

    async def start(self) -> None:
        """Start the background rebalancing loop."""
        if self._running:
            logger.warning("ResourceAllocationAgent already running")
            return
        self._running = True
        self._rebalance_task = asyncio.create_task(self._rebalance_loop())
        logger.info("ResourceAllocationAgent started", strategy=self._strategy.value)

    async def stop(self) -> None:
        """Stop the background rebalancing loop."""
        self._running = False
        if self._rebalance_task:
            self._rebalance_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._rebalance_task
        logger.info("ResourceAllocationAgent stopped")

    async def _rebalance_loop(self) -> None:
        """Background loop that periodically rebalances resources."""
        while self._running:
            try:
                self.rebalance()
            except Exception as exc:
                logger.error("Rebalance failed", error=str(exc))
            await asyncio.sleep(self._rebalance_interval)

    def submit_request(self, request: ResourceRequest) -> None:
        """Submit a resource request.

        Args:
            request: The resource request to submit.
        """
        self._requests[request.project_id] = request
        logger.info(
            "Resource request submitted",
            project_id=request.project_id,
            cpu=request.cpu_cores,
            memory=request.memory_gb,
        )

    def cancel_request(self, project_id: str) -> bool:
        """Cancel a resource request.

        Args:
            project_id: The project whose request to cancel.

        Returns:
            True if a request was found and cancelled.
        """
        if project_id in self._requests:
            del self._requests[project_id]
            self._allocations.pop(project_id, None)
            logger.info("Resource request cancelled", project_id=project_id)
            return True
        return False

    def rebalance(self) -> dict[str, ResourceAllocation]:
        """Rebalance all resource allocations.

        Returns:
            Updated allocations dictionary.
        """
        if not self._requests:
            return {}

        if self._strategy == AllocationStrategy.WEIGHTED_FAIR:
            self._allocations_weighted_fair()
        elif self._strategy == AllocationStrategy.PRIORITY_BASED:
            self._allocations_priority_based()
        elif self._strategy == AllocationStrategy.ROUND_ROBIN:
            self._allocations_round_robin()

        logger.info(
            "Resources rebalanced",
            strategy=self._strategy.value,
            num_projects=len(self._allocations),
        )
        return dict(self._allocations)

    def _allocations_weighted_fair(self) -> None:
        """Allocate resources using weighted fair sharing."""
        if not self._requests:
            return

        # Calculate total weight (inverse of priority)
        total_weight = sum(1.0 / r.priority for r in self._requests.values())

        for project_id, request in self._requests.items():
            weight = (1.0 / request.priority) / total_weight
            self._allocations[project_id] = ResourceAllocation(
                project_id=project_id,
                allocated_cpu=min(request.cpu_cores, self._pool.effective_cpu * weight),
                allocated_memory=min(request.memory_gb, self._pool.effective_memory * weight),
                allocated_storage=min(request.storage_gb, self._pool.effective_storage * weight),
                allocated_api_quota=min(
                    request.api_quota, int(self._pool.effective_api_quota * weight)
                ),
                strategy_used=AllocationStrategy.WEIGHTED_FAIR.value,
            )

    def _allocations_priority_based(self) -> None:
        """Allocate resources based on priority (lower number = higher priority)."""
        sorted_requests = sorted(self._requests.values(), key=lambda r: r.priority)
        remaining_cpu = self._pool.effective_cpu
        remaining_memory = self._pool.effective_memory
        remaining_storage = self._pool.effective_storage
        remaining_quota = self._pool.effective_api_quota

        for request in sorted_requests:
            alloc_cpu = min(request.cpu_cores, remaining_cpu)
            alloc_mem = min(request.memory_gb, remaining_memory)
            alloc_storage = min(request.storage_gb, remaining_storage)
            alloc_quota = min(request.api_quota, remaining_quota)

            self._allocations[request.project_id] = ResourceAllocation(
                project_id=request.project_id,
                allocated_cpu=alloc_cpu,
                allocated_memory=alloc_mem,
                allocated_storage=alloc_storage,
                allocated_api_quota=alloc_quota,
                strategy_used=AllocationStrategy.PRIORITY_BASED.value,
            )

            remaining_cpu -= alloc_cpu
            remaining_memory -= alloc_mem
            remaining_storage -= alloc_storage
            remaining_quota -= alloc_quota

    def _allocations_round_robin(self) -> None:
        """Allocate resources equally among all requesters."""
        if not self._requests:
            return

        count = len(self._requests)
        equal_cpu = self._pool.effective_cpu / count
        equal_mem = self._pool.effective_memory / count
        equal_storage = self._pool.effective_storage / count
        equal_quota = self._pool.effective_api_quota // count

        for project_id, request in self._requests.items():
            self._allocations[project_id] = ResourceAllocation(
                project_id=project_id,
                allocated_cpu=min(request.cpu_cores, equal_cpu),
                allocated_memory=min(request.memory_gb, equal_mem),
                allocated_storage=min(request.storage_gb, equal_storage),
                allocated_api_quota=min(request.api_quota, equal_quota),
                strategy_used=AllocationStrategy.ROUND_ROBIN.value,
            )

    def get_allocation(self, project_id: str) -> ResourceAllocation | None:
        """Get the allocation for a specific project.

        Args:
            project_id: The project to look up.

        Returns:
            The resource allocation or None.
        """
        return self._allocations.get(project_id)

    def get_utilization(self) -> dict[str, float]:
        """Get current resource utilization percentages.

        Returns:
            Dictionary with utilization percentages for each resource type.
        """
        used_cpu = sum(a.allocated_cpu for a in self._allocations.values())
        used_mem = sum(a.allocated_memory for a in self._allocations.values())
        used_storage = sum(a.allocated_storage for a in self._allocations.values())
        used_quota = sum(a.allocated_api_quota for a in self._allocations.values())

        return {
            "cpu_percent": (used_cpu / self._pool.effective_cpu) * 100,
            "memory_percent": (used_mem / self._pool.effective_memory) * 100,
            "storage_percent": (used_storage / self._pool.effective_storage) * 100,
            "api_quota_percent": (used_quota / self._pool.effective_api_quota) * 100,
        }
