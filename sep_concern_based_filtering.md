# Proposal: Concern-Based Filtering System

## Abstract

The MCP protocol currently provides primitives (Tools, Prompts, Resources, Tasks) that enable servers to expose capabilities to clients. However, as the number of available primitives grows, clients face "Context Overflow" – an overwhelming number of options that makes it difficult to select the most appropriate tools for a given task.

While technical organization mechanisms like grouping can help developers structure primitives, they do not address the fundamental need for **user‑centric filtering**. Users and MCP Hosts need to express their requirements in natural, domain‑oriented terms (e.g., "high security", "low cost", "production‑ready") rather than navigating technical categories.

This proposal introduces a **Concern‑Based Filtering System** that allows:
1. MCP servers to declare a set of available **Concerns** (e.g., security, cost, performance, data‑privacy).
2. MCP hosts to configure their preferences for those Concerns.
3. MCP servers to return a subset of primitives (such as Tools, Resources, Prompts, and Tasks) that match the configured Concerns.

This approach complements existing technical‑organization proposals (e.g., Group primitive) by providing a higher‑level, user‑oriented filtering layer that is intuitive for end‑users while remaining flexible and extensible for server implementers.

## Motivation

### The Context Overflow Problem
As MCP ecosystems grow, a single server may expose dozens or hundreds of primitives. Clients (especially AI agents) must sift through this large set to choose the right tool for a given context. Without a filtering mechanism that aligns with user intent, the cognitive load increases, leading to suboptimal tool selection or inefficient use of context window.

### User‑Centric vs. Developer‑Centric Organization
Existing proposals focus on **developer‑centric organization** – grouping primitives by technical categories, namespace hierarchies, or functional similarity. While valuable for server‑side structure, these groupings do not directly translate to user needs. For example, a user who cares about "security" and "cost" should not need to understand which internal groups correspond to those concerns.

### Minimal Protocol Impact
A key design goal is to keep protocol changes minimal and backward‑compatible. The Concern‑Based Filtering System integrates with the existing MCP lifecycle through optional extensions:

- **Seamless Initialization Integration**: Concern declaration and configuration are embedded within the existing `initialize` request/response flow, avoiding additional round‑trips.
- **Optional Concern Fields**: Concerns are expressed via optional fields in server capabilities, primitive schemas, and client preferences, preserving compatibility with existing implementations.
- **Gradual Adoption**: Servers and clients can adopt Concerns incrementally; non‑aware components continue to function normally with full primitive visibility.

This approach ensures that the filtering system enhances the protocol without disrupting established workflows or requiring immediate ecosystem‑wide upgrades.

## Specification

### Overview
The Concern‑Based Filtering System operates in three phases:

1. **Concern Declaration** – The server advertises which Concerns it supports, along with possible values/levels for each Concern.
2. **Concern Configuration** – The host (or user) sets preferences for the advertised Concerns.
3. **Dynamic Subset Generation** – The server filters its available primitives (such as Tools, Resources, Prompts, and Tasks) based on the configured Concerns and returns the matching subset.

### Concern Declaration
Concerns can be declared through the MCP lifecycle's **Initialization phase**, integrating seamlessly with the existing protocol flow.

#### Option A: Initialization Extension
During the `initialize` request/response exchange, the server may include an optional `concerns` field within the `capabilities` object:

```json
// Server's initialize response
{
  "serverInfo": {
    "name": "example-server",
    "version": "1.0.0"
  },
  "capabilities": {
    // ... existing capabilities ...
    "concerns": [
      {
        "name": "security",
        "description": "Security level required for the operation",
        "values": ["high", "medium", "low"],
        "default": "medium"
      },
      {
        "name": "cost",
        "description": "Estimated cost impact of using this primitive",
        "values": ["minimal", "moderate", "high"],
        "default": "moderate"
      }
    ]
  }
}
```

#### Option B: Dedicated `listConcerns` Method (Fallback)
For servers that prefer dynamic concern discovery or need to update Concerns after initialization, an optional `listConcerns()` method can be provided. This method returns the same Concern definitions as above.

#### Concern Definition
Each Concern is defined as:

```json
{
  "name": "security",
  "description": "Security level required for the operation",
  "values": ["high", "medium", "low"],
  "default": "medium"
}
```

- `name`: A unique identifier for the Concern (e.g., "security", "cost", "performance").
- `description`: Human‑readable explanation of what this Concern represents.
- `values`: An array of possible values/levels for this Concern. May be an enumerated set or a range.
- `default`: The default value if the host does not explicitly configure this Concern.

Servers may declare multiple Concerns. The set of Concerns is static for a given server version but may change across versions. The Initialization‑based approach (Option A) is preferred as it aligns with the MCP lifecycle and reduces round‑trips.

### Concern Configuration
Concern preferences can be communicated through multiple channels, with the **post‑initialization phase** being the primary recommended approach.

#### Option A: Initialized Notification Extension
After receiving the server's `initialize` response (which contains the server's declared Concerns), the host includes an optional `concerns` field in the `initialized` notification:

```json
// Host's initialized notification
{
  "concerns": {
    "security": "high",
    "cost": "minimal",
    "performance": "balanced"
  }
}
```

This timing ensures the host knows which Concerns the server supports before providing its preferences.

#### Option B: Dynamic Update via `updateConcerns`
After the session is established, the host can update its Concern configuration at any time using the optional `updateConcerns(config)` method (see "New Protocol Methods" below).

#### Option C: Initialization Request with Pre‑known Concerns
If the host already knows the server's Concerns (e.g., from a previous session, documentation, or discovery), it may include `concerns` in the `initialize` request. This is an advanced use case and not the default recommendation.

#### Option D: Host‑Side Preference Storage
The host may store Concern preferences per‑user or per‑session and apply them transparently when communicating with the server. This is an implementation detail outside the protocol.

#### Configuration Format
The configuration is a simple object mapping Concern names to desired values:

```json
{
  "security": "high",
  "cost": "minimal",
  "performance": "balanced"
}
```

Any Concern not explicitly configured uses the server‑declared default value. If the host configures a Concern that the server does not declare, that entry is ignored (or may trigger a warning).

#### Timing and Precedence
1. **Initialized‑notification configuration** (Option A) is applied first if present.
2. **Dynamic updates** (Option B) override previous settings.
3. The server uses the most recent configuration for all subsequent primitive listings.

This design ensures Concerns can be configured with full knowledge of server capabilities, while maintaining flexibility for runtime adjustments.

### Filtering Mechanism
When the host issues a request for primitives (e.g., `listTools`, `listResources`, `listPrompts`, `listTasks`), the server uses the current Concern configuration to filter the returned set. The filtering applies to all primitives that support Concerns, including Tools, Resources, Prompts, and Tasks.

The server maintains an internal mapping that associates each primitive with Concern values. This mapping is an implementation detail of the server and is not exposed in the protocol. For example, a server might have a configuration file or code that maps primitive names to Concern values:

```json
{
  "encryptData": {"security": "high", "cost": "minimal"},
  "logData": {"security": "medium"},
  "validateData": {}
}
```

When the host provides a Concern configuration, the server filters its primitives based on this internal mapping. If a primitive has no mapping for a given Concern, it is assumed to match **all** values of that Concern (i.e., it is Concern‑agnostic). If a primitive has a mapping for a Concern, it is included only when the host’s configured value matches.

**Filtering rule**: A primitive is included if for every Concern configured by the host, the primitive’s mapped Concern value (if any) matches the host’s configured value. Concerns not configured by the host are ignored.

### Implementation Flexibility
The server may choose how to associate Concern values with primitives. Two common approaches are:

1. **Internal Mapping**: The server maintains a separate mapping (e.g., configuration file, code map) that links primitive names to Concern values. This approach does not modify the primitive schemas and is entirely internal to the server.

2. **Optional Field in `_meta`**: For servers that prefer to embed Concern information directly in primitive schemas, an optional `concerns` field can be placed inside the existing `_meta` property:

   ```json
   {
     "name": "encryptData",
     "_meta": {
       "concerns": {
         "security": "high",
         "cost": "minimal"
       }
     }
   }
   ```

   This allows Concern‑aware clients to inspect the field for debugging or UI purposes, while non‑aware clients ignore it.

The first approach (internal mapping) is recommended as it keeps the protocol unchanged and delegates filtering logic entirely to the server. The second approach provides additional transparency but requires modifying primitive schemas.

### New Protocol Methods (Optional)
For richer interaction, two optional methods can be added:

#### `listConcerns()`
Returns the server’s declared Concerns and their possible values, identical to the `concerns` array that may be provided during initialization. This method allows hosts to discover Concerns dynamically if they were not provided during initialization.

#### `updateConcerns(config)`
Dynamically updates the host’s Concern configuration. This method enables runtime adjustment of filtering preferences without re‑initializing the session.

**Request**:
```json
{
  "concerns": {
    "security": "high",
    "cost": "moderate"
  }
}
```

**Response**: The server acknowledges the update with a success response. The new configuration takes effect immediately for all subsequent primitive listings (e.g., `listTools`, `listResources`, `listPrompts`, `listTasks`).

**Behavior**:
- Partial updates are allowed: only the Concerns included in the request are updated; others retain their previous values (or default if never set).
- If a Concern value is not recognized by the server, the server may ignore that entry or return an error (implementation‑specific).
- The method is idempotent: sending the same configuration multiple times has the same effect as sending it once.
- If the server does not implement this method, the host can still communicate Concern changes through other extension mechanisms (e.g., re‑initialization or out‑of‑band configuration).

**Error Handling**:
- If the configuration is malformed (e.g., not an object), the server returns a standard MCP error.
- If a Concern value is outside the declared `values` range, the server may either clamp to the nearest valid value, ignore the entry, or return an error.

If these methods are not implemented, the Concern configuration can be communicated via existing extension mechanisms (e.g., initialization options or host‑to‑server messages).

## Rationale

### Why Concerns Instead of Just Groups?
Groups provide a technical, server‑side organization mechanism. Concerns provide a **user‑intent‑based** filtering layer. The two are complementary:
- **Groups** help developers structure primitives internally (e.g., by functional area, by namespace).
- **Concerns** help users express what they care about (e.g., "I want secure and cheap tools").

A server may implement Groups internally to manage its primitives, then map those Groups to Concerns for user‑friendly filtering. This separation of concerns (pun intended) keeps the protocol flexible.

### Minimal Protocol Changes
The proposal requires only:
1. Adding an optional `concerns` declaration in the server's initialization response (within the `capabilities` object).
2. Defining a simple filtering rule that servers can implement optionally, using internal mapping as described in the Implementation Flexibility section.
3. No changes to existing primitive schemas are required.

No changes are required to existing RPC messages, and clients that ignore the `concerns` field continue to work as before.

### Extensibility
New Concerns can be added over time without breaking existing clients or servers. Servers can adopt Concerns incrementally – starting with a few well‑known Concerns (security, cost) and adding more as needed.

Concerns can also be combined with other filtering mechanisms (tags, groups, search keywords) to create a powerful, multi‑layered filtering system.

### Example Workflow
This example demonstrates the complete flow using the **Initialization‑phase integration** with proper timing:

1. **Server declares Concerns during initialization**:
   ```json
   // Server's initialize response
   {
     "serverInfo": { "name": "data‑processor", "version": "2.0.0" },
     "capabilities": {
       "tools": {},
       "concerns": [
         {
           "name": "security",
           "description": "Security level required",
           "values": ["high", "medium", "low"],
           "default": "medium"
         },
         {
           "name": "cost",
           "description": "Cost impact",
           "values": ["minimal", "moderate", "high"],
           "default": "moderate"
         }
       ]
     }
   }
   ```

2. **Host configures Concerns in initialized notification** (after receiving server's Concerns):
   ```json
   // Host's initialized notification
   {
     "concerns": {
       "security": "high",
       "cost": "minimal"
     }
   }
   ```

3. **Server filters Tools when listing** (using its internal mapping):
   - Tool A (encryptData) is mapped to `{"security": "high", "cost": "minimal"}` → included.
   - Tool B (logData) is mapped to `{"security": "medium"}` → excluded (security mismatch).
   - Tool C (validateData) has no mapping for security or cost → included (treated as matching all values).

4. **Host receives filtered `listTools` response** containing only tools that match high security and minimal cost requirements.

**Dynamic update scenario**:
- Later, the host decides to relax cost constraints and calls `updateConcerns({"security": "high", "cost": "moderate"})`.
- The server immediately applies the new configuration, and subsequent `listTools` calls include tools with `"cost": "moderate"` (or no cost concern).

This workflow shows how Concerns integrate naturally with the MCP lifecycle while ensuring the host has full knowledge of server capabilities before providing preferences.

## Backward Compatibility

### Clients
- Clients that do not support Concerns will ignore the `concerns` fields and receive the full set of primitives (current behavior).
- Clients that support Concerns can use them to reduce context overflow and improve tool selection.

### Servers
- Servers that do not implement Concerns simply omit the `concerns` fields; everything works as today.
- Servers that implement Concerns can do so optionally; they may still expose all primitives to non‑Concern‑aware clients.

### Protocol
No existing RPC methods are changed or removed. New optional methods (`listConcerns`, `updateConcerns`) are introduced only if needed. The primary mechanism is adding an optional `concerns` field within the `capabilities` object during initialization, which is already designed for optional, backward‑compatible enhancements.

## Security Implications

### Information Disclosure
Declaring Concerns may reveal information about server capabilities (e.g., that the server has tools with different security levels). This is similar to existing metadata (tool descriptions) and is not considered a new risk.

### Filtering Bypass
A malicious client could ignore Concern filtering and attempt to access primitives that do not match its configured Concerns. This is no different from today’s behavior, where clients can call any tool they discover. Concern filtering is a **recommendation/optimization** layer, not an access‑control mechanism. Proper access control should be implemented separately (e.g., via authentication and authorization).

### Server‑Side Implementation
Servers must ensure that Concern filtering is implemented correctly and does not introduce bugs that inadvertently hide critical primitives. Testing and validation are required, as with any new feature.

## Reference Implementation

A reference implementation will be provided in a separate repository. The implementation will demonstrate:

1. Extending an existing MCP server (e.g., a file‑system server) to declare Concerns.
2. Implementing an internal mapping that associates primitives (e.g., Tools, Resources, and Tasks) with Concern values.
3. Filtering the `listTools` and `listTasks` responses based on host‑provided Concern configuration.
4. A simple client that configures Concerns and displays the filtered primitives.

The implementation will showcase both the internal‑mapping approach and the optional `_meta.concerns` field for transparency.

## Next Steps

1. **Community feedback** – Discuss this proposal in the MCP community forum to gather use cases and refine the specification.
2. **Prototype implementation** – Build the reference implementation and test with real‑world servers and clients.
3. **Integration with Group primitive** – Explore how Concerns and Groups can work together (e.g., mapping Groups to Concerns for easier server‑side management).
4. **Standardization** – Submit a formal SEP through the MCP SEP process once the design is stable.

## Acknowledgements

Thanks to the MCP community for the ongoing discussion about tool filtering and context management. Special thanks to Scott Lewis for the Group primitive proposal that sparked this complementary idea.
