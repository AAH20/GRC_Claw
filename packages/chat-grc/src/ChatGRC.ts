import { classifyIntent, normalizeFrameworkName } from './intents/classifier.js';
import { generateResponse } from './intents/responder.js';
import type {
  ChatMessage,
  ChatContext,
  ChatResponse,
  ChatSession,
  IntentType,
} from './types.js';
import { createEventUuid } from '@grc-claw/core';

function createSessionId(): string {
  return `chat-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}

export class ChatGRC {
  private sessions = new Map<string, ChatSession>();
  private defaultContext: ChatContext = {
    frameworks: [],
    controls: [],
    evidence: [],
    risks: [],
  };

  createSession(initialContext?: Partial<ChatContext>): ChatSession {
    const id = createSessionId();
    const now = new Date().toISOString();
    const session: ChatSession = {
      id,
      messages: [],
      context: { ...this.defaultContext, ...initialContext },
      createdAt: now,
      updatedAt: now,
    };
    this.sessions.set(id, session);
    return session;
  }

  getSession(sessionId: string): ChatSession | undefined {
    return this.sessions.get(sessionId);
  }

  async processMessage(
    message: string,
    context: ChatContext,
    sessionId?: string,
  ): Promise<ChatResponse & { sessionId: string; intent: IntentType }> {
    const session = sessionId
      ? this.sessions.get(sessionId)
      : this.createSession(context);

    if (!session && sessionId) {
      return {
        sessionId: sessionId,
        intent: 'help',
        message: 'Session not found. Please start a new conversation.',
        suggestions: ['help'],
      };
    }

    const activeSession = session ?? this.createSession(context);

    const userMessage: ChatMessage = {
      role: 'user',
      content: message,
      timestamp: new Date().toISOString(),
    };
    activeSession.messages.push(userMessage);

    const intentMatch = classifyIntent(message);

    const mergedContext = {
      ...activeSession.context,
      ...context,
    };

    const response = generateResponse(
      intentMatch.intent,
      intentMatch.entities,
      mergedContext,
    );

    this.updateContextFromEntities(activeSession.context, intentMatch.entities);

    const assistantMessage: ChatMessage = {
      role: 'assistant',
      content: response.message,
      timestamp: new Date().toISOString(),
    };
    activeSession.messages.push(assistantMessage);
    activeSession.updatedAt = new Date().toISOString();

    return {
      ...response,
      sessionId: activeSession.id,
      intent: intentMatch.intent,
    };
  }

  getHistory(sessionId: string): ChatMessage[] {
    return this.sessions.get(sessionId)?.messages ?? [];
  }

  clearSession(sessionId: string): boolean {
    return this.sessions.delete(sessionId);
  }

  listSessions(): ChatSession[] {
    return [...this.sessions.values()];
  }

  private updateContextFromEntities(
    context: ChatContext,
    entities: Record<string, string>,
  ): void {
    if (entities.framework) {
      const normalized = normalizeFrameworkName(entities.framework);
      if (!context.frameworks.includes(normalized)) {
        context.frameworks.push(normalized);
      }
    }
  }
}

export type {
  ChatMessage,
  ChatContext,
  ChatResponse,
  ChatSession,
  IntentType,
  CompliancePosture,
  ReportData,
  ReportSection,
  IntentMatch,
  MessageRole,
} from './types.js';
