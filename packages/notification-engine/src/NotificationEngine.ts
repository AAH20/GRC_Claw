import type {
  ChannelConfig,
  NotificationChannel,
  NotificationPayload,
  NotificationTemplate,
  NotificationSeverity,
  ResolvedPayload,
  DeliveryRecord,
  DeliveryStatus,
  RateLimitConfig,
  RateLimitState,
  RetryConfig,
} from './types.js';
import { generateId, DEFAULT_RATE_LIMIT, DEFAULT_RETRY_CONFIG } from './types.js';

// ─── Template Renderer ──────────────────────────────────────────────

function renderTemplate(payload: NotificationPayload): ResolvedPayload {
  const { template, severity, title, message, data, tags } = payload;
  const severityEmoji: Record<NotificationSeverity, string> = {
    info: '\u2139\uFE0F',
    warning: '\u26A0\uFE0F',
    critical: '\uD83D\uDD34',
  };
  const prefix = severityEmoji[severity] ?? '';
  const tagLine = tags?.length ? `\nTags: ${tags.join(', ')}` : '';

  const dataLines = data
    ? Object.entries(data).map(([k, v]) => `  ${k}: ${typeof v === 'string' ? v : JSON.stringify(v)}`).join('\n')
    : '';

  switch (template) {
    case 'compliance_alert':
      return {
        title: `${prefix} Compliance Alert: ${title}`,
        body: `${message}${dataLines ? `\n\nDetails:\n${dataLines}` : ''}${tagLine}`,
        slack: {
          text: `${prefix} *Compliance Alert: ${title}*\n${message}`,
          blocks: [
            { type: 'header', text: { type: 'plain_text', text: `${prefix} Compliance Alert: ${title}` } },
            { type: 'section', text: { type: 'mrkdwn', text: message } },
            ...(data ? [{ type: 'section', fields: Object.entries(data).map(([k, v]) => ({ type: 'mrkdwn', text: `*${k}:*\n${v}` })) }] : []),
          ],
        },
        email: {
          subject: `[${severity.toUpperCase()}] Compliance Alert: ${title}`,
          html: `<h2>${prefix} Compliance Alert: ${title}</h2><p>${message}</p>${dataLines ? `<pre>${dataLines}</pre>` : ''}`,
          text: `${prefix} Compliance Alert: ${title}\n${message}\n${dataLines}`,
        },
        teams: {
          text: `${prefix} **Compliance Alert: ${title}**\n${message}`,
          themeColor: severity === 'critical' ? 'FF0000' : severity === 'warning' ? 'FFC107' : '0078D4',
          facts: data ? Object.entries(data).map(([k, v]) => ({ name: k, value: String(v) })) : undefined,
        },
      };

    case 'drift_alert':
      return {
        title: `${prefix} Drift Detected: ${title}`,
        body: `${message}${dataLines ? `\n\nDrift Details:\n${dataLines}` : ''}${tagLine}`,
        slack: {
          text: `${prefix} *Drift Detected: ${title}*\n${message}`,
          blocks: [
            { type: 'header', text: { type: 'plain_text', text: `${prefix} Drift Detected: ${title}` } },
            { type: 'section', text: { type: 'mrkdwn', text: message } },
          ],
        },
        email: {
          subject: `[${severity.toUpperCase()}] Drift Detected: ${title}`,
          html: `<h2>${prefix} Drift Detected: ${title}</h2><p>${message}</p>`,
          text: `${prefix} Drift Detected: ${title}\n${message}`,
        },
        teams: {
          text: `${prefix} **Drift Detected: ${title}**\n${message}`,
          themeColor: severity === 'critical' ? 'FF0000' : 'FFC107',
        },
      };

    case 'remediation_complete':
      return {
        title: `\u2705 Remediation Complete: ${title}`,
        body: `${message}${dataLines ? `\n\nSummary:\n${dataLines}` : ''}${tagLine}`,
        slack: {
          text: `\u2705 *Remediation Complete: ${title}*\n${message}`,
          blocks: [
            { type: 'header', text: { type: 'plain_text', text: `\u2705 Remediation Complete: ${title}` } },
            { type: 'section', text: { type: 'mrkdwn', text: message } },
          ],
        },
        email: {
          subject: `[RESOLVED] Remediation Complete: ${title}`,
          html: `<h2>\u2705 Remediation Complete: ${title}</h2><p>${message}</p>`,
          text: `\u2705 Remediation Complete: ${title}\n${message}`,
        },
        teams: {
          text: `\u2705 **Remediation Complete: ${title}**\n${message}`,
          themeColor: '00FF00',
        },
      };

    case 'incident_created':
      return {
        title: `${prefix} Incident Created: ${title}`,
        body: `${message}${dataLines ? `\n\nIncident Details:\n${dataLines}` : ''}${tagLine}`,
        slack: {
          text: `${prefix} *Incident Created: ${title}*\n${message}`,
        },
        email: {
          subject: `[${severity.toUpperCase()}] Incident Created: ${title}`,
          html: `<h2>${prefix} Incident Created: ${title}</h2><p>${message}</p>`,
          text: `${prefix} Incident Created: ${title}\n${message}`,
        },
        teams: {
          text: `${prefix} **Incident Created: ${title}**\n${message}`,
          themeColor: severity === 'critical' ? 'FF0000' : 'FFC107',
        },
      };

    case 'risk_threshold_exceeded':
      return {
        title: `${prefix} Risk Threshold Exceeded: ${title}`,
        body: `${message}${dataLines ? `\n\nRisk Details:\n${dataLines}` : ''}${tagLine}`,
        slack: {
          text: `${prefix} *Risk Threshold Exceeded: ${title}*\n${message}`,
        },
        email: {
          subject: `[${severity.toUpperCase()}] Risk Threshold Exceeded: ${title}`,
          html: `<h2>${prefix} Risk Threshold Exceeded: ${title}</h2><p>${message}</p>`,
          text: `${prefix} Risk Threshold Exceeded: ${title}\n${message}`,
        },
        teams: {
          text: `${prefix} **Risk Threshold Exceeded: ${title}**\n${message}`,
          themeColor: 'FF0000',
        },
      };

    case 'custom':
    default:
      return {
        title: `${prefix} ${title}`,
        body: `${message}${dataLines ? `\n\nData:\n${dataLines}` : ''}${tagLine}`,
        slack: { text: `${prefix} *${title}*\n${message}` },
        email: {
          subject: `[${severity.toUpperCase()}] ${title}`,
          html: `<h2>${prefix} ${title}</h2><p>${message}</p>`,
          text: `${prefix} ${title}\n${message}`,
        },
        teams: {
          text: `${prefix} **${title}**\n${message}`,
          themeColor: severity === 'critical' ? 'FF0000' : severity === 'warning' ? 'FFC107' : '0078D4',
        },
      };
  }
}

// ─── Channel Senders ────────────────────────────────────────────────

async function sendSlack(config: { webhookUrl: string; channel?: string; username?: string; iconEmoji?: string }, payload: ResolvedPayload): Promise<void> {
  const body: Record<string, unknown> = {
    text: payload.slack?.text ?? payload.title,
    channel: config.channel,
    username: config.username,
    icon_emoji: config.iconEmoji,
  };
  if (payload.slack?.blocks) {
    body.blocks = payload.slack.blocks;
  }
  const response = await fetch(config.webhookUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(10_000),
  });
  if (!response.ok) {
    throw new Error(`Slack webhook failed: ${response.status} ${response.statusText}`);
  }
}

async function sendEmail(config: { smtpHost: string; smtpPort: number; smtpUser: string; smtpPass: string; fromAddress: string; useTls?: boolean }, payload: ResolvedPayload): Promise<void> {
  const net = await import('node:net');
  const tls = await import('node:tls');

  const subject = payload.email?.subject ?? payload.title;
  const body = payload.email?.text ?? payload.body;
  const htmlBody = payload.email?.html ?? `<p>${payload.body}</p>`;
  const boundary = `----=_Part_${Date.now()}`;

  const rawEmail = [
    `From: ${config.fromAddress}`,
    `To: ${config.fromAddress}`,
    `Subject: ${subject}`,
    `MIME-Version: 1.0`,
    `Content-Type: multipart/alternative; boundary="${boundary}"`,
    ``,
    `--${boundary}`,
    `Content-Type: text/plain; charset=UTF-8`,
    ``,
    body,
    ``,
    `--${boundary}`,
    `Content-Type: text/html; charset=UTF-8`,
    ``,
    htmlBody,
    ``,
    `--${boundary}--`,
    ``,
  ].join('\r\n');

  const socket = new net.Socket();
  await new Promise<void>((resolve, reject) => {
    socket.connect(config.smtpPort, config.smtpHost, () => resolve());
    socket.setTimeout(10_000);
    socket.on('timeout', () => { socket.destroy(); reject(new Error('SMTP connection timeout')); });
    socket.on('error', (err) => reject(err));
  });

  const sendCommand = async (cmd: string, expectedCode?: number): Promise<string> => {
    return new Promise<string>((resolve, reject) => {
      let data = '';
      const onData = (chunk: Buffer) => {
        data += chunk.toString();
        if (expectedCode && data.match(new RegExp(`^${expectedCode}`))) {
          socket.removeListener('data', onData);
          resolve(data);
        } else if (!expectedCode && data.length > 0) {
          socket.removeListener('data', onData);
          resolve(data);
        }
      };
      socket.on('data', onData);
      socket.write(cmd + '\r\n');
      if (!expectedCode) {
        setTimeout(() => { socket.removeListener('data', onData); resolve(data); }, 500);
      }
    });
  };

  try {
    await sendCommand('', 220);
    await sendCommand(`EHLO localhost`, 250);

    if (config.useTls !== false) {
      await sendCommand('STARTTLS', 220);
      const upgraded = tls.connect({ socket, servername: config.smtpHost, rejectUnauthorized: false });
      await new Promise<void>((resolve, reject) => {
        upgraded.on('secureConnect', resolve);
        upgraded.on('error', reject);
      });
      // Re-wrap socket methods for the upgraded connection
      const origWrite = upgraded.write.bind(upgraded);
      const upgradedSocket = upgraded;
      // Use upgraded socket for remaining commands
      const sendCommandTLS = async (cmd: string, expectedCode: number): Promise<string> => {
        return new Promise<string>((resolve, reject) => {
          let data = '';
          const onData = (chunk: Buffer) => {
            data += chunk.toString();
            if (data.match(new RegExp(`^${expectedCode}`))) {
              upgradedSocket.removeListener('data', onData);
              resolve(data);
            }
          };
          upgradedSocket.on('data', onData);
          origWrite(cmd + '\r\n');
        });
      };
      await sendCommandTLS('EHLO localhost', 250);
      await sendCommandTLS('AUTH LOGIN', 334);
      await sendCommandTLS(Buffer.from(config.smtpUser).toString('base64'), 334);
      await sendCommandTLS(Buffer.from(config.smtpPass).toString('base64'), 235);
      await sendCommandTLS(`MAIL FROM:<${config.fromAddress}>`, 250);
      await sendCommandTLS(`RCPT TO:<${config.fromAddress}>`, 250);
      await sendCommandTLS('DATA', 354);
      await sendCommandTLS(rawEmail + '\r\n.', 250);
      await sendCommandTLS('QUIT', 221);
    } else {
      await sendCommand('AUTH LOGIN', 334);
      await sendCommand(Buffer.from(config.smtpUser).toString('base64'), 334);
      await sendCommand(Buffer.from(config.smtpPass).toString('base64'), 235);
      await sendCommand(`MAIL FROM:<${config.fromAddress}>`, 250);
      await sendCommand(`RCPT TO:<${config.fromAddress}>`, 250);
      await sendCommand('DATA', 354);
      await sendCommand(rawEmail + '\r\n.', 250);
      await sendCommand('QUIT', 221);
    }
  } finally {
    socket.destroy();
  }
}

async function sendTeams(config: { webhookUrl: string }, payload: ResolvedPayload): Promise<void> {
  const body: Record<string, unknown> = {
    text: payload.teams?.text ?? payload.title,
  };
  if (payload.teams?.themeColor) {
    body.themeColor = payload.teams.themeColor;
  }
  if (payload.teams?.facts) {
    body.sections = [{ facts: payload.teams.facts }];
  }
  const response = await fetch(config.webhookUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout(10_000),
  });
  if (!response.ok) {
    throw new Error(`Teams webhook failed: ${response.status} ${response.statusText}`);
  }
}

// ─── Notification Engine ────────────────────────────────────────────

export interface NotificationEngineConfig {
  channels: ChannelConfig;
  rateLimits?: Partial<Record<NotificationChannel, Partial<RateLimitConfig>>>;
  retry?: Partial<RetryConfig>;
}

export class NotificationEngine {
  private config: NotificationEngineConfig;
  private retryConfig: RetryConfig;
  private history: Map<string, DeliveryRecord> = new Map();
  private rateLimitState: Map<NotificationChannel, RateLimitState> = new Map();

  constructor(config: NotificationEngineConfig) {
    this.config = config;
    this.retryConfig = { ...DEFAULT_RETRY_CONFIG, ...config.retry };
  }

  // ── Public API ──

  async send(payload: NotificationPayload): Promise<DeliveryRecord[]> {
    const records: DeliveryRecord[] = [];

    for (const channel of payload.channels) {
      if (!this.isChannelEnabled(channel)) {
        records.push(this.createRecord(channel, payload, 'failed', 'Channel not configured'));
        continue;
      }

      if (this.isRateLimited(channel)) {
        records.push(this.createRecord(channel, payload, 'rate_limited', 'Rate limit exceeded'));
        continue;
      }

      const record = await this.sendWithRetry(channel, payload);
      records.push(record);
      this.history.set(record.id, record);
    }

    return records;
  }

  getHistory(channel?: NotificationChannel, limit = 50): DeliveryRecord[] {
    const records = Array.from(this.history.values());
    const filtered = channel ? records.filter(r => r.channel === channel) : records;
    return filtered
      .sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())
      .slice(0, limit);
  }

  getDeliveryStats(): { total: number; sent: number; failed: number; rateLimited: number; byChannel: Record<string, { sent: number; failed: number }> } {
    const records = Array.from(this.history.values());
    const byChannel: Record<string, { sent: number; failed: number }> = {};

    for (const record of records) {
      if (!byChannel[record.channel]) {
        byChannel[record.channel] = { sent: 0, failed: 0 };
      }
      if (record.status === 'sent') byChannel[record.channel].sent++;
      if (record.status === 'failed') byChannel[record.channel].failed++;
    }

    return {
      total: records.length,
      sent: records.filter(r => r.status === 'sent').length,
      failed: records.filter(r => r.status === 'failed').length,
      rateLimited: records.filter(r => r.status === 'rate_limited').length,
      byChannel,
    };
  }

  // ── Private Methods ──

  private isChannelEnabled(channel: NotificationChannel): boolean {
    return this.config.channels[channel] !== undefined;
  }

  private isRateLimited(channel: NotificationChannel): boolean {
    const limit = this.getRateLimit(channel);
    const now = Date.now();
    let state = this.rateLimitState.get(channel);

    if (!state) {
      state = { minuteCount: 0, hourCount: 0, dayCount: 0, minuteWindowStart: now, hourWindowStart: now, dayWindowStart: now };
      this.rateLimitState.set(channel, state);
    }

    // Reset windows
    if (now - state.minuteWindowStart >= 60_000) {
      state.minuteCount = 0;
      state.minuteWindowStart = now;
    }
    if (now - state.hourWindowStart >= 3_600_000) {
      state.hourCount = 0;
      state.hourWindowStart = now;
    }
    if (now - state.dayWindowStart >= 86_400_000) {
      state.dayCount = 0;
      state.dayWindowStart = now;
    }

    if (state.minuteCount >= limit.maxPerMinute) return true;
    if (state.hourCount >= limit.maxPerHour) return true;
    if (state.dayCount >= limit.maxPerDay) return true;

    state.minuteCount++;
    state.hourCount++;
    state.dayCount++;
    return false;
  }

  private getRateLimit(channel: NotificationChannel): RateLimitConfig {
    return { ...DEFAULT_RATE_LIMIT, ...this.config.rateLimits?.[channel] };
  }

  private async sendWithRetry(channel: NotificationChannel, payload: NotificationPayload): Promise<DeliveryRecord> {
    const resolved = renderTemplate(payload);
    let lastError: string | undefined;
    const record = this.createRecord(channel, payload, 'pending');
    record.resolvedPayload = resolved;

    for (let attempt = 0; attempt <= this.retryConfig.maxRetries; attempt++) {
      try {
        record.attempts = attempt + 1;
        record.status = 'retrying';
        await this.sendToChannel(channel, resolved);
        record.status = 'sent';
        record.sentAt = new Date().toISOString();
        record.updatedAt = new Date().toISOString();
        return record;
      } catch (err) {
        lastError = err instanceof Error ? err.message : String(err);
        record.lastError = lastError;
        record.updatedAt = new Date().toISOString();

        if (attempt < this.retryConfig.maxRetries) {
          const delay = Math.min(
            this.retryConfig.baseDelayMs * Math.pow(2, attempt),
            this.retryConfig.maxDelayMs,
          );
          await new Promise(resolve => setTimeout(resolve, delay));
        }
      }
    }

    record.status = 'failed';
    return record;
  }

  private async sendToChannel(channel: NotificationChannel, payload: ResolvedPayload): Promise<void> {
    switch (channel) {
      case 'slack': {
        const cfg = this.config.channels.slack!;
        await sendSlack(cfg, payload);
        break;
      }
      case 'email': {
        const cfg = this.config.channels.email!;
        await sendEmail(cfg, payload);
        break;
      }
      case 'teams': {
        const cfg = this.config.channels.teams!;
        await sendTeams(cfg, payload);
        break;
      }
    }
  }

  private createRecord(channel: NotificationChannel, payload: NotificationPayload, status: DeliveryStatus, error?: string): DeliveryRecord {
    const now = new Date().toISOString();
    return {
      id: generateId(),
      channel,
      status,
      payload,
      resolvedPayload: renderTemplate(payload),
      attempts: 0,
      lastError: error,
      createdAt: now,
      updatedAt: now,
    };
  }
}
