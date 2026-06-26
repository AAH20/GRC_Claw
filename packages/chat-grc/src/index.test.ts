import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import { ChatGRC } from './ChatGRC.js';
import { classifyIntent, normalizeFrameworkName } from './intents/classifier.js';
import { generateResponse } from './intents/responder.js';
import type { ChatContext } from './types.js';

const defaultContext: ChatContext = {
  frameworks: ['soc2', 'iso27001'],
  controls: [],
  evidence: [],
  risks: [],
};

describe('classifyIntent', () => {
  it('classifies control query with framework entity', () => {
    const result = classifyIntent('Show me all controls for SOC 2');
    assert.equal(result.intent, 'query_controls');
    assert.ok(result.confidence >= 0.8);
    assert.ok(result.entities.framework);
  });

  it('classifies evidence query', () => {
    const result = classifyIntent('What evidence is missing for ISO 27001?');
    assert.equal(result.intent, 'query_evidence');
    assert.ok(result.entities.framework);
  });

  it('classifies risk query', () => {
    const result = classifyIntent('What are our top risks?');
    assert.equal(result.intent, 'query_risks');
  });

  it('classifies posture query', () => {
    const result = classifyIntent('Show me our compliance posture');
    assert.equal(result.intent, 'query_posture');
  });

  it('classifies framework list query', () => {
    const result = classifyIntent('Which frameworks are supported?');
    assert.equal(result.intent, 'query_frameworks');
  });

  it('classifies report generation', () => {
    const result = classifyIntent('Generate a board report');
    assert.equal(result.intent, 'generate_report');
  });

  it('classifies compliance scan', () => {
    const result = classifyIntent('Run a compliance scan');
    assert.equal(result.intent, 'check_compliance');
  });

  it('classifies help', () => {
    const result = classifyIntent('help');
    assert.equal(result.intent, 'help');
  });

  it('falls back to keyword matching for unclear inputs', () => {
    const result = classifyIntent('tell me about our policies');
    assert.equal(result.intent, 'query_controls');
    assert.ok(result.confidence > 0);
  });
});

describe('normalizeFrameworkName', () => {
  it('normalizes SOC 2 variations', () => {
    assert.equal(normalizeFrameworkName('SOC 2'), 'soc2');
    assert.equal(normalizeFrameworkName('soc2'), 'soc2');
    assert.equal(normalizeFrameworkName('SOC 2.0'), 'soc2');
  });

  it('normalizes ISO 27001 variations', () => {
    assert.equal(normalizeFrameworkName('ISO 27001'), 'iso27001');
    assert.equal(normalizeFrameworkName('iso27001'), 'iso27001');
    assert.equal(normalizeFrameworkName('ISO/IEC 27001'), 'iso27001');
  });

  it('normalizes NIST CSF', () => {
    assert.equal(normalizeFrameworkName('NIST CSF'), 'nist_csf');
    assert.equal(normalizeFrameworkName('nist_csf'), 'nist_csf');
  });

  it('passes through unknown frameworks', () => {
    assert.equal(normalizeFrameworkName('custom_framework'), 'custom_framework');
  });
});

describe('generateResponse', () => {
  it('returns controls list for query_controls', () => {
    const response = generateResponse('query_controls', { framework: 'soc2' }, defaultContext);
    assert.ok(response.message.includes('SOC2') || response.message.includes('SOC 2'));
    assert.ok(response.data);
    assert.ok(response.suggestions);
  });

  it('prompts for framework when none specified', () => {
    const response = generateResponse('query_controls', {}, { ...defaultContext, frameworks: [] });
    assert.ok(response.message.includes('Which framework'));
  });

  it('returns evidence coverage for query_evidence', () => {
    const response = generateResponse('query_evidence', { framework: 'iso27001' }, defaultContext);
    assert.ok(response.message.includes('Evidence Coverage'));
    assert.ok(response.message.includes('ISO27001'));
  });

  it('returns risk data for query_risks', () => {
    const response = generateResponse('query_risks', {}, defaultContext);
    assert.ok(response.message.includes('Top Risks'));
    assert.ok(response.data);
  });

  it('returns posture overview for query_posture', () => {
    const response = generateResponse('query_posture', {}, defaultContext);
    assert.ok(response.message.includes('Compliance Posture'));
  });

  it('returns framework list for query_frameworks', () => {
    const response = generateResponse('query_frameworks', {}, defaultContext);
    assert.ok(response.message.includes('Supported Frameworks'));
  });

  it('returns report data for generate_report', () => {
    const response = generateResponse('generate_report', { reportType: 'board' }, defaultContext);
    assert.ok(response.message.includes('Board Report'));
    assert.ok(response.data);
  });

  it('returns scan results for check_compliance', () => {
    const response = generateResponse('check_compliance', { framework: 'soc2' }, defaultContext);
    assert.ok(response.message.includes('Compliance Scan'));
  });

  it('returns help text for help', () => {
    const response = generateResponse('help', {}, defaultContext);
    assert.ok(response.message.includes('Available Commands'));
  });

  it('includes suggestions in responses', () => {
    const response = generateResponse('query_controls', { framework: 'soc2' }, defaultContext);
    assert.ok(Array.isArray(response.suggestions));
    assert.ok(response.suggestions!.length > 0);
  });
});

describe('ChatGRC', () => {
  it('creates a session', () => {
    const chat = new ChatGRC();
    const session = chat.createSession({ frameworks: ['soc2'] });
    assert.ok(session.id.startsWith('chat-'));
    assert.deepEqual(session.context.frameworks, ['soc2']);
    assert.equal(session.messages.length, 0);
  });

  it('retrieves a session', () => {
    const chat = new ChatGRC();
    const session = chat.createSession();
    const retrieved = chat.getSession(session.id);
    assert.equal(retrieved?.id, session.id);
  });

  it('returns undefined for unknown session', () => {
    const chat = new ChatGRC();
    assert.equal(chat.getSession('nonexistent'), undefined);
  });

  it('processes a message and returns response with intent', async () => {
    const chat = new ChatGRC();
    const response = await chat.processMessage('help', defaultContext);
    assert.equal(response.intent, 'help');
    assert.ok(response.message.includes('Available Commands'));
    assert.ok(response.sessionId);
  });

  it('adds user and assistant messages to session history', async () => {
    const chat = new ChatGRC();
    const result = await chat.processMessage('help', defaultContext);
    const history = chat.getHistory(result.sessionId);
    assert.equal(history.length, 2);
    assert.equal(history[0].role, 'user');
    assert.equal(history[1].role, 'assistant');
  });

  it('tracks frameworks in context from entity extraction', async () => {
    const chat = new ChatGRC();
    const ctx: ChatContext = { frameworks: [], controls: [], evidence: [], risks: [] };
    await chat.processMessage('Show me all controls for SOC 2', ctx);
    const session = chat.listSessions()[0];
    assert.ok(session.context.frameworks.includes('soc2'));
  });

  it('clears a session', async () => {
    const chat = new ChatGRC();
    const result = await chat.processMessage('help', defaultContext);
    assert.ok(chat.clearSession(result.sessionId));
    assert.equal(chat.getSession(result.sessionId), undefined);
  });

  it('lists all sessions', async () => {
    const chat = new ChatGRC();
    await chat.processMessage('help', defaultContext);
    await chat.processMessage('help', defaultContext);
    assert.equal(chat.listSessions().length, 2);
  });

  it('processes control query end-to-end', async () => {
    const chat = new ChatGRC();
    const response = await chat.processMessage(
      'Show me all controls for SOC 2',
      defaultContext,
    );
    assert.equal(response.intent, 'query_controls');
    assert.ok(response.message.includes('CC6.1'));
    assert.ok(response.data);
  });

  it('processes risk query end-to-end', async () => {
    const chat = new ChatGRC();
    const response = await chat.processMessage('What are our top risks?', defaultContext);
    assert.equal(response.intent, 'query_risks');
    assert.ok(response.message.includes('Ransomware'));
  });

  it('processes framework list end-to-end', async () => {
    const chat = new ChatGRC();
    const response = await chat.processMessage('List all frameworks', defaultContext);
    assert.equal(response.intent, 'query_frameworks');
    assert.ok(response.message.includes('iso27001'));
  });
});
