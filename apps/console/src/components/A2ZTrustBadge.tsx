import { loadSettings } from '../lib/settings';

interface A2ZTrustBadgeProps {
  compact?: boolean;
}

export function A2ZTrustBadge({ compact }: A2ZTrustBadgeProps) {
  const { a2zSocUrl, a2zTrustTenantId, trustScore, trustTier } = loadSettings();
  const profileUrl = `${a2zSocUrl.replace(/\/$/, '')}/trust/${encodeURIComponent(a2zTrustTenantId)}`;
  const w = compact ? 180 : 220;
  const h = compact ? 48 : 60;

  return (
    <a
      href={profileUrl}
      target="_blank"
      rel="noopener noreferrer"
      className="trust-badge-link"
      title="View continuous trust profile on A2Z SOC"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width={w}
        height={h}
        viewBox={`0 0 ${w} ${h}`}
        role="img"
        aria-label={`Secured by A2Z SOC ${trustTier} ${trustScore} of 100`}
      >
        <rect width={w} height={h} rx="10" fill="#0b1220" stroke="#22d3ee" strokeWidth="1" />
        <text
          x={w / 2}
          y={compact ? 20 : 24}
          fill="#e2e8f0"
          fontSize={compact ? 10 : 12}
          fontFamily="system-ui, sans-serif"
          textAnchor="middle"
        >
          Secured by A2Z SOC
        </text>
        <text
          x={w / 2}
          y={compact ? 36 : 44}
          fill="#22d3ee"
          fontSize={compact ? 13 : 15}
          fontWeight="700"
          fontFamily="system-ui, sans-serif"
          textAnchor="middle"
        >
          {trustTier} · {trustScore}/100
        </text>
      </svg>
    </a>
  );
}
