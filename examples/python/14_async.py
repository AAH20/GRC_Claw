"""
GRC_Claw Python SDK - Async Operations
=======================================
Using the SDK with asyncio for concurrent operations.
"""

import asyncio
from grc_claw import GRCClawClient

async def main():
    client = GRCClawClient(
        api_key="grc_live_abc123...",
        tenant_id="org-acme",
        environment="production",
    )

    # --- Concurrent API Calls ---
    policies_task = asyncio.create_task(
        asyncio.to_thread(client.policies.list, limit=10)
    )
    agents_task = asyncio.create_task(
        asyncio.to_thread(client.agents.list, limit=10)
    )
    health_task = asyncio.create_task(
        asyncio.to_thread(client.system.health)
    )

    (policies, pagination), (agents, _), health = await asyncio.gather(
        policies_task, agents_task, health_task
    )

    print(f"Health: {health.status}")
    print(f"Policies: {pagination.total}")
    print(f"Agents: {len(agents)}")

    # --- Concurrent Enforcement Decisions ---
    decisions = await asyncio.gather(*[
        asyncio.to_thread(
            client.enforcement.decide,
            agent_id=f"agent-{i}",
            action="read",
            resource=f"s3://bucket/file{i}.csv",
        )
        for i in range(10)
    ])

    for d in decisions:
        print(f"  {d.decision_id}: {d.verdict}")

    client.close()

asyncio.run(main())