#!/usr/bin/env node
import { MCPServer, type MCPServerConfig } from "./server.js";

const config: MCPServerConfig = {
  baseUrl: process.env.GRC_CLAW_GATEWAY_URL ?? "http://localhost:37777",
  token: process.env.GRC_CLAW_TOKEN,
};

const server = new MCPServer(config);
server.start();
