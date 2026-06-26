export { ChatGRC } from './ChatGRC.js';
export { classifyIntent, normalizeFrameworkName } from './intents/classifier.js';
export { generateResponse } from './intents/responder.js';
export type {
  ChatMessage,
  ChatContext,
  ChatResponse,
  ChatSession,
  IntentType,
  IntentMatch,
  MessageRole,
  CompliancePosture,
  ReportData,
  ReportSection,
} from './types.js';
