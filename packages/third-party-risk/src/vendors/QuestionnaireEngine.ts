import type { VendorAssessment, AssessmentQuestion, FrameworkCode } from "../types.js";

const QUESTIONNAIRES: Record<string, AssessmentQuestion[]> = {
  soc2: [
    { id: "q1", category: "Access Control", question: "Do you enforce MFA for all user access?", required: true, type: "boolean" },
    { id: "q2", category: "Access Control", question: "How do you manage role-based access control?", required: true, type: "text" },
    { id: "q3", category: "Encryption", question: "Do you encrypt data at rest and in transit?", required: true, type: "boolean" },
    { id: "q4", category: "Monitoring", question: "Do you have 24/7 security monitoring?", required: true, type: "boolean" },
    { id: "q5", category: "Incident Response", question: "Describe your incident response process.", required: true, type: "text" },
    { id: "q6", category: "Vendor Management", question: "How do you assess sub-processor risk?", required: false, type: "text" },
  ],
  iso27001: [
    { id: "q1", category: "Governance", question: "Do you have an Information Security Management System (ISMS)?", required: true, type: "boolean" },
    { id: "q2", category: "Governance", question: "When was your last ISO 27001 audit?", required: true, type: "text" },
    { id: "q3", category: "Risk Management", question: "Do you perform annual risk assessments?", required: true, type: "boolean" },
    { id: "q4", category: "Controls", question: "List your key security controls.", required: true, type: "text" },
    { id: "q5", category: "Continual Improvement", question: "How do you track and remediate non-conformities?", required: true, type: "text" },
  ],
  gdpr: [
    { id: "q1", category: "Data Processing", question: "Do you have a Data Processing Agreement (DPA)?", required: true, type: "boolean" },
    { id: "q2", category: "Data Subject Rights", question: "How do you handle DSAR requests?", required: true, type: "text" },
    { id: "q3", category: "Cross-Border", question: "Do you transfer data outside the EU/EEA?", required: true, type: "boolean" },
    { id: "q4", category: "Breach Notification", question: "What is your breach notification timeline?", required: true, type: "text" },
    { id: "q5", category: "DPO", question: "Do you have a Data Protection Officer?", required: false, type: "boolean" },
  ],
};

export class QuestionnaireEngine {
  getQuestionnaire(framework: FrameworkCode): AssessmentQuestion[] {
    return QUESTIONNAIRES[framework] || QUESTIONNAIRES.soc2;
  }

  createAssessment(vendorId: string, framework: FrameworkCode): VendorAssessment {
    const questions = this.getQuestionnaire(framework);
    return {
      id: `assess-${Date.now()}`,
      vendorId,
      type: "questionnaire",
      status: "pending",
      framework,
      questions,
      responses: {},
      score: 0,
      findings: [],
      createdAt: new Date().toISOString(),
    };
  }

  calculateScore(responses: Record<string, string>, questions: AssessmentQuestion[]): number {
    const requiredQuestions = questions.filter((q) => q.required);
    const answeredRequired = requiredQuestions.filter((q) => responses[q.id] && responses[q.id].trim().length > 0);
    const booleanYes = requiredQuestions.filter((q) => q.type === "boolean" && responses[q.id] === "true");
    const baseScore = (answeredRequired.length / requiredQuestions.length) * 70;
    const qualityScore = (booleanYes.length / requiredQuestions.filter((q) => q.type === "boolean").length) * 30;
    return Math.round(baseScore + qualityScore);
  }

  autoGenerateResponses(vendorName: string, framework: FrameworkCode): Record<string, string> {
    const questions = this.getQuestionnaire(framework);
    const responses: Record<string, string> = {};
    for (const q of questions) {
      if (q.type === "boolean") {
        responses[q.id] = "true";
      } else {
        responses[q.id] = `${vendorName} implements industry-standard ${q.category.toLowerCase()} controls as part of their ${framework.toUpperCase()} compliance program.`;
      }
    }
    return responses;
  }
}
