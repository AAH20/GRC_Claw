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
