import { ExecPolicy, AgentSession, BUILTIN_AGENT_TOOLS, HermesProvider, AgentOrchestrator } from '../src/index.js';

// A mock provider that simulates an LLM response without making a real network call
class MockHermesProvider extends HermesProvider {
  constructor() {
    super({ baseUrl: 'mock', apiKey: 'mock', model: 'mock' });
  }

  async generate(messages: any[], availableTools: any[]): Promise<any> {
    const lastMessage = messages[messages.length - 1];

    if (lastMessage.role === 'user') {
      console.log('🤖 Agent thought: I need to quarantine this device.');
      return {
        role: 'assistant',
        tool_calls: [{
          id: 'call_123',
          type: 'function',
          function: {
            name: 'chronicle__soar__run_playbook',
            arguments: JSON.stringify({ payload: '{"playbook": "quarantine"}' })
          }
        }]
      };
    }

    if (lastMessage.role === 'tool' && lastMessage.content.includes('DENIED')) {
      console.log('🤖 Agent thought: My action was denied. I need to ask for an approval token or report back.');
      return {
        role: 'assistant',
        content: 'I cannot run the quarantine playbook because it requires explicit approval. Please provide an approval token.'
      };
    }

    return { role: 'assistant', content: 'Task completed.' };
  }
}

async function runTest() {
  console.log('--- Starting GRC_Claw Agent Loop Test ---');
  
  const policy = new ExecPolicy(BUILTIN_AGENT_TOOLS);
  const session = new AgentSession('test-session-001', policy);
  const provider = new MockHermesProvider();
  
  const orchestrator = new AgentOrchestrator(
    provider,
    session,
    BUILTIN_AGENT_TOOLS,
    'You are a strict SOC analyst agent.'
  );

  console.log('User: "Please quarantine the compromised device."');
  
  try {
    const finalResponse = await orchestrator.executeTask('Please quarantine the compromised device.');
    console.log(`\nFinal Output: ${finalResponse}`);
    
    console.log('\n--- Audit Log ---');
    console.dir(session.getAuditLog(), { depth: null });
  } catch (err) {
    console.error(err);
  }
}

runTest().catch(console.error);
