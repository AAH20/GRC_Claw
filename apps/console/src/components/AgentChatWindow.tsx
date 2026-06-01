import { useRef, useEffect, useState, type KeyboardEvent } from 'react';
import { api, ApiError } from '../lib/api';
import { GEMINI_SYSTEM_PROMPT, CURSOR_AUTO_SYSTEM_PROMPT } from '../lib/chatPrompts';
import { runOperatorTools, formatToolResultsForPrompt } from '../lib/operatorAgent';
import { wantsJobCatalog, formatSchedulableJobsCatalog } from '../lib/schedulableJobs';
import { wantsSkillsQuery, formatSkillsCatalog } from '../lib/skillsCatalog';

export type ChatMode = 'gemini' | 'cursor-auto';

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  mode: ChatMode;
  meta?: string;
}

interface AgentChatWindowProps {
  llmProviderId?: string;
  llmAvailable?: boolean;
}

const CHAT_MAX_TOKENS = 8192;

function uid(): string {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

export function AgentChatWindow({
  llmProviderId = 'gemini',
  llmAvailable = true,
}: AgentChatWindowProps) {
  const [mode, setMode] = useState<ChatMode>('gemini');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, sending]);

  async function completeChat(
    systemPrompt: string,
    history: ChatMessage[],
    userText: string,
    toolContext: string
  ): Promise<string> {
    const payload = [
      { role: 'system', content: systemPrompt + toolContext },
      ...history.map((m) => ({ role: m.role, content: m.content })),
      { role: 'user' as const, content: userText },
    ];

    const res = await api.llmChat(llmProviderId, {
      messages: payload,
      maxTokens: CHAT_MAX_TOKENS,
      temperature: mode === 'gemini' ? 0.5 : 0.4,
    });

    const text = String(res.content ?? '').trim();
    if (!text) throw new Error('Model returned empty content — try again or check gateway logs.');
    return text;
  }

  /** Catalog answers — no Gemini call (avoids 503 when listing skills/jobs). */
  async function tryLocalReply(
    userText: string,
    chatMode: ChatMode
  ): Promise<{ content: string; meta: string } | null> {
    if (wantsSkillsQuery(userText)) {
      return {
        content: await formatSkillsCatalog(),
        meta: 'From skills catalog (no LLM)',
      };
    }
    if (wantsJobCatalog(userText)) {
      let out = formatSchedulableJobsCatalog();
      if (chatMode === 'cursor-auto') {
        const toolResults = await runOperatorTools(userText);
        const health = toolResults.find((r) => r.tool === 'GET /health');
        if (health) out += `\n---\n**Live gateway:** ${health.summary}\n`;
      }
      return { content: out, meta: 'From schedulable jobs catalog (no LLM)' };
    }
    return null;
  }

  async function sendGemini(history: ChatMessage[], userText: string) {
    const local = await tryLocalReply(userText, 'gemini');
    if (local) return local;
    const text = await completeChat(GEMINI_SYSTEM_PROMPT, history, userText, '');
    return { content: text, meta: '' };
  }

  async function sendCursorAuto(history: ChatMessage[], userText: string) {
    const local = await tryLocalReply(userText, 'cursor-auto');
    if (local) return local;

    const toolResults = await runOperatorTools(userText);
    const toolContext = formatToolResultsForPrompt(toolResults);
    const antiHallucination =
      '\n\nNEVER invent tools like claw.list_skills(). Use only gateway APIs and the skills catalog when listing skills.\n';
    const text = await completeChat(
      CURSOR_AUTO_SYSTEM_PROMPT,
      history,
      userText,
      toolContext + antiHallucination
    );
    return { content: text, meta: 'Gateway tools may have been invoked' };
  }

  function friendlyLlmError(e: unknown): string {
    const raw =
      e instanceof ApiError
        ? `${e.message}: ${typeof e.body === 'string' ? e.body : JSON.stringify(e.body)}`
        : e instanceof Error
          ? e.message
          : 'Send failed';
    if (/503|UNAVAILABLE|high demand/i.test(raw)) {
      return (
        'Gemini is temporarily overloaded (503). Try again in a minute, switch to **Cursor Auto** for gateway-only tasks, or use "List skills" / "List jobs" which do not call Gemini.'
      );
    }
    return raw;
  }

  async function handleSend() {
    const text = input.trim();
    if (!text || sending) return;

    const needsLlm = !wantsSkillsQuery(text) && !wantsJobCatalog(text);
    if (needsLlm && !llmAvailable) {
      setError('No LLM provider configured on gateway — set GEMINI_API_KEY and reload connectors.');
      return;
    }

    setInput('');
    setError(null);
    setSending(true);

    const userMsg: ChatMessage = { id: uid(), role: 'user', content: text, mode };
    setMessages((prev) => [...prev, userMsg]);

    try {
      const history = messages.filter((m) => m.mode === mode);
      const result =
        mode === 'gemini' ? await sendGemini(history, text) : await sendCursorAuto(history, text);

      setMessages((prev) => [
        ...prev,
        {
          id: uid(),
          role: 'assistant',
          content: result.content,
          mode,
          meta: result.meta || undefined,
        },
      ]);
    } catch (e) {
      setError(friendlyLlmError(e));
    } finally {
      setSending(false);
    }
  }

  function onKeyDown(e: KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      void handleSend();
    }
  }

  const visible = messages.filter((m) => m.mode === mode);

  return (
    <div className="card chat-window" data-agent-chat="true">
      <div className="chat-header">
        <div>
          <h2>Agent chat</h2>
          <p className="explain-lead">
            {mode === 'gemini'
              ? 'Direct Gemini — full replies with GRC/A2Z context (up to 8k output tokens).'
              : 'Cursor Auto — runs gateway tools when relevant, then answers. Cannot start OS daemons or Cursor IDE agents from the browser.'}
          </p>
        </div>
        <div className="chat-mode-switch" role="tablist" aria-label="Chat mode">
          <button
            type="button"
            role="tab"
            aria-selected={mode === 'cursor-auto'}
            className={mode === 'cursor-auto' ? 'active' : ''}
            onClick={() => setMode('cursor-auto')}
          >
            Cursor Auto
          </button>
          <button
            type="button"
            role="tab"
            aria-selected={mode === 'gemini'}
            className={mode === 'gemini' ? 'active' : ''}
            onClick={() => setMode('gemini')}
          >
            Gemini
          </button>
        </div>
      </div>

      {mode === 'cursor-auto' && (
        <div className="chat-notice">
          <strong>Scope:</strong> This mode calls the GRC_Claw gateway (health, sync, frameworks, read
          tools). For background agents, cron, or daemons use{' '}
          <strong>Cursor Automations</strong> (desktop) or host cron → gateway API.
        </div>
      )}

      {!llmAvailable && (
        <p className="error">
          LLM provider &quot;{llmProviderId}&quot; not loaded — configure gateway env and restart.
        </p>
      )}

      <div className="chat-messages" ref={scrollRef}>
        {visible.length === 0 && (
          <div className="chat-empty">
            <p>
              {mode === 'gemini'
                ? 'Ask for multi-step GRC guidance, framework mapping, or alert triage.'
                : 'Try: “What is our gateway status?” or “How do I schedule A2Z sync hourly?”'}
            </p>
          </div>
        )}
        {visible.map((m) => (
          <div key={m.id} className={`chat-bubble ${m.role}`}>
            <div className="chat-bubble-label">
              {m.role === 'user' ? 'You' : mode === 'gemini' ? 'Gemini' : 'Cursor Auto'}
            </div>
            <div className="chat-bubble-body">{m.content}</div>
            {m.meta && <div className="chat-bubble-meta">{m.meta}</div>}
          </div>
        ))}
        {sending && (
          <div className="chat-bubble assistant">
            <div className="chat-bubble-label">{mode === 'gemini' ? 'Gemini' : 'Cursor Auto'}</div>
            <div className="chat-bubble-body chat-typing">
              {wantsSkillsQuery(input) || wantsJobCatalog(input)
                ? 'Loading catalog…'
                : mode === 'cursor-auto'
                  ? 'Running gateway tools & composing reply…'
                  : 'Thinking…'}
            </div>
          </div>
        )}
      </div>

      {error && <p className="error chat-error">{error}</p>}

      <div className="chat-input-row">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={onKeyDown}
          placeholder={
            mode === 'gemini'
              ? 'Message Gemini… (Enter to send, Shift+Enter for newline)'
              : 'Ask about gateway, A2Z SOC, skills, or automation setup…'
          }
          rows={3}
          disabled={sending}
        />
        <button
          type="button"
          className="primary chat-send"
          onClick={() => void handleSend()}
          disabled={sending || !input.trim()}
        >
          {sending ? '…' : 'Send'}
        </button>
      </div>
    </div>
  );
}
