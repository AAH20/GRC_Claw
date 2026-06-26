import { SecurityGraph, SecurityGraphSeeder } from '@grc-claw/security-graph';
import { listAllFrameworkPacks } from '@grc-claw/frameworks';

let seededGraph: SecurityGraph | null = null;

export function initSecurityGraph(): SecurityGraph {
  if (seededGraph) return seededGraph;

  const graph = new SecurityGraph();
  const seeder = new SecurityGraphSeeder(graph);

  const frameworks = listAllFrameworkPacks();
  seeder.seedFromFrameworks(frameworks);
  seeder.seedAttackPaths();
  seeder.seedRiskNetwork();

  const stats = graph.getStats();
  console.log(
    `[GRAPH] Seeded security graph: ${stats.totalNodes} nodes, ${stats.totalEdges} edges ` +
    `(${Object.entries(stats.nodesByType).map(([k, v]) => `${k}:${v}`).join(', ')})`
  );

  seededGraph = graph;
  return graph;
}

export function getSecurityGraph(): SecurityGraph {
  if (!seededGraph) {
    return initSecurityGraph();
  }
  return seededGraph;
}
