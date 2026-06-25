import { randomUUID } from "node:crypto";
import type { Incident, IncidentSeverity, IncidentType, IncidentStatus, IncidentEvidence, Notification, IncidentStats, ImpactAssessment } from "../types.js";

export class IncidentManager {
  private incidents: Map<string, Incident> = new Map();

  reportIncident(input: { title: string; type: IncidentType; severity: IncidentSeverity; description: string; reportedBy: string; assignee: string }): Incident {
    const incident: Incident = {
      id: randomUUID(),
      title: input.title,
      type: input.type,
      severity: input.severity,
      status: "detected",
      description: input.description,
      detectedAt: new Date().toISOString(),
      reportedBy: input.reportedBy,
      assignee: input.assignee,
      timeline: [{ timestamp: new Date().toISOString(), action: "Incident detected and reported", actor: input.reportedBy }],
      evidence: [],
      impact: { dataRecordsAffected: 0, systemsAffected: [], businessImpact: "", financialImpact: 0, regulatoryNotificationRequired: false, jurisdictions: [] },
      notifications: [],
      remediationSteps: [],
      createdAt: new Date().toISOString(),
    };
    this.incidents.set(incident.id, incident);
    return incident;
  }

  getIncident(id: string): Incident | undefined { return this.incidents.get(id); }
  listIncidents(): Incident[] { return Array.from(this.incidents.values()); }
  getOpenIncidents(): Incident[] { return this.listIncidents().filter((i) => i.status !== "closed"); }

  transitionIncident(id: string, status: IncidentStatus, actor: string): boolean {
    const incident = this.incidents.get(id);
    if (!incident) return false;
    incident.status = status;
    incident.timeline.push({ timestamp: new Date().toISOString(), action: `Status changed to ${status}`, actor });
    if (status === "closed") incident.closedAt = new Date().toISOString();
    return true;
  }

  addEvidence(incidentId: string, evidence: Omit<IncidentEvidence, "id" | "chainOfCustody">): IncidentEvidence | null {
    const incident = this.incidents.get(incidentId);
    if (!incident) return null;
    const newEvidence: IncidentEvidence = {
      ...evidence,
      id: randomUUID(),
      chainOfCustody: [{ timestamp: new Date().toISOString(), action: "Evidence collected", person: incident.assignee }],
    };
    incident.evidence.push(newEvidence);
    return newEvidence;
  }

  updateImpact(incidentId: string, impact: Partial<ImpactAssessment>): boolean {
    const incident = this.incidents.get(incidentId);
    if (!incident) return false;
    incident.impact = { ...incident.impact, ...impact };
    return true;
  }

  scheduleNotification(incidentId: string, type: Notification["type"], recipient: string, content: string): Notification | null {
    const incident = this.incidents.get(incidentId);
    if (!incident) return null;
    const notification: Notification = { id: randomUUID(), type, recipient, content, status: "pending" };
    incident.notifications.push(notification);
    return notification;
  }

  getStats(): IncidentStats {
    const incidents = this.listIncidents();
    const open = incidents.filter((i) => i.status !== "closed");
    const closed = incidents.filter((i) => i.status === "closed");
    const byType: Record<string, number> = {};
    for (const i of incidents) byType[i.type] = (byType[i.type] || 0) + 1;

    return {
      total: incidents.length,
      open: open.length,
      closed: closed.length,
      bySeverity: {
        critical: incidents.filter((i) => i.severity === "critical").length,
        high: incidents.filter((i) => i.severity === "high").length,
        medium: incidents.filter((i) => i.severity === "medium").length,
        low: incidents.filter((i) => i.severity === "low").length,
      },
      byType,
      avgResolutionDays: 0,
    };
  }
}
