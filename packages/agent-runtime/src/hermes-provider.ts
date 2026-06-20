import { ToolDefinition } from './index.js';

export interface Message {
  role: 'system' | 'user' | 'assistant' | 'tool';
  content?: string | null;
  name?: string;
  tool_calls?: ToolCall[];
  tool_call_id?: string;
}

export interface ToolCall {
  id: string;
  type: 'function';
  function: {
    name: string;
    arguments: string;
  };
}

export interface HermesProviderConfig {
  baseUrl: string;
  apiKey: string;
  model: string;
}

/**
 * A lightweight, zero-dependency provider for OpenAI-compatible endpoints
 * (e.g. vLLM, OpenRouter, or local Nemotron/Hermes serving).
 */
export class HermesProvider {
  constructor(private readonly config: HermesProviderConfig) {}

  /**
   * Translates GRC_Claw tool definitions into OpenAI-compatible JSON Schema.
   */
  private formatTools(tools: ToolDefinition[]): any[] {
    return tools.map((tool) => ({
      type: 'function',
      function: {
        name: tool.name.replace(/\./g, '__'), // Encode dots as double underscores
        description: `Execute the ${tool.name} tool. Tier: ${tool.tier}.`,
        parameters: {
          type: 'object',
          properties: {
            payload: {
              type: 'string',
              description: 'JSON string of arguments for the tool'
            }
          },
          required: []
        }
      }
    }));
  }

  /**
   * Calls the LLM and returns the assistant's message.
   */
  async generate(messages: Message[], availableTools: ToolDefinition[]): Promise<Message> {
    const url = `${this.config.baseUrl.replace(/\/+$/, '')}/chat/completions`;
    
    const body = {
      model: this.config.model,
      messages,
      tools: this.formatTools(availableTools),
      tool_choice: 'auto',
      temperature: 0.1, // Low temp for reliable function calling
    };

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.config.apiKey}`
      },
      body: JSON.stringify(body)
    });

    if (!response.ok) {
      const errText = await response.text();
      throw new Error(`HermesProvider error (${response.status}): ${errText}`);
    }

    const data = await response.json();
    return data.choices[0].message;
  }
}
