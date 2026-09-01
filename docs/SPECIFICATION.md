# MCP Server Passport & Fingerprint Specification

Version: `1.0.0`  
Standard: Open MCP Server Passport & Signature Specification  
Maintainer: [@JMartynov](https://github.com/JMartynov)

---

## 1. Executive Summary & Purpose

The **Model Context Protocol (MCP)** enables Large Language Model (LLM) agents to access external data sources, execute commands, and invoke tools across diverse ecosystems (npm, PyPI, Go, Rust, Docker). However, the decentralized and dynamic nature of MCP introduces critical security and governance challenges:

1. **Tool Poisoning & Description Manipulation**: Malicious or hijacked servers can silently alter tool input schemas or inject hidden instructions into tool descriptions to manipulate agent reasoning.
2. **Server Impersonation & Typosquatting**: Malicious actors publish counterfeit MCP servers mimicking legitimate database connectors or cloud utilities.
3. **Version Drift & Silent Capabilities**: Between package releases, developers may introduce high-privilege tools without schema validation or operator awareness.
4. **Anonymous Runtime Discovery**: When an agent connects to an unauthenticated or third-party MCP endpoint, there is no standardized cryptographic mechanism to identify what package and version the server actually is.

The **MCP Fingerprint & Passport Knowledge Base** solves these challenges by computing deterministic, order-invariant cryptographic hashes over MCP tool contracts, resource templates, and prompt interfaces, packaging them into canonical **MCP Server Passports**.

---

## 2. Core Architecture & Concepts

### 2.1 The MCP Server Passport (`ServerPackageSpec`)
An **MCP Passport** is a standardized, high-fidelity JSON document representing the catalog identity, metadata, and complete historical evolution of an MCP server across all published versions.

### 2.2 Canonical Toolset Hash (`toolset_canonical_hash`)
A deterministic SHA-256 digest computed across all tools exposed by an MCP server version. The hashing algorithm is strictly **order-independent** and **whitespace-invariant**, ensuring that two servers exposing identical JSON Schema tool contracts produce the exact same hash regardless of the order tools were declared in JSON or runtime registration.

### 2.3 Layered Matching Engine
- **Layer 1 (Exact Cryptographic Match)**: $O(1)$ lookup matching the client's observed runtime toolset hash directly against known passports.
- **Layer 2 (Topological & Signature Similarity)**: Jaccard and structural similarity metrics identifying renamed servers or version-drift mutations ($0.0 \le S \le 1.0$).
- **Layer 3 (Name/PURL/Alias Disambiguation)**: Fast token and prefix resolution across npm scopes, PyPI distribution names, and Smithery qualified identifiers.

---

## 3. Data Format & Schema Specification

Every passport document in `data/fingerprints/<package_name>.json` conforms to the following schema hierarchy.

```
ServerPackageSpec
 ├── package_name: string (Required)
 ├── purl: string (Required, Package URL RFC)
 ├── ecosystem: "npm" | "pypi" | "generic" | "github" | "golang"
 ├── display_name: string | null
 ├── description: string | null
 ├── repository_url: string | null
 ├── homepage_url: string | null
 ├── license: string | null
 ├── verified: boolean
 ├── download_count: integer
 ├── stars: integer
 ├── dist_tags: { "latest": string, ... }
 ├── categories: [ string, ... ]
 ├── keywords: [ string, ... ]
 ├── aliases: [ string, ... ]
 └── versions: [ VersionFingerprint, ... ]
      ├── version: string (SemVer)
      ├── toolset_canonical_hash: string (SHA-256 hex)
      ├── release_date: string (ISO 8601 UTC) | null
      ├── dependencies: { string: string }
      ├── connections: [ object, ... ]
      ├── capabilities: { "tools": bool, "prompts": bool, "resources": bool, "logging": bool }
      ├── tool_signatures: [ ToolContractSignature, ... ]
      │    ├── name: string
      │    ├── canonical_hash: string (SHA-256 hex)
      │    ├── description: string
      │    ├── description_hash: string (SHA-256 hex)
      │    ├── is_mutating: boolean
      │    ├── property_keys: [ string, ... ]
      │    ├── required_keys: [ string, ... ]
      │    ├── parameter_types: { key: type_string }
      │    ├── inputSchema: object (JSON Schema)
      │    └── outputSchema: object | null
      ├── prompt_signatures: [ PromptSignature, ... ]
      │    ├── name: string
      │    ├── description: string
      │    └── argument_keys: [ string, ... ]
      └── resource_signatures: [ ResourceSignature, ... ]
           ├── uri: string (or URI template)
           ├── name: string
           ├── description: string
           └── mimeType: string | null
```

---

## 4. Comprehensive Schema Sub-Variants & Detailed JSON Examples

### 4.1 Variant A: Complete Multi-Version Passport (npm Ecosystem)

This example shows a full passport for `@modelcontextprotocol/server-postgres` containing multiple versions, schema drift tracking, and rich tool contracts.

```json
{
  "package_name": "@modelcontextprotocol/server-postgres",
  "purl": "pkg:npm/%40modelcontextprotocol/server-postgres",
  "ecosystem": "npm",
  "display_name": "PostgreSQL MCP Server",
  "description": "Model Context Protocol server providing read and write capabilities to PostgreSQL databases with parameterized query validation.",
  "repository_url": "https://github.com/modelcontextprotocol/servers",
  "homepage_url": "https://modelcontextprotocol.io",
  "license": "MIT",
  "verified": true,
  "download_count": 128500,
  "stars": 4200,
  "dist_tags": {
    "latest": "0.6.2",
    "next": "0.7.0-beta.1"
  },
  "categories": [
    "database",
    "sql",
    "infrastructure"
  ],
  "keywords": [
    "mcp",
    "postgres",
    "postgresql",
    "database",
    "sql"
  ],
  "aliases": [
    "@modelcontextprotocol/server-postgres",
    "server-postgres",
    "postgres",
    "postgresql-mcp"
  ],
  "versions": [
    {
      "version": "0.6.2",
      "toolset_canonical_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
      "release_date": "2026-02-15T14:22:00Z",
      "dependencies": {
        "@modelcontextprotocol/sdk": "^1.0.1",
        "pg": "^8.11.3",
        "zod": "^3.22.4"
      },
      "connections": [
        {
          "type": "stdio",
          "command": "npx",
          "args": ["-y", "@modelcontextprotocol/server-postgres", "postgresql://localhost/mydb"]
        }
      ],
      "capabilities": {
        "tools": true,
        "prompts": false,
        "resources": true,
        "logging": true
      },
      "tool_signatures": [
        {
          "name": "query",
          "canonical_hash": "a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e",
          "description": "Execute a read-only SQL query against the connected PostgreSQL database.",
          "description_hash": "2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae",
          "is_mutating": false,
          "property_keys": [
            "query",
            "params"
          ],
          "required_keys": [
            "query"
          ],
          "parameter_types": {
            "query": "string",
            "params": "array"
          },
          "inputSchema": {
            "type": "object",
            "properties": {
              "query": {
                "type": "string",
                "description": "SQL query text (e.g. SELECT * FROM users WHERE id = $1)"
              },
              "params": {
                "type": "array",
                "items": {
                  "type": "string"
                },
                "description": "Parameterized values replacing placeholders in the query text"
              }
            },
            "required": [
              "query"
            ],
            "additionalProperties": false
          },
          "outputSchema": {
            "type": "object",
            "properties": {
              "rows": {
                "type": "array",
                "items": {
                  "type": "object"
                }
              },
              "rowCount": {
                "type": "integer"
              }
            }
          }
        },
        {
          "name": "list_tables",
          "canonical_hash": "d2a0e5b7b9f3452148b598b9e67890123456789abcdef0123456789abcdef012",
          "description": "List all schemas and tables present in the current database catalog.",
          "description_hash": "8f434346648f6b96df89dda901c5176b10a6d83961dd3c1ac88b59b2dc327aa4",
          "is_mutating": false,
          "property_keys": [
            "schema_filter"
          ],
          "required_keys": [],
          "parameter_types": {
            "schema_filter": "string"
          },
          "inputSchema": {
            "type": "object",
            "properties": {
              "schema_filter": {
                "type": "string",
                "description": "Optional PostgreSQL schema name filter (defaults to 'public')"
              }
            }
          },
          "outputSchema": null
        }
      ],
      "prompt_signatures": [],
      "resource_signatures": [
        {
          "uri": "postgres://localhost/{schema}/{table}/schema",
          "name": "Table Schema Definition",
          "description": "DDL and column metadata for the target table.",
          "mimeType": "application/json"
        }
      ]
    }
  ]
}
```

---

### 4.2 Variant B: PyPI / Python-Native MCP Passport

```json
{
  "package_name": "mcp-server-sqlite",
  "purl": "pkg:pypi/mcp-server-sqlite",
  "ecosystem": "pypi",
  "display_name": "SQLite MCP Server",
  "description": "Official Python SQLite Model Context Protocol connector.",
  "repository_url": "https://github.com/modelcontextprotocol/python-sdk",
  "homepage_url": "https://pypi.org/project/mcp-server-sqlite/",
  "license": "Apache-2.0",
  "verified": true,
  "download_count": 89000,
  "stars": 1900,
  "dist_tags": {
    "latest": "1.2.0"
  },
  "categories": [
    "database",
    "sqlite"
  ],
  "keywords": [
    "mcp",
    "sqlite"
  ],
  "aliases": [
    "mcp-server-sqlite",
    "sqlite-mcp"
  ],
  "versions": [
    {
      "version": "1.2.0",
      "toolset_canonical_hash": "4a5e2f7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f",
      "release_date": "2026-01-20T10:00:00Z",
      "dependencies": {
        "mcp": ">=1.0.0",
        "aiosqlite": ">=0.19.0"
      },
      "connections": [
        {
          "type": "stdio",
          "command": "python",
          "args": ["-m", "mcp_server_sqlite", "--db-path", "app.db"]
        }
      ],
      "capabilities": {
        "tools": true,
        "prompts": true,
        "resources": true,
        "logging": false
      },
      "tool_signatures": [
        {
          "name": "read_query",
          "canonical_hash": "f1e2d3c4b5a697887766554433221100ffeeddccbbaa99887766554433221100",
          "description": "Execute SELECT SQL queries against SQLite database.",
          "description_hash": "112233445566778899aabbccddeeff00112233445566778899aabbccddeeff00",
          "is_mutating": false,
          "property_keys": ["query"],
          "required_keys": ["query"],
          "parameter_types": {
            "query": "string"
          },
          "inputSchema": {
            "type": "object",
            "properties": {
              "query": {
                "type": "string"
              }
            },
            "required": ["query"]
          },
          "outputSchema": null
        }
      ],
      "prompt_signatures": [
        {
          "name": "analyze_table",
          "description": "Generates exploratory queries for analyzing a database table.",
          "argument_keys": ["table_name"]
        }
      ],
      "resource_signatures": [
        {
          "uri": "memo://insights",
          "name": "Database Memo Insights",
          "description": "Schema structure and usage memo.",
          "mimeType": "text/plain"
        }
      ]
    }
  ]
}
```

---

## 5. Canonical Hashing Algorithms

### 5.1 Tool Signature Canonicalization Formula
For any tool contract $T$:
1. Extract property keys and sort alphabetically: $K = \text{sort}(\text{keys}(T.\text{inputSchema}.\text{properties}))$.
2. Extract required property keys and sort alphabetically: $R = \text{sort}(T.\text{inputSchema}.\text{required})$.
3. Extract type signatures into a sorted dictionary: $P = \{k: T.\text{inputSchema}.\text{properties}[k].\text{type} \mid k \in K\}$.
4. Build canonical JSON string with zero whitespace:
   $$\text{canonical\_repr} = \text{JSON}(\{ \text{"name"}: T.\text{name}, \text{"parameter\_types"}: P, \text{"property\_keys"}: K, \text{"required\_keys"}: R \})$$
5. Compute canonical hash:
   $$\text{canonical\_hash}(T) = \text{SHA256}(\text{canonical\_repr})$$

### 5.2 Toolset Canonicalization Formula
For a collection of tools $\{T_1, T_2, \dots, T_n\}$:
1. Compute $\text{canonical\_hash}(T_i)$ for each tool.
2. Sort all hashes lexicographically: $H = \text{sort}([\text{canonical\_hash}(T_1), \dots, \text{canonical\_hash}(T_n)])$.
3. Concatenate with pipe delimiter: $\text{joined} = \text{join}(H, \text{"|"})$.
4. Compute toolset hash:
   $$\text{toolset\_canonical\_hash} = \text{SHA256}(\text{joined})$$

This mathematical structure guarantees that:
- Tool declaration order does **not** change the hash.
- Schema parameter dictionary key order does **not** change the hash.
- Any change in tool names, parameter names, parameter types, or required keys strictly produces a distinct hash.

---

## 6. What Can This Knowledge Base Serve?

1. **Autonomous MCP Firewall & Proxy Inspection**:
   - Inspects `tools/list` responses during the MCP initialization handshake.
   - Instantly looks up the passport to verify if tool schemas match certified repository builds.
   - Blocks unauthorized runtime tool additions or hidden prompts.
2. **Security Vulnerability Resolution**:
   - Correlates the resolved server and version directly to the [MCP Vulnerability Advisory Database](https://github.com/JMartynov/mcp-vulnerabilities).
3. **Supply-Chain Verification & SBOM Generation**:
   - Generates deterministic Software Bill of Materials (SBOM) for LLM agents and tools.
4. **Automated Threat Hunting**:
   - Detects tool description modifications (prompt injection staging) by comparing `description_hash` against historical baselines.
