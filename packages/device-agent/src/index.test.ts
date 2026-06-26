import { describe, it, beforeEach } from 'node:test';
import assert from 'node:assert/strict';
import { DeviceComplianceAgent } from './DeviceComplianceAgent.js';
import type { SystemAdapter, AgentConfig } from './types.js';
import { COMPLIANCE_RULES, getRuleById, getRulesByFramework } from './rules/index.js';

function createMockAdapter(responses: Record<string, string> = {}): SystemAdapter {
  const defaultResponses: Record<string, string> = {
    'fdesetup status': 'FileVault is On.',
    '/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate': 'Firewall global state is enabled.',
    'launchctl list': 'com.apple.XProtect\ncom.crowdstrike.falcond',
    'sw_vers -productVersion': '14.5',
    'sw_vers -buildVersion': '23F79',
    'defaults read com.apple.screensaver askForPassword': '1',
    'defaults -currentHost read com.apple.screensaver idleTime': '120',
    'ls /Applications/': '1Password.app\nSlack.app',
    'defaults read /Library/Preferences/com.apple.loginwindow': '',
    'sysadminctl -smartcard status': 'Smart card status: Online',
    'ufw status': 'Status: active',
    'netsh advfirewall show allprofiles': 'State ON',
    'cat /etc/os-release': 'PRETTY_NAME="Ubuntu 22.04"',
    'gsettings get org.gnome.desktop.screensaver lock-enabled': 'true',
    'gsettings get org.gnome.desktop.session idle-delay': '120',
  };

  const merged = { ...defaultResponses, ...responses };

  return {
    exec: async (cmd: string) => {
      for (const [key, value] of Object.entries(merged)) {
        if (cmd.includes(key)) return value;
      }
      return '';
    },
    readFile: async () => '',
    platform: () => 'darwin',
    hostname: () => 'test-device-001',
  };
}

describe('COMPLIANCE_RULES', () => {
  it('should have 10 rules defined', () => {
    assert.equal(COMPLIANCE_RULES.length, 10);
  });

  it('each rule should have required fields', () => {
    for (const rule of COMPLIANCE_RULES) {
      assert.ok(rule.id, `Rule missing id`);
      assert.ok(rule.name, `Rule ${rule.id} missing name`);
      assert.ok(rule.category, `Rule ${rule.id} missing category`);
      assert.ok(rule.checkFunction, `Rule ${rule.id} missing checkFunction`);
      assert.ok(rule.frameworks.length > 0, `Rule ${rule.id} missing frameworks`);
      assert.ok(['critical', 'high', 'medium', 'low'].includes(rule.severity), `Rule ${rule.id} invalid severity`);
      assert.ok(rule.controlId && typeof rule.controlId === 'object', `Rule ${rule.id} missing controlId`);
    }
  });

  it('getRuleById returns correct rule', () => {
    const rule = getRuleById('mfa_enabled');
    assert.ok(rule);
    assert.equal(rule.name, 'Multi-Factor Authentication Enabled');
  });

  it('getRulesByFramework filters correctly', () => {
    const soc2Rules = getRulesByFramework('SOC2');
    assert.ok(soc2Rules.length > 0);
    for (const rule of soc2Rules) {
      assert.ok(rule.frameworks.includes('SOC2'));
    }
  });
});

describe('DeviceComplianceAgent', () => {
  let agent: DeviceComplianceAgent;
  let adapter: SystemAdapter;

  beforeEach(() => {
    adapter = createMockAdapter();
    const config: AgentConfig = {
      deviceId: 'device-001',
      checksToRun: [],
    };
    agent = new DeviceComplianceAgent(config, adapter);
  });

  it('collectEvidence returns evidence with all checks', async () => {
    const evidence = await agent.collectEvidence();
    assert.equal(evidence.deviceId, 'device-001');
    assert.equal(evidence.hostname, 'test-device-001');
    assert.equal(evidence.os, 'darwin');
    assert.ok(evidence.checks.length > 0);
    assert.ok(typeof evidence.overallScore === 'number');
    assert.ok(evidence.collectedAt);
  });

  it('checkMFAStatus detects smart card on macOS', async () => {
    const check = await agent.checkMFAStatus();
    assert.equal(check.id, 'mfa_enabled');
    assert.equal(check.status, 'pass');
    assert.ok(check.details.includes('smart card'));
  });

  it('checkMFAStatus fails when no MFA detected', async () => {
    adapter = createMockAdapter({
      'sysadminctl -smartcard status': 'Smart card status: Not Online',
    });
    const config: AgentConfig = { deviceId: 'device-001', checksToRun: [] };
    const a = new DeviceComplianceAgent(config, adapter);
    const check = await a.checkMFAStatus();
    assert.equal(check.status, 'fail');
  });

  it('checkEncryptionStatus detects FileVault on macOS', async () => {
    const check = await agent.checkEncryptionStatus();
    assert.equal(check.id, 'disk_encryption');
    assert.equal(check.status, 'pass');
    assert.ok(check.details.includes('FileVault'));
  });

  it('checkEncryptionStatus fails when FileVault off', async () => {
    adapter = createMockAdapter({ 'fdesetup status': 'FileVault is Off.' });
    const config: AgentConfig = { deviceId: 'device-001', checksToRun: [] };
    const a = new DeviceComplianceAgent(config, adapter);
    const check = await a.checkEncryptionStatus();
    assert.equal(check.status, 'fail');
  });

  it('checkFirewallStatus detects enabled firewall on macOS', async () => {
    const check = await agent.checkFirewallStatus();
    assert.equal(check.id, 'firewall_enabled');
    assert.equal(check.status, 'pass');
  });

  it('checkFirewallStatus fails when firewall disabled', async () => {
    adapter = createMockAdapter({
      '/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate': 'Firewall global state is disabled.',
    });
    const config: AgentConfig = { deviceId: 'device-001', checksToRun: [] };
    const a = new DeviceComplianceAgent(config, adapter);
    const check = await a.checkFirewallStatus();
    assert.equal(check.status, 'fail');
  });

  it('checkAntivirusStatus detects endpoint protection', async () => {
    const check = await agent.checkAntivirusStatus();
    assert.equal(check.id, 'antivirus_running');
    assert.equal(check.status, 'pass');
  });

  it('checkOSVersion reports macOS version', async () => {
    const check = await agent.checkOSVersion();
    assert.equal(check.id, 'os_up_to_date');
    assert.equal(check.status, 'pass');
    assert.ok(check.details.includes('14.5'));
  });

  it('checkOSVersion warns on old macOS', async () => {
    adapter = createMockAdapter({ 'sw_vers -productVersion': '12.6' });
    const config: AgentConfig = { deviceId: 'device-001', checksToRun: [] };
    const a = new DeviceComplianceAgent(config, adapter);
    const check = await a.checkOSVersion();
    assert.equal(check.status, 'warning');
    assert.ok(check.details.includes('below Ventura'));
  });

  it('checkPasswordManager detects 1Password', async () => {
    const check = await agent.checkPasswordManager();
    assert.equal(check.id, 'password_manager');
    assert.equal(check.status, 'pass');
    assert.ok(check.details.includes('1Password'));
  });

  it('checkScreenLock detects enabled lock', async () => {
    const check = await agent.checkScreenLock();
    assert.equal(check.id, 'screen_lock');
    assert.equal(check.status, 'pass');
  });

  it('checkAutoLock detects 120s timeout', async () => {
    const check = await agent.checkAutoLock();
    assert.equal(check.id, 'auto_lock');
    assert.equal(check.status, 'pass');
    assert.ok(check.details.includes('120'));
  });

  it('checkAutoLock warns on long timeout', async () => {
    adapter = createMockAdapter({ 'defaults -currentHost read com.apple.screensaver idleTime': '600' });
    const config: AgentConfig = { deviceId: 'device-001', checksToRun: [] };
    const a = new DeviceComplianceAgent(config, adapter);
    const check = await a.checkAutoLock();
    assert.equal(check.status, 'warning');
  });

  it('generateReport produces valid report', async () => {
    const evidence = await agent.collectEvidence();
    const report = agent.generateReport(evidence);
    assert.equal(report.deviceId, 'device-001');
    assert.equal(report.hostname, 'test-device-001');
    assert.ok(report.overallScore >= 0 && report.overallScore <= 100);
    assert.ok(typeof report.frameworkScores === 'object');
    assert.ok(report.frameworkScores['SOC2'] !== undefined);
    assert.ok(Array.isArray(report.failedChecks));
  });

  it('collectEvidence handles check execution errors gracefully', async () => {
    const errorAdapter: SystemAdapter = {
      exec: async () => { throw new Error('command not found'); },
      readFile: async () => '',
      platform: () => 'darwin',
      hostname: () => 'error-device',
    };
    const config: AgentConfig = { deviceId: 'err-001', checksToRun: ['mfa_enabled'] };
    const a = new DeviceComplianceAgent(config, errorAdapter);
    const evidence = await a.collectEvidence();
    assert.equal(evidence.checks.length, 1);
    assert.equal(evidence.checks[0].status, 'unknown');
    assert.ok(evidence.checks[0].details.includes('could not be completed'));
  });

  it('collectEvidence runs only configured checks when checksToRun is set', async () => {
    const config: AgentConfig = {
      deviceId: 'device-002',
      checksToRun: ['mfa_enabled', 'disk_encryption'],
    };
    const a = new DeviceComplianceAgent(config, adapter);
    const evidence = await a.collectEvidence();
    assert.equal(evidence.checks.length, 2);
    const ids = evidence.checks.map((c) => c.id);
    assert.ok(ids.includes('mfa_enabled'));
    assert.ok(ids.includes('disk_encryption'));
  });

  it('Linux adapter uses ufw for firewall check', async () => {
    const linuxAdapter: SystemAdapter = {
      exec: async (cmd: string) => {
        if (cmd.includes('ufw status')) return 'Status: active';
        return '';
      },
      readFile: async () => '',
      platform: () => 'linux',
      hostname: () => 'linux-host',
    };
    const config: AgentConfig = { deviceId: 'linux-001', checksToRun: ['firewall_enabled'] };
    const a = new DeviceComplianceAgent(config, linuxAdapter);
    const check = await a.checkFirewallStatus();
    assert.equal(check.status, 'pass');
    assert.ok(check.details.includes('UFW'));
  });
});
