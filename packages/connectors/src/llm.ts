import type { LlmProviderConfig } from './types.js';
import { ConnectorRegistry } from './registry.js';

export interface LlmChatRequest {
  messages: { role: string; content: string }[];
  model?: string;
  maxTokens?: number;
  temperature?: number;
}

export interface LlmChatResult {
  providerId: string;
  model: string;
  content: string;
  raw?: Record<string, unknown>;
}

export async function chatViaProvider(
  registry: ConnectorRegistry,
  providerId: string,
  req: LlmChatRequest
): Promise<LlmChatResult> {
  const provider = registry.getLlm(providerId);
  if (!provider) throw new Error(`llm_provider_not_found:${providerId}`);

  const apiKey = registry.resolveApiKey(provider.apiKeyEnv);
  if (!apiKey) throw new Error(`llm_api_key_missing:${provider.apiKeyEnv}`);

  const model = req.model ?? provider.defaultModel ?? 'gpt-4o-mini';

  if (provider.kind === 'anthropic_messages') {
    return anthropicChat(provider, apiKey, model, req);
  }
  if (provider.kind === 'gemini_generate') {
    return geminiChat(provider, apiKey, model, req);
  }
  return openAiCompatibleChat(provider, apiKey, model, req);
}

async function openAiCompatibleChat(
  provider: LlmProviderConfig,
  apiKey: string,
  model: string,
  req: LlmChatRequest
): Promise<LlmChatResult> {
  const base = provider.baseUrl.replace(/\/$/, '');
  const url = base.endsWith('/v1') ? `${base}/chat/completions` : `${base}/v1/chat/completions`;
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${apiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model,
      messages: req.messages,
      max_tokens: req.maxTokens ?? 1024,
      temperature: req.temperature ?? 0.2,
    }),
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => '');
    throw new Error(`llm_http_${res.status}:${detail.slice(0, 200)}`);
  }
  const body = (await res.json()) as {
    choices?: { message?: { content?: string } }[];
  };
  const content = body.choices?.[0]?.message?.content ?? '';
  return { providerId: provider.id, model, content, raw: body as Record<string, unknown> };
}

async function anthropicChat(
  provider: LlmProviderConfig,
  apiKey: string,
  model: string,
  req: LlmChatRequest
): Promise<LlmChatResult> {
  const base = provider.baseUrl.replace(/\/$/, '');
  const url = base.includes('/v1') ? `${base}/messages` : `${base}/v1/messages`;
  const system = req.messages.find((m) => m.role === 'system')?.content;
  const messages = req.messages.filter((m) => m.role !== 'system').map((m) => ({
    role: m.role === 'assistant' ? 'assistant' : 'user',
    content: m.content,
  }));

  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model,
      max_tokens: req.maxTokens ?? 1024,
      system,
      messages,
    }),
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => '');
    throw new Error(`llm_http_${res.status}:${detail.slice(0, 200)}`);
  }
  const body = (await res.json()) as {
    content?: { type: string; text?: string }[];
  };
  const content = body.content?.find((c) => c.type === 'text')?.text ?? '';
  return { providerId: provider.id, model, content, raw: body as Record<string, unknown> };
}

function extractGeminiText(body: {
  candidates?: {
    content?: { parts?: { text?: string }[] };
    finishReason?: string;
  }[];
  promptFeedback?: { blockReason?: string };
}): string {
  const candidate = body.candidates?.[0];
  if (!candidate?.content?.parts?.length) {
    const reason = body.promptFeedback?.blockReason ?? candidate?.finishReason ?? 'no_candidates';
    throw new Error(`gemini_empty_response:${reason}`);
  }
  const text = candidate.content.parts
    .map((p) => p.text ?? '')
    .join('')
    .trim();
  if (!text) {
    throw new Error(`gemini_empty_text:${candidate.finishReason ?? 'unknown'}`);
  }
  return text;
}

async function geminiChat(
  provider: LlmProviderConfig,
  apiKey: string,
  model: string,
  req: LlmChatRequest
): Promise<LlmChatResult> {
  const base =
    provider.baseUrl.replace(/\/$/, '') || 'https://generativelanguage.googleapis.com/v1beta';
  const url = `${base}/models/${model}:generateContent`;

  const systemMsg = req.messages.find((m) => m.role === 'system')?.content;
  const contents = req.messages
    .filter((m) => m.role !== 'system')
    .map((m) => ({
      role: m.role === 'assistant' ? 'model' : 'user',
      parts: [{ text: m.content }],
    }));

  const maxOutputTokens = req.maxTokens ?? 8192;
  const generationConfig: Record<string, unknown> = {
    maxOutputTokens,
    temperature: req.temperature ?? 0.4,
  };
  // Gemini 2.5 "thinking" can consume the entire token budget — leave room for visible reply
  if (/gemini-2\.5/i.test(model)) {
    generationConfig.thinkingConfig = { thinkingBudget: 1024 };
  }

  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-goog-api-key': apiKey,
    },
    body: JSON.stringify({
      ...(systemMsg
        ? { systemInstruction: { parts: [{ text: systemMsg }] } }
        : {}),
      contents,
      generationConfig,
    }),
  });
  if (!res.ok) {
    const detail = await res.text().catch(() => '');
    throw new Error(`llm_http_${res.status}:${detail.slice(0, 300)}`);
  }
  const body = (await res.json()) as {
    candidates?: {
      content?: { parts?: { text?: string }[] };
      finishReason?: string;
    }[];
    promptFeedback?: { blockReason?: string };
  };
  const content = extractGeminiText(body);
  return { providerId: provider.id, model, content, raw: body as Record<string, unknown> };
}
