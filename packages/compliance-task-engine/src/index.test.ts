import { describe, it } from "node:test";
import assert from "node:assert/strict";
import { ComplianceTaskEngine } from "./ComplianceTaskEngine.js";

describe("ComplianceTaskEngine", () => {
  const engine = new ComplianceTaskEngine();

  it("should create a task", () => {
    const task = engine.createTask({
      title: "Implement MFA",
      description: "Deploy MFA on all critical systems",
      type: "gap_remediation",
      priority: "high",
      assigneeId: "eng-1",
      assigneeName: "Alice",
      assigneeEmail: "alice@test.com",
      framework: "ISO 27001",
      controlId: "A.9.4.2",
      controlTitle: "MFA Requirement",
      dueDate: "2025-06-30",
      createdBy: "admin",
    });

    assert.equal(task.status, "open");
    assert.equal(task.priority, "high");
    assert.equal(task.notifications.length, 2);
  });

  it("should transition task through statuses", () => {
    const task = engine.createTask({
      title: "Status Transition Test",
      description: "Test",
      type: "control_update",
      priority: "medium",
      assigneeId: "eng-1",
      assigneeName: "Alice",
      assigneeEmail: "alice@test.com",
      framework: "SOC 2",
      dueDate: "2025-06-30",
      createdBy: "admin",
    });

    engine.startTask(task.id);
    assert.equal(engine.getTask(task.id)?.status, "in_progress");

    engine.completeTask(task.id);
    assert.equal(engine.getTask(task.id)?.status, "completed");
    assert.ok(engine.getTask(task.id)?.completedAt);
  });

  it("should block a task", () => {
    const task = engine.createTask({
      title: "Block Test",
      description: "Test",
      type: "evidence_collection",
      priority: "low",
      assigneeId: "eng-1",
      assigneeName: "Alice",
      assigneeEmail: "alice@test.com",
      framework: "HIPAA",
      dueDate: "2025-06-30",
      createdBy: "admin",
    });

    engine.blockTask(task.id, "Waiting for vendor response");
    assert.equal(engine.getTask(task.id)?.status, "blocked");
    assert.equal(engine.getTask(task.id)?.comments.length, 1);
  });

  it("should enforce dependencies on completion", () => {
    const t1 = engine.createTask({
      title: "Dependency Task 1",
      description: "Test",
      type: "gap_remediation",
      priority: "high",
      assigneeId: "eng-1",
      assigneeName: "Alice",
      assigneeEmail: "alice@test.com",
      framework: "ISO 27001",
      dueDate: "2025-06-30",
      createdBy: "admin",
    });

    const t2 = engine.createTask({
      title: "Dependency Task 2",
      description: "Test",
      type: "gap_remediation",
      priority: "high",
      assigneeId: "eng-1",
      assigneeName: "Alice",
      assigneeEmail: "alice@test.com",
      framework: "ISO 27001",
      dueDate: "2025-06-30",
      dependencies: [t1.id],
      createdBy: "admin",
    });

    engine.startTask(t1.id);
    engine.blockTask(t2.id, "Waiting for task 1");

    assert.equal(engine.getTask(t2.id)?.status, "blocked");

    engine.completeTask(t1.id);
    assert.equal(engine.getTask(t2.id)?.status, "open");
  });

  it("should add comments and attachments", () => {
    const task = engine.createTask({
      title: "Comment Test",
      description: "Test",
      type: "custom",
      priority: "low",
      assigneeId: "eng-1",
      assigneeName: "Alice",
      assigneeEmail: "alice@test.com",
      framework: "General",
      dueDate: "2025-06-30",
      createdBy: "admin",
    });

    const comment = engine.addComment(task.id, "admin", "Admin", "Great progress!");
    assert.equal(comment.content, "Great progress!");

    const attachment = engine.addAttachment(task.id, "evidence.pdf", "https://example.com/evidence.pdf", "sha256hash", "admin");
    assert.equal(attachment.name, "evidence.pdf");
  });

  it("should create task from audit finding", () => {
    const task = engine.createTaskFromFinding({
      id: "finding-1",
      findingNumber: "F-001",
      title: "Missing MFA",
      description: "MFA not enabled on admin accounts",
      severity: "high",
      controlId: "A.9.4.2",
      controlTitle: "MFA",
      framework: "ISO 27001",
      remediation: "Enable MFA for all admin accounts",
      status: "open",
      dueDate: "2025-06-30",
      createdAt: new Date().toISOString(),
    });

    assert.equal(task.type, "audit_finding");
    assert.equal(task.priority, "high");
    assert.equal(task.auditFindingId, "finding-1");
  });

  it("should search tasks", () => {
    engine.createTask({
      title: "Searchable KPI Task",
      description: "Track metrics",
      type: "assessment",
      priority: "medium",
      assigneeId: "eng-1",
      assigneeName: "Alice",
      assigneeEmail: "alice@test.com",
      framework: "SOC 2",
      dueDate: "2025-06-30",
      tags: ["kpi"],
      createdBy: "admin",
    });

    const results = engine.searchTasks({ query: "KPI" });
    assert.ok(results.length >= 1);
    assert.ok(results.some((t) => t.title === "Searchable KPI Task"));
  });

  it("should filter by overdue", () => {
    const task = engine.createTask({
      title: "Overdue Test Task",
      description: "Test",
      type: "custom",
      priority: "low",
      assigneeId: "eng-1",
      assigneeName: "Alice",
      assigneeEmail: "alice@test.com",
      framework: "General",
      dueDate: "2020-01-01",
      createdBy: "admin",
    });

    const overdue = engine.searchTasks({ isOverdue: true });
    assert.ok(overdue.some((t) => t.id === task.id));
  });

  it("should return analytics", () => {
    const analytics = engine.getAnalytics();
    assert.ok(analytics.totalTasks > 0);
    assert.ok(typeof analytics.byStatus === "object");
    assert.ok(typeof analytics.byPriority === "object");
    assert.ok(typeof analytics.byType === "object");
    assert.ok(typeof analytics.byFramework === "object");
    assert.ok(Array.isArray(analytics.topAssignees));
  });

  it("should get tasks by framework", () => {
    engine.createTask({
      title: "Framework Filter Test",
      description: "Test",
      type: "policy_review",
      priority: "low",
      assigneeId: "eng-1",
      assigneeName: "Alice",
      assigneeEmail: "alice@test.com",
      framework: "PCI DSS",
      dueDate: "2025-06-30",
      createdBy: "admin",
    });

    const pciTasks = engine.getTasksByFramework("PCI DSS");
    assert.ok(pciTasks.length >= 1);
    assert.ok(pciTasks.every((t) => t.framework === "PCI DSS"));
  });

  it("should manage notifications", () => {
    const task = engine.createTask({
      title: "Notification Test",
      description: "Test",
      type: "custom",
      priority: "low",
      assigneeId: "eng-2",
      assigneeName: "Bob",
      assigneeEmail: "bob@test.com",
      framework: "General",
      dueDate: "2025-06-30",
      createdBy: "admin",
    });

    const unread = engine.getUnreadNotifications("eng-2");
    assert.ok(unread.length >= 2);

    engine.markNotificationRead(unread[0].id);
    const stillUnread = engine.getUnreadNotifications("eng-2");
    assert.ok(!stillUnread.some((n) => n.id === unread[0].id));
  });

  it("should get overdue tasks", () => {
    const overdueTasks = engine.getOverdueTasks();
    assert.ok(Array.isArray(overdueTasks));
    assert.ok(overdueTasks.some((t) => t.dueDate < new Date().toISOString()));
  });
});
