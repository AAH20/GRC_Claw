/**
 * GRC_Claw — cloud-connectors/aws-asset-inventory.ts
 *
 * AWS asset inventory scanner — pulls EC2, S3, IAM, RDS assets into the
 * security graph format used by A2Z SOC's cloud-assets API endpoint.
 *
 * Uses AWS SDK v3 via dynamic import so the SDK remains an optional peer dep.
 * Callers must install @aws-sdk/client-ec2 and @aws-sdk/client-s3 as needed.
 * Falls back gracefully (empty arrays) when SDK is absent or credentials fail.
 */

export interface CloudAssetNode {
  id: string;
  type: 'ec2_instance' | 's3_bucket' | 'iam_user' | 'rds_instance' | 'security_group' | 'vpc';
  label: string;
  region: string;
  account_id: string;
  metadata: Record<string, unknown>;
  /** Risk flags detected during scan, e.g. 'public_ip', 'no_mfa', 'public_acl' */
  risk_indicators: string[];
  /** IDs of connected asset nodes */
  connected_to: string[];
}

export interface CloudAssetEdge {
  from: string;
  to: string;
  label: string;
}

export interface ScanConfig {
  /** AWS access key ID. Omit to use instance profile / env vars. */
  accessKeyId?: string;
  /** AWS secret access key. Required if accessKeyId is set. */
  secretAccessKey?: string;
  region: string;
  accountId?: string;
}

export interface ScanResult {
  nodes: CloudAssetNode[];
  edges: CloudAssetEdge[];
  errors: string[];
  scanned_at: string;
}

/**
 * Scan AWS account for EC2 instances and S3 buckets.
 * Returns a graph of asset nodes and edges suitable for
 * POST /api/platform/cloud-assets.
 */
export async function scanAwsAssets(config: ScanConfig): Promise<ScanResult> {
  const nodes: CloudAssetNode[] = [];
  const edges: CloudAssetEdge[] = [];
  const errors: string[] = [];

  const credentials =
    config.accessKeyId && config.secretAccessKey
      ? { accessKeyId: config.accessKeyId, secretAccessKey: config.secretAccessKey }
      : undefined;

  // ─── EC2: instances, security groups ──────────────────────────────────────
  try {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const { EC2Client, DescribeInstancesCommand, DescribeSecurityGroupsCommand } = await import('@aws-sdk/client-ec2' as any);
    const ec2 = new EC2Client({ region: config.region, ...(credentials ? { credentials } : {}) });

    const { Reservations = [] } = await ec2.send(new DescribeInstancesCommand({ MaxResults: 100 }));
    for (const r of Reservations) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      for (const inst of (r.Instances ?? []) as any[]) {
        const risks: string[] = [];
        if (inst.PublicIpAddress) risks.push('public_ip');
        if (!inst.IamInstanceProfile) risks.push('no_iam_role');
        if (inst.State?.Name === 'running' && inst.MetadataOptions?.HttpTokens !== 'required') risks.push('imdsv1_enabled');

        const name =
          inst.Tags?.find((t: { Key: string; Value: string }) => t.Key === 'Name')?.Value ??
          inst.InstanceId ??
          'EC2';

        const node: CloudAssetNode = {
          id: `ec2:${inst.InstanceId}`,
          type: 'ec2_instance',
          label: name,
          region: config.region,
          account_id: config.accountId ?? 'unknown',
          metadata: {
            instance_type: inst.InstanceType,
            state: inst.State?.Name,
            public_ip: inst.PublicIpAddress ?? null,
            private_ip: inst.PrivateIpAddress ?? null,
            launch_time: inst.LaunchTime,
          },
          risk_indicators: risks,
          connected_to: inst.SecurityGroups?.map((sg: { GroupId: string }) => `sg:${sg.GroupId}`) ?? [],
        };
        nodes.push(node);

        for (const sg of inst.SecurityGroups ?? []) {
          edges.push({ from: node.id, to: `sg:${sg.GroupId}`, label: 'protected_by' });
        }
        if (inst.VpcId) {
          edges.push({ from: node.id, to: `vpc:${inst.VpcId}`, label: 'in_vpc' });
        }
      }
    }

    // Security groups
    const { SecurityGroups = [] } = await ec2.send(new DescribeSecurityGroupsCommand({ MaxResults: 100 }));
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    for (const sg of SecurityGroups as any[]) {
      const risks: string[] = [];
      const hasOpenIngress = sg.IpPermissions?.some(
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        (p: any) => p.IpRanges?.some((r: any) => r.CidrIp === '0.0.0.0/0') || p.Ipv6Ranges?.some((r: any) => r.CidrIpv6 === '::/0')
      );
      if (hasOpenIngress) risks.push('open_ingress_0.0.0.0/0');

      nodes.push({
        id: `sg:${sg.GroupId}`,
        type: 'security_group',
        label: sg.GroupName ?? sg.GroupId,
        region: config.region,
        account_id: config.accountId ?? 'unknown',
        metadata: { description: sg.Description, vpc_id: sg.VpcId },
        risk_indicators: risks,
        connected_to: [],
      });
    }
  } catch (e) {
    errors.push(`EC2 scan: ${(e as Error).message}`);
  }

  // ─── S3: buckets + public ACL check ───────────────────────────────────────
  try {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const { S3Client, ListBucketsCommand, GetBucketAclCommand } = await import('@aws-sdk/client-s3' as any);
    const s3 = new S3Client({ region: config.region, ...(credentials ? { credentials } : {}) });

    const { Buckets = [] } = await s3.send(new ListBucketsCommand({}));
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    for (const bucket of (Buckets as any[]).slice(0, 50)) {
      const risks: string[] = [];
      try {
        const { Grants } = await s3.send(new GetBucketAclCommand({ Bucket: bucket.Name }));
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const isPublic = (Grants ?? []).some((g: any) => g.Grantee?.URI?.includes('AllUsers'));
        if (isPublic) risks.push('public_acl');
      } catch {
        // No permission to read ACL — treat as unknown
      }

      nodes.push({
        id: `s3:${bucket.Name}`,
        type: 's3_bucket',
        label: bucket.Name ?? 'S3 Bucket',
        region: config.region,
        account_id: config.accountId ?? 'unknown',
        metadata: { created: bucket.CreationDate },
        risk_indicators: risks,
        connected_to: [],
      });
    }
  } catch (e) {
    errors.push(`S3 scan: ${(e as Error).message}`);
  }

  return { nodes, edges, errors, scanned_at: new Date().toISOString() };
}
