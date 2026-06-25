import type { SecurityQuestion } from "../types.js";

const KNOWLEDGE_BASE: Record<string, Record<string, string>> = {
  encryption: {
    "data at rest": "We use AES-256 encryption for all data at rest across production databases and storage systems.",
    "data in transit": "All data in transit is encrypted using TLS 1.3. We enforce HTTPS across all endpoints.",
    "key management": "Encryption keys are managed via AWS KMS with automatic rotation every 90 days.",
  },
  access_control: {
    "mfa": "Multi-factor authentication is enforced for all employee and customer accounts.",
    "rbac": "Role-based access control is implemented across all systems with least-privilege principles.",
    "sso": "Single sign-on via SAML 2.0/OIDC is supported for enterprise customers.",
  },
  monitoring: {
    "siem": "We operate a 24/7 SOC with real-time SIEM monitoring using industry-standard tools.",
    "logging": "All access and system events are logged with 1-year retention.",
    "ids": "Intrusion detection systems are deployed at network and application layers.",
  },
  compliance: {
    "soc2": "We maintain SOC 2 Type II certification, audited annually.",
    "iso27001": "ISO 27001 certification is maintained with annual surveillance audits.",
    "gdpr": "GDPR compliance is maintained with a designated DPO and documented procedures.",
  },
};

export class SecurityQuestionnaireResponder {
  answerQuestion(question: string): SecurityQuestion {
    const lower = question.toLowerCase();
    let bestMatch = { response: "This information is available upon request under NDA.", confidence: 0.3, category: "general" };

    for (const [category, answers] of Object.entries(KNOWLEDGE_BASE)) {
      for (const [keyword, response] of Object.entries(answers)) {
        if (lower.includes(keyword)) {
          bestMatch = { response, confidence: 0.95, category };
          break;
        }
      }
    }

    return {
      id: `sq-${Date.now()}`,
      question,
      category: bestMatch.category,
      autoAnswered: bestMatch.confidence > 0.8,
      response: bestMatch.response,
      confidence: bestMatch.confidence,
    };
  }

  bulkAnswer(questions: string[]): SecurityQuestion[] {
    return questions.map((q) => this.answerQuestion(q));
  }

  getCompletionRate(questions: SecurityQuestion[]): { total: number; autoAnswered: number; manualReview: number; rate: number } {
    const autoAnswered = questions.filter((q) => q.autoAnswered).length;
    return {
      total: questions.length,
      autoAnswered,
      manualReview: questions.length - autoAnswered,
      rate: Math.round((autoAnswered / questions.length) * 100),
    };
  }
}
