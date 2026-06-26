import type {
  AgentConfig,
  ComplianceCheck,
  DeviceEvidence,
  DeviceReport,
  SystemAdapter,
} from './types.js';
import { COMPLIANCE_RULES, getRuleById } from './rules/index.js';

const REQUIRED_CHECKS = [
  'mfa_enabled',
  'disk_encryption',
  'firewall_enabled',
  'antivirus_running',
  'os_up_to_date',
  'password_manager',
  'screen_lock',
  'auto_lock',
] as const;

export class DeviceComplianceAgent {
  private config: AgentConfig;
  private system: SystemAdapter;

  constructor(config: AgentConfig, systemAdapter: SystemAdapter) {
    this.config = config;
    this.system = systemAdapter;
  }

  async collectEvidence(): Promise<DeviceEvidence> {
    const enabledChecks = this.config.checksToRun.length > 0
      ? this.config.checksToRun
      : REQUIRED_CHECKS.slice();

    const checks: ComplianceCheck[] = [];

    for (const checkId of enabledChecks) {
      const rule = getRuleById(checkId);
      if (!rule) continue;

      const methodName = rule.checkFunction;
      const method = (this as Record<string, unknown>)[methodName];
      if (typeof method !== 'function') continue;

      try {
        const result = await (method as () => Promise<ComplianceCheck>).call(this);
        checks.push({
          ...result,
          controlId: rule.controlId[rule.frameworks[0]] ?? result.controlId,
          framework: rule.frameworks.join(','),
        });
      } catch (err) {
        checks.push({
          id: checkId,
          name: rule.name,
          category: rule.category,
          status: 'unknown',
          severity: rule.severity,
          details: `Check execution failed: ${err instanceof Error ? err.message : String(err)}`,
        });
      }
    }

    const overallScore = this.calculateScore(checks);
    const hostname = this.system.hostname();

    return {
      deviceId: this.config.deviceId,
      hostname,
      os: this.system.platform(),
      osVersion: '',
      checks,
      overallScore,
      collectedAt: new Date().toISOString(),
    };
  }

  async checkMFAStatus(): Promise<ComplianceCheck> {
    const platform = this.system.platform();
    let status: ComplianceCheck['status'] = 'fail';
    let details = '';

    try {
      if (platform === 'darwin') {
        const result = await this.system.exec(
          'defaults read /Library/Preferences/com.apple.loginwindow 2>/dev/null || echo ""'
        );
        const dualAuth = result.includes('enforced') || result.includes('YES');
        const smsResult = await this.system.exec(
          'sysadminctl -smartcard status 2>&1 || echo ""'
        );
        const smartCard = smsResult.includes('enabled') || (smsResult.includes('Online') && !smsResult.includes('Not Online'));
        if (dualAuth || smartCard) {
          status = 'pass';
          details = 'MFA via smart card or managed policy detected';
        } else {
          details = 'No MFA method detected via smart card or login policy';
        }
      } else if (platform === 'linux') {
        const pamResult = await this.system.exec(
          'grep -r "pam_google_authenticator\\|pam_u2f\\|pam_duo" /etc/pam.d/ 2>/dev/null || echo ""'
        );
        if (pamResult.trim().length > 0) {
          status = 'pass';
          details = 'MFA PAM module configured';
        } else {
          details = 'No MFA PAM module found in /etc/pam.d/';
        }
      } else if (platform === 'win32') {
        const wResult = await this.system.exec(
          'powershell -Command "Get-MpPreference | Select-Object -ExpandProperty DisableRealtimeMonitoring" 2>nul || echo ""'
        );
        const helloResult = await this.system.exec(
          'reg query "HKLM\\SOFTWARE\\Microsoft\\Windows\\HelloFace" 2>nul || echo ""'
        );
        if (helloResult.includes('REG_DWORD')) {
          status = 'pass';
          details = 'Windows Hello configured for MFA';
        } else {
          details = 'Windows Hello MFA not detected';
        }
      } else {
        details = `Platform ${platform} not supported for MFA check`;
        status = 'unknown';
      }
    } catch {
      status = 'unknown';
      details = 'MFA check could not be completed';
    }

    return {
      id: 'mfa_enabled',
      name: 'Multi-Factor Authentication Enabled',
      category: 'Identity & Access Management',
      status,
      severity: 'critical',
      details,
    };
  }

  async checkEncryptionStatus(): Promise<ComplianceCheck> {
    const platform = this.system.platform();
    let status: ComplianceCheck['status'] = 'fail';
    let details = '';

    try {
      if (platform === 'darwin') {
        const result = await this.system.exec(
          'fdesetup status 2>/dev/null || echo ""'
        );
        if (result.includes('On') || result.includes('Encrypted')) {
          status = 'pass';
          details = 'FileVault full disk encryption is enabled';
        } else {
          details = 'FileVault is not enabled';
        }
      } else if (platform === 'linux') {
        const result = await this.system.exec(
          'lsblk -o NAME,FSTYPE 2>/dev/null | grep -i "crypto\\|LUKS" || echo ""'
        );
        if (result.trim().length > 0) {
          status = 'pass';
          details = 'LUKS encryption detected on block devices';
        } else {
          details = 'No LUKS encryption detected';
        }
      } else if (platform === 'win32') {
        const result = await this.system.exec(
          'manage-bde -status C: 2>nul || echo ""'
        );
        if (result.includes('Protection On') || result.includes('Conversion Status:    Fully Encrypted')) {
          status = 'pass';
          details = 'BitLocker encryption is enabled on C:';
        } else {
          details = 'BitLocker encryption not detected or not fully encrypted';
        }
      } else {
        details = `Platform ${platform} not supported for encryption check`;
        status = 'unknown';
      }
    } catch {
      details = 'Encryption check could not be completed';
    }

    return {
      id: 'disk_encryption',
      name: 'Full Disk Encryption',
      category: 'Data Protection',
      status,
      severity: 'critical',
      details,
    };
  }

  async checkFirewallStatus(): Promise<ComplianceCheck> {
    const platform = this.system.platform();
    let status: ComplianceCheck['status'] = 'fail';
    let details = '';

    try {
      if (platform === 'darwin') {
        const result = await this.system.exec(
          '/usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate 2>/dev/null || echo ""'
        );
        if (result.includes('enabled') || result.includes('ENABLED')) {
          status = 'pass';
          details = 'macOS application firewall is enabled';
        } else {
          details = 'macOS application firewall is disabled';
        }
      } else if (platform === 'linux') {
        const ufwResult = await this.system.exec('ufw status 2>/dev/null || echo ""');
        const nftResult = await this.system.exec('nft list ruleset 2>/dev/null | head -5 || echo ""');
        const iptResult = await this.system.exec('iptables -L -n 2>/dev/null | head -5 || echo ""');

        if (ufwResult.includes('active')) {
          status = 'pass';
          details = 'UFW firewall is active';
        } else if (nftResult.trim().length > 0) {
          status = 'pass';
          details = 'nftables rules are configured';
        } else if (iptResult.includes('ACCEPT') || iptResult.includes('DROP')) {
          status = 'pass';
          details = 'iptables rules are configured';
        } else {
          details = 'No active firewall detected (ufw, nftables, iptables)';
        }
      } else if (platform === 'win32') {
        const result = await this.system.exec(
          'netsh advfirewall show allprofiles 2>nul || echo ""'
        );
        if (result.includes('State ON')) {
          status = 'pass';
          details = 'Windows Defender Firewall is enabled for all profiles';
        } else if (result.includes('State')) {
          details = 'Windows Defender Firewall not enabled for all profiles';
        } else {
          details = 'Could not query Windows firewall status';
        }
      } else {
        details = `Platform ${platform} not supported for firewall check`;
        status = 'unknown';
      }
    } catch {
      details = 'Firewall check could not be completed';
    }

    return {
      id: 'firewall_enabled',
      name: 'Host Firewall Enabled',
      category: 'Network Security',
      status,
      severity: 'high',
      details,
    };
  }

  async checkAntivirusStatus(): Promise<ComplianceCheck> {
    const platform = this.system.platform();
    let status: ComplianceCheck['status'] = 'fail';
    let details = '';

    try {
      if (platform === 'darwin') {
        const result = await this.system.exec(
          'launchctl list 2>/dev/null | grep -i "endpoint\\|protect\\|defender\\|crowdstrike\\|sentinel\\|falcon" || echo ""'
        );
        if (result.trim().length > 0) {
          status = 'pass';
          details = `Endpoint protection service detected: ${result.trim().split('\n')[0]}`;
        } else {
          const xprotect = await this.system.exec(
            'ls /Library/Apple/System/Library/CoreServices/XProtect.app 2>/dev/null && echo present || echo ""'
          );
          if (xprotect.includes('present')) {
            status = 'pass';
            details = 'XProtect (built-in macOS AV) is available';
          } else {
            details = 'No endpoint protection detected';
          }
        }
      } else if (platform === 'linux') {
        const clamResult = await this.system.exec('systemctl is-active clamav-daemon 2>/dev/null || echo ""');
        const savResult = await this.system.exec('systemctl is-active sav-protect.service 2>/dev/null || echo ""');

        if (clamResult.includes('active')) {
          status = 'pass';
          details = 'ClamAV daemon is running';
        } else if (savResult.includes('active')) {
          status = 'pass';
          details = 'SOPHOS protection is running';
        } else {
          details = 'No antivirus service detected (clamav, sophos)';
        }
      } else if (platform === 'win32') {
        const result = await this.system.exec(
          'powershell -Command "Get-MpComputerStatus | Select-Object -Property AntivirusEnabled,RealTimeProtectionEnabled | Format-List" 2>nul || echo ""'
        );
        if (result.includes('AntivirusEnabled : True') && result.includes('RealTimeProtectionEnabled : True')) {
          status = 'pass';
          details = 'Windows Defender real-time protection is enabled';
        } else {
          details = 'Windows Defender may not be fully enabled';
        }
      } else {
        details = `Platform ${platform} not supported for antivirus check`;
        status = 'unknown';
      }
    } catch {
      details = 'Antivirus check could not be completed';
    }

    return {
      id: 'antivirus_running',
      name: 'Antivirus / Endpoint Protection Running',
      category: 'Endpoint Security',
      status,
      severity: 'high',
      details,
    };
  }

  async checkOSVersion(): Promise<ComplianceCheck> {
    const platform = this.system.platform();
    let status: ComplianceCheck['status'] = 'pass';
    let details = '';

    try {
      if (platform === 'darwin') {
        const version = await this.system.exec('sw_vers -productVersion 2>/dev/null || echo unknown');
        const build = await this.system.exec('sw_vers -buildVersion 2>/dev/null || echo unknown');
        const versionParts = version.trim().split('.').map(Number);
        const major = versionParts[0] ?? 0;
        if (major < 13) {
          status = 'warning';
          details = `macOS ${version.trim()} (${build.trim()}) - upgrade recommended (below Ventura)`;
        } else {
          details = `macOS ${version.trim()} (${build.trim()}) - current or supported version`;
        }
      } else if (platform === 'linux') {
        const version = await this.system.exec('cat /etc/os-release 2>/dev/null || echo unknown');
        const prettyName = version.split('\n').find(l => l.startsWith('PRETTY_NAME'));
        details = prettyName ? prettyName.split('=')[1]?.replace(/"/g, '') : 'Linux OS detected';
      } else if (platform === 'win32') {
        const result = await this.system.exec(
          'powershell -Command "(Get-CimInstance Win32_OperatingSystem).Caption" 2>nul || echo ""'
        );
        details = result.trim() || 'Windows OS detected';
      } else {
        details = `Platform ${platform} - version check not available`;
        status = 'unknown';
      }
    } catch {
      details = 'OS version check could not be completed';
    }

    return {
      id: 'os_up_to_date',
      name: 'Operating System Up to Date',
      category: 'Vulnerability Management',
      status,
      severity: 'high',
      details,
    };
  }

  async checkPasswordManager(): Promise<ComplianceCheck> {
    const platform = this.system.platform();
    let status: ComplianceCheck['status'] = 'fail';
    let details = '';

    try {
      if (platform === 'darwin') {
        const result = await this.system.exec(
          'ls /Applications/ 2>/dev/null | grep -i "1password\\|bitwarden\\|lastpass\\|dashlane\\|keeper\\|nordpass" || echo ""'
        );
        if (result.trim().length > 0) {
          status = 'pass';
          details = `Password manager found: ${result.trim().split('\n')[0]}`;
        } else {
          const homebrew = await this.system.exec(
            'brew list 2>/dev/null | grep -i "1password\\|bitwarden\\|lastpass\\|dashlane\\|keeper" || echo ""'
          );
          if (homebrew.trim().length > 0) {
            status = 'pass';
            details = `Password manager installed via Homebrew: ${homebrew.trim().split('\n')[0]}`;
          } else {
            details = 'No known password manager detected in /Applications';
          }
        }
      } else if (platform === 'linux') {
        const result = await this.system.exec(
          'which 1password bitwarden lastpass dashlane keeper 2>/dev/null || echo ""'
        );
        if (result.trim().length > 0) {
          status = 'pass';
          details = `Password manager binary found: ${result.trim().split('\n')[0]}`;
        } else {
          details = 'No known password manager detected in PATH';
        }
      } else if (platform === 'win32') {
        const result = await this.system.exec(
          'powershell -Command "Get-ItemProperty HKLM:\\Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\* 2>$null | Where-Object { $_.DisplayName -match \'1Password|Bitwarden|LastPass|Dashlane|Keeper\' } | Select-Object DisplayName" 2>nul || echo ""'
        );
        if (result.includes('DisplayName')) {
          status = 'pass';
          details = 'Password manager detected in installed programs';
        } else {
          details = 'No known password manager detected';
        }
      } else {
        details = `Platform ${platform} - password manager check not available`;
        status = 'unknown';
      }
    } catch {
      details = 'Password manager check could not be completed';
    }

    return {
      id: 'password_manager',
      name: 'Password Manager Installed',
      category: 'Identity & Access Management',
      status,
      severity: 'medium',
      details,
    };
  }

  async checkScreenLock(): Promise<ComplianceCheck> {
    const platform = this.system.platform();
    let status: ComplianceCheck['status'] = 'fail';
    let details = '';

    try {
      if (platform === 'darwin') {
        const result = await this.system.exec(
          'defaults read com.apple.screensaver 2>/dev/null || echo ""'
        );
        const askForPassword = await this.system.exec(
          'defaults read com.apple.screensaver askForPassword 2>/dev/null || echo ""'
        );
        if (askForPassword.includes('1')) {
          status = 'pass';
          details = 'Screen lock with password required is enabled';
        } else {
          details = 'Screen lock password requirement not confirmed';
        }
      } else if (platform === 'linux') {
        const result = await this.system.exec(
          'gsettings get org.gnome.desktop.screensaver lock-enabled 2>/dev/null || echo ""'
        );
        if (result.includes('true')) {
          status = 'pass';
          details = 'GNOME screen lock is enabled';
        } else {
          details = 'Screen lock not confirmed (GNOME settings not available or disabled)';
        }
      } else if (platform === 'win32') {
        const result = await this.system.exec(
          'reg query "HKCU\\Control Panel\\Desktop" /v ScreenSaveActive 2>nul || echo ""'
        );
        if (result.includes('0x1')) {
          status = 'pass';
          details = 'Screen saver / screen lock is active';
        } else {
          details = 'Screen saver not confirmed as active';
        }
      } else {
        details = `Platform ${platform} - screen lock check not available`;
        status = 'unknown';
      }
    } catch {
      details = 'Screen lock check could not be completed';
    }

    return {
      id: 'screen_lock',
      name: 'Screen Lock Configured',
      category: 'Physical Security',
      status,
      severity: 'medium',
      details,
    };
  }

  async checkAutoLock(): Promise<ComplianceCheck> {
    const platform = this.system.platform();
    let status: ComplianceCheck['status'] = 'fail';
    let details = '';

    try {
      if (platform === 'darwin') {
        const result = await this.system.exec(
          'defaults -currentHost read com.apple.screensaver idleTime 2>/dev/null || echo ""'
        );
        const match = result.trim().match(/^\d+$/);
        if (match) {
          const seconds = parseInt(match[0], 10);
          if (seconds > 0 && seconds <= 300) {
            status = 'pass';
            details = `Auto-lock timeout set to ${seconds} seconds`;
          } else if (seconds > 300) {
            status = 'warning';
            details = `Auto-lock timeout ${seconds} seconds exceeds 5-minute recommendation`;
          } else {
            details = 'Auto-lock is disabled (idleTime = 0)';
          }
        } else {
          details = 'Auto-lock idle time not determinable';
        }
      } else if (platform === 'linux') {
        const result = await this.system.exec(
          'gsettings get org.gnome.desktop.session idle-delay 2>/dev/null || echo ""'
        );
        const match = result.match(/^(\d+)$/);
        if (match) {
          const seconds = parseInt(match[1], 10);
          if (seconds > 0 && seconds <= 300) {
            status = 'pass';
            details = `Auto-lock idle delay set to ${seconds} seconds`;
          } else if (seconds > 300) {
            status = 'warning';
            details = `Auto-lock idle delay ${seconds} seconds exceeds recommendation`;
          } else {
            details = 'Auto-lock idle delay is disabled';
          }
        } else {
          details = 'Auto-lock delay not determinable';
        }
      } else if (platform === 'win32') {
        const result = await this.system.exec(
          'reg query "HKCU\\Control Panel\\Desktop" /v ScreenSaveTimeOut 2>nul || echo ""'
        );
        const match = result.match(/ScreenSaveTimeOut\s+REG_SZ\s+(\d+)/);
        if (match) {
          const seconds = parseInt(match[1], 10);
          if (seconds > 0 && seconds <= 300) {
            status = 'pass';
            details = `Auto-lock timeout set to ${seconds} seconds`;
          } else if (seconds > 300) {
            status = 'warning';
            details = `Auto-lock timeout ${seconds} seconds exceeds recommendation`;
          } else {
            details = 'Auto-lock is disabled';
          }
        } else {
          details = 'Auto-lock timeout not determinable';
        }
      } else {
        details = `Platform ${platform} - auto-lock check not available`;
        status = 'unknown';
      }
    } catch {
      details = 'Auto-lock check could not be completed';
    }

    return {
      id: 'auto_lock',
      name: 'Auto-Lock Timeout Active',
      category: 'Physical Security',
      status,
      severity: 'medium',
      details,
    };
  }

  generateReport(evidence: DeviceEvidence): DeviceReport {
    const frameworkScores = this.mapToFrameworks(evidence.checks);
    const failedChecks = evidence.checks.filter(
      (c) => c.status === 'fail' || c.status === 'warning'
    );

    return {
      deviceId: evidence.deviceId,
      hostname: evidence.hostname,
      timestamp: evidence.collectedAt,
      checks: evidence.checks,
      overallScore: evidence.overallScore,
      frameworkScores,
      failedChecks,
    };
  }

  private calculateScore(checks: ComplianceCheck[]): number {
    if (checks.length === 0) return 0;

    const severityWeights: Record<string, number> = {
      critical: 4,
      high: 3,
      medium: 2,
      low: 1,
    };

    let totalWeight = 0;
    let earnedWeight = 0;

    for (const check of checks) {
      const weight = severityWeights[check.severity] ?? 1;
      totalWeight += weight;
      if (check.status === 'pass') earnedWeight += weight;
      else if (check.status === 'warning') earnedWeight += weight * 0.5;
    }

    return totalWeight === 0 ? 0 : Math.round((earnedWeight / totalWeight) * 100);
  }

  private mapToFrameworks(checks: ComplianceCheck[]): Record<string, number> {
    const frameworkChecks: Record<string, { total: number; earned: number }> = {};

    for (const check of checks) {
      const rule = COMPLIANCE_RULES.find((r) => r.id === check.id);
      if (!rule) continue;

      for (const fw of rule.frameworks) {
        if (!frameworkChecks[fw]) frameworkChecks[fw] = { total: 0, earned: 0 };
        frameworkChecks[fw].total += 1;
        if (check.status === 'pass') frameworkChecks[fw].earned += 1;
        else if (check.status === 'warning') frameworkChecks[fw].earned += 0.5;
      }
    }

    const scores: Record<string, number> = {};
    for (const [fw, { total, earned }] of Object.entries(frameworkChecks)) {
      scores[fw] = total === 0 ? 0 : Math.round((earned / total) * 100);
    }
    return scores;
  }
}
