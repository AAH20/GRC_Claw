import { AgentSession, ToolDefinition, ToolInvocation } from './index.js';
import { HermesProvider, Message } from './hermes-provider.js';

export interface OrchestratorOptions {
  maxSteps?: number;
  agentRole?: string; // Define the role under which this agent/swarm squad is running
  llmProviderId?: string; // Define the LLM provider used to route this turn
  onToolCall?: (invocation: ToolInvocation) => Promise<string | Record<string, unknown>>;
}

export class AgentOrchestrator {
  private readonly messages: Message[] = [];

  constructor(
    private readonly provider: HermesProvider,
    private readonly session: AgentSession,
    private readonly availableTools: ToolDefinition[],
    private readonly systemPrompt?: string
  ) {
    if (this.systemPrompt) {
      this.messages.push({ role: 'system', content: this.systemPrompt });
    }
  }

  /**
   * Translates the underscore-based tool name back to dot notation.
   */
  private parseToolName(name: string): string {
    return name.replace(/__/g, '.');
  }

  async executeTask(taskPrompt: string, options?: OrchestratorOptions): Promise<string> {
    const maxSteps = options?.maxSteps ?? 10;
    this.messages.push({ role: 'user', content: taskPrompt });

    for (let step = 0; step < maxSteps; step++) {
      const responseMessage = await this.provider.generate(this.messages, this.availableTools);
      this.messages.push(responseMessage);

      // If the model didn't call any tools, it means it returned a final response.
      if (!responseMessage.tool_calls || responseMessage.tool_calls.length === 0) {
        return responseMessage.content || '';
      }

      // Process tool calls
      for (const toolCall of responseMessage.tool_calls) {
        if (toolCall.type !== 'function') continue;

        const toolName = this.parseToolName(toolCall.function.name);
        
        let parsedArgs: Record<string, unknown>;
        try {
          parsedArgs = JSON.parse(toolCall.function.arguments);
          // If the model passed { payload: "{...}" }, try parsing it again
          if (typeof parsedArgs.payload === 'string') {
            try {
              parsedArgs = JSON.parse(parsedArgs.payload);
            } catch {
              // Ignore inner parse error
            }
          }
        } catch (e) {
          parsedArgs = { raw: toolCall.function.arguments };
        }

        const invocation: ToolInvocation = {
          tool: toolName,
          args: parsedArgs,
          agentRole: options?.agentRole, // Pass the role to enforce Segregation of Duties
          llmProviderId: options?.llmProviderId, // Pass the LLM provider ID for sovereign boundary checks
          thought: responseMessage.content || undefined, // Pass the thought content if available
        };

        // Pass invocation to the strict GRC_Claw ExecPolicy
        const decision = await this.session.invoke(invocation);

        let toolResultText = '';
        if (decision.allowed) {
          // If allowed, actually execute the tool
          if (options?.onToolCall) {
            try {
              const result = await options.onToolCall(invocation);
              toolResultText = typeof result === 'string' ? result : JSON.stringify(result);
            } catch (error: any) {
              toolResultText = `Error executing tool: ${error.message}`;
            }
          } else {
            toolResultText = `Tool ${toolName} executed successfully (mock response). Sandbox: ${decision.sandbox}`;
          }
        } else {
          // If denied, feed the exact reason back to the model so it learns
          toolResultText = `DENIED: ${decision.reason}. Sandbox: ${decision.sandbox}. Requires Approval: ${decision.requiresApproval}. Toxicity: ${decision.toxicityScore ?? 0}`;
        }

        // Send tool result back to model
        this.messages.push({
          role: 'tool',
          tool_call_id: toolCall.id,
          name: toolCall.function.name,
          content: toolResultText
        });
      }
    }

    throw new Error('AgentOrchestrator max steps exceeded');
  }

  getMessages(): Message[] {
    return this.messages;
  }
}

