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
// --json is the forwarding proof: in that mode the CLI must hand back exactly what the plugin
// sent. The default mode renders JSON Schema documents, so it is asserted separately below.
const stdioClient = new Client({ name: 'JutsuMcpCliCompatibilityStdio', version: '1.0.0' });
const stdioTransport = new StdioClientTransport({
  command: interpreter,
  args: [entryPoint, '--json', '--port', String(endpoint.port)],
  stderr: 'inherit'
});
const renderClient = new Client({ name: 'JutsuMcpCliCompatibilityRender', version: '1.0.0' });
const renderTransport = new StdioClientTransport({
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
  await renderClient.connect(renderTransport);

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

  // The rendered mode: the tool list must stay real JSON Schema, because the host builds calls
  // from it, while a schema inside a result becomes a signature that keeps every constraint.
  const { tools: renderTools } = await renderClient.listTools();
  assert.deepEqual(renderTools, httpTools, 'rendering must never touch the published tool list');

  const describeArguments = { requests: [{ id: 'core.registry.inspect' }] };
  const plainDescribe = await httpClient.callTool({ name: 'jutsu_capabilities_describe', arguments: describeArguments });
  const renderedDescribe = await renderClient.callTool({ name: 'jutsu_capabilities_describe', arguments: describeArguments });
  const plainSchema = plainDescribe.structuredContent.results[0].capability.inputSchema;
  const renderedSchema = renderedDescribe.structuredContent.results[0].capability.inputSchema;
  assert.equal(typeof plainSchema, 'object', 'the plugin should still send a JSON Schema object');
  assert.equal(typeof renderedSchema, 'string', 'the CLI should render a schema in a result as text');
  for (const property of Object.keys(plainSchema.properties ?? {})) {
    assert.ok(renderedSchema.includes(property), `rendered schema lost the property ${property}`);
  }
  for (const name of (plainSchema.required ?? [])) {
    assert.ok(new RegExp(`\b${name}: `).test(renderedSchema), `rendered schema lost that ${name} is required`);
  }
  assert.ok(renderedSchema.length < JSON.stringify(plainSchema).length, 'the signature should be shorter than its JSON');

  // Everything that is not a schema is identical between the two modes.
  const strip = value => JSON.parse(JSON.stringify(value), (key, item) => key.endsWith('Schema') ? undefined : item);
  assert.deepEqual(strip(renderedDescribe), strip(plainDescribe), 'rendering changed something other than a schema');

  console.log('stdio front end matched the live plugin on tools, instructions and all routes');
  console.log('rendered mode kept the tool list intact and every schema constraint readable');
} finally {
  await renderClient.close().catch(() => {});
  await stdioClient.close().catch(() => {});
  await httpClient.close().catch(() => {});
}
