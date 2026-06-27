export type HttpMethod = 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';

export interface EndpointDefinition {
  path: string;
  method: HttpMethod;
  summary: string;
  description: string;
  tags: string[];
  operationId: string;
  authenticated: boolean;
  requestBody?: {
    contentType: string;
    schema: Record<string, unknown>;
  };
  queryParams?: Array<{
    name: string;
    in: string;
    required: boolean;
    schema: Record<string, unknown>;
    description?: string;
  }>;
  responses: Record<string, {
    description: string;
    contentType?: string;
    schema?: Record<string, unknown>;
  }>;
}

export interface OpenApiSpec {
  openapi: string;
  info: {
    title: string;
    version: string;
    description: string;
    license: { name: string; url: string };
  };
  servers: Array<{ url: string; description: string }>;
  paths: Record<string, Record<string, Record<string, unknown>>>;
  components: {
    securitySchemes: Record<string, Record<string, unknown>>;
    schemas: Record<string, Record<string, unknown>>;
  };
  tags: Array<{ name: string; description: string }>;
}

export interface GeneratorConfig {
  title: string;
  version: string;
  description: string;
  baseUrl: string;
}
