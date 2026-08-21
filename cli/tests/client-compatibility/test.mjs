// Drives the CLI's stdio MCP front end with the official MCP client, and compares everything it
// sees against the same official client talking straight to the plugin over HTTP.
//
// The HTTP connection is the ground truth: whatever it publishes is what the stdio route has to
// publish, because the CLI's whole contract is that it forwards rather than declares.
//
//   npm ci
//   JUTSU_MCP_URL=http://127.0.0.1:19781/mcp JUTSU_CLI_PYTHON=python npm test
//
// An Unreal editor with the plugin has to be running.

import assert from 'node:assert/strict';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { Client, StreamableHTTPClientTransport } from '@modelcontextprotocol/client';
import { StdioClientTransport } from '@modelcontextprotocol/client/stdio';

const here = path.dirname(fileURLToPath(import.meta.url));
const entryPoint = path.resolve(here, '..', '..', 'jutsu_mcp_stdio.py');
const endpoint = new URL(process.env.JUTSU_MCP_URL ?? 'http://127.0.0.1:19781/mcp');
const interpreter = process.env.JUTSU_CLI_PYTHON ?? 'python';

const httpClient = new Client({ name: 'JutsuMcpCliCompatibilityHttp', version: '1.0.0' });
const stdioClient = new Client({ name: 'JutsuMcpCliCompatibilityStdio', version: '1.0.0' });
const stdioTransport = new StdioClientTransport({
  command: interpreter,
  args: [entryPoint, '--port', String(endpoint.port)],
  stderr: 'inherit'
});

const expectSuccess = (name, result) => {
  assert.notEqual(result.isError, true, `${name} unexpectedly returned a tool error`);
  assert.ok(result.structuredContent && typeof result.structuredContent === 'object', `${name} returned no structured content`);
};
const expectError = (name, result) => {
  assert.equal(result.isError, true, `${name} did not return an intentional tool error`);
  assert.ok(result.structuredContent?.error?.code, `${name} error omitted code`);
  assert.ok(result.structuredContent?.error?.message, `${name} error omitted message`);
};

// Continuation cursors are bound to the session that produced them, so two clients holding two
// sessions legitimately see two different cursor strings for the same page. Everything else in
// the response has to match exactly.
const withoutCursors = value => {
  if (Array.isArray(value)) return value.map(withoutCursors);
  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value)
        .filter(([key]) => key !== 'continuation')
        .map(([key, item]) => [key, withoutCursors(item)])
    );
  }
  return value;
};

// Read-only or idempotent on both routes, so the two clients can issue each call and be compared.
const successRoutes = [
  ['jutsu_recommend', { goal: 'Inspect the capability registry', constraints: ['read only'] }],
  ['jutsu_capabilities_search', { mode: 'search', query: 'inspect capability registry', limit: 5 }],
  ['jutsu_capabilities_describe', { requests: [{ id: 'core.registry.inspect' }] }],
  ['jutsu_inspect', { requests: [{ capability: 'core.registry.inspect', arguments: {} }] }]
];

// Every one of these violates the tool's own input contract, so the plugin - not the CLI - is
// what produces the diagnostic, and both routes must produce the same one.
const errorRoutes = [
  ['jutsu_recommend', {}],
  ['jutsu_capabilities_search', { query: 'no mode was given' }],
  ['jutsu_capabilities_describe', { requests: [] }],
  ['jutsu_inspect', { requests: [] }],
  ['jutsu_execute', { steps: [] }]
];

try {
  await httpClient.connect(new StreamableHTTPClientTransport(endpoint));
  await stdioClient.connect(stdioTransport);

  assert.equal(
    stdioClient.getInstructions(),
    httpClient.getInstructions(),
    'the CLI did not forward the plugin instructions byte-identically'
  );

  const { tools: httpTools } = await httpClient.listTools();
  const { tools: stdioTools } = await stdioClient.listTools();
  assert.deepEqual(stdioTools.map(tool => tool.name).sort(), [
    'jutsu_capabilities_describe',
    'jutsu_capabilities_search',
    'jutsu_execute',
    'jutsu_inspect',
    'jutsu_recommend'
  ]);
  assert.deepEqual(stdioTools, httpTools, 'the CLI tool list differs from the live plugin tool list');

  for (const [name, args] of successRoutes) {
    const overHttp = await httpClient.callTool({ name, arguments: args });
    const overStdio = await stdioClient.callTool({ name, arguments: args });
    expectSuccess(`${name} over stdio`, overStdio);
    assert.deepEqual(withoutCursors(overStdio), withoutCursors(overHttp), `${name} differed between the CLI and the plugin`);
  }

  // jutsu_execute writes, so it gets a value it already holds rather than a new one.
  const settings = { class: '/Script/JutsuUnrealMcp.JutsuUnrealMcpSettings', property: 'Port' };
  const read = await stdioClient.callTool({
    name: 'jutsu_inspect',
    arguments: { requests: [{ capability: 'settings.get', arguments: settings }] }
  });
  expectSuccess('settings.get over stdio', read);
  const currentPort = read.structuredContent.results[0].result.value;
  const executeArguments = {
    steps: [{ capability: 'settings.set', arguments: { ...settings, value: currentPort } }]
  };
  const executeOverHttp = await httpClient.callTool({ name: 'jutsu_execute', arguments: executeArguments });
  const executeOverStdio = await stdioClient.callTool({ name: 'jutsu_execute', arguments: executeArguments });
  expectSuccess('jutsu_execute over stdio', executeOverStdio);
  assert.deepEqual(withoutCursors(executeOverStdio), withoutCursors(executeOverHttp), 'jutsu_execute differed between the CLI and the plugin');

  for (const [name, args] of errorRoutes) {
    const overHttp = await httpClient.callTool({ name, arguments: args });
    const overStdio = await stdioClient.callTool({ name, arguments: args });
    expectError(`${name} over stdio`, overStdio);
    assert.deepEqual(withoutCursors(overStdio), withoutCursors(overHttp), `${name} error differed between the CLI and the plugin`);
  }

  console.log('stdio front end matched the live plugin on tools, instructions and all routes');
} finally {
  await stdioClient.close().catch(() => {});
  await httpClient.close().catch(() => {});
}
