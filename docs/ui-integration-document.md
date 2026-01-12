# RAG Test Suite — UI Integration Document

*Complete Guide for Integrating RAG Test Suite into KonectaIQ Agent Marketplace*

---

## Overview

This document provides a comprehensive guide for integrating the RAG Test Suite Flow into the KonectaIQ Agent Marketplace UI (`IQ-diagram-demo`). The UI will allow users to configure RAG backends, select run modes, and execute tests through a visual interface.

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [UI Design Specifications](#2-ui-design-specifications)
3. [API Integration](#3-api-integration)
4. [Configuration Forms](#4-configuration-forms)
5. [Run Mode Workflows](#5-run-mode-workflows)
6. [Results Display](#6-results-display)
7. [Implementation Plan](#7-implementation-plan)
8. [Code Examples](#8-code-examples)

---

## 1. Architecture Overview

### System Components

```
┌─────────────────────────────────────────────────────────────────┐
│                    KonectaIQ Agent Marketplace                   │
│                    (IQ-diagram-demo/index.html)                  │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│              RAG Test Suite UI (rag-test-suite.html)             │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ RAG Backend  │  │  Run Mode    │  │  Target Crew         │   │
│  │ Selector     │  │  Selector    │  │  Configuration       │   │
│  └──────────────┘  └──────────────┘  └──────────────────────┘   │
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │              Execution Status & Results Panel              │  │
│  └────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                   Local Proxy Server (port 3000)                 │
│                      (CORS bypass for CrewAI API)                │
└─────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                  CrewAI Enterprise Flow API                      │
│        POST /api/v1/flows/{flow_id}/kickoff                      │
│        GET  /api/v1/flows/{flow_id}/tasks/{id}/status           │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **User Input** → UI form collects RAG configuration and run mode
2. **API Call** → UI sends JSON payload to proxy server
3. **Proxy** → Forwards request to CrewAI Enterprise API
4. **Flow Execution** → RAG Test Suite Flow processes the request
5. **Polling** → UI polls for status updates
6. **Results** → UI displays test results and quality report

---

## 2. UI Design Specifications

### Design System (from existing UI)

| Element | Value |
|---------|-------|
| Background | `#0d1117` (konecta-bg) |
| Card Background | `#1c2128` (konecta-card) |
| Borders | `#30363d` (konecta-border) |
| Primary Purple | `#8b5cf6` (konecta-purple) |
| Success Green | `#22c55e` (konecta-green) |
| Error Red | `#ef4444` (konecta-red) |
| Orange Accent | `#f97316` (konecta-orange) |
| Font | Inter, sans-serif |

### Page Layout Structure

```
┌────────────────────────────────────────────────────────────────────┐
│ HEADER BAR                                                          │
│ ← Back | [icon] RAG Test Suite | [LIVE badge] | Help | Reset        │
├────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │           MODE SELECTION (Initial State)                        │ │
│  │                                                                  │ │
│  │   ┌─────────────────┐    ┌─────────────────┐                    │ │
│  │   │  Quick Test     │    │  Full Analysis  │                    │ │
│  │   │  (prompt_only)  │    │  (full mode)    │                    │ │
│  │   └─────────────────┘    └─────────────────┘                    │ │
│  │                                                                  │ │
│  │   ┌─────────────────┐    ┌─────────────────┐                    │ │
│  │   │ Generate Tests  │    │ Execute CSV     │                    │ │
│  │   │ (generate_only) │    │ (execute_only)  │                    │ │
│  │   └─────────────────┘    └─────────────────┘                    │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │           CONFIGURATION FORM (After Mode Selection)             │ │
│  │                                                                  │ │
│  │   RAG Backend: [RAG Engine ▼] [Qdrant ▼]                        │ │
│  │                                                                  │ │
│  │   ── RAG Engine Config ──                                        │ │
│  │   MCP URL: [_________________________]                           │ │
│  │   MCP Token: [_________________________]                         │ │
│  │   Corpus: [_________________________]                            │ │
│  │                                                                  │ │
│  │   ── Target Crew ──                                              │ │
│  │   API URL: [_________________________]                           │ │
│  │   API Token: [_________________________]                         │ │
│  │                                                                  │ │
│  │   Crew Description: [_________________________]                  │ │
│  │   Number of Tests: [20 ▼]                                        │ │
│  │                                                                  │ │
│  │   [▶ Run Test Suite]                                             │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │           EXECUTION STATUS (During Run)                         │ │
│  │                                                                  │ │
│  │   [spinner] Running test suite...                                │ │
│  │   ✓ Discovery phase complete                                     │ │
│  │   ✓ Prompt suggestions generated                                 │ │
│  │   ○ Generating test cases...                                     │ │
│  │   ○ Executing tests                                              │ │
│  │   ○ Generating report                                            │ │
│  │                                                                  │ │
│  │   Elapsed: 45s                                                   │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │           RESULTS PANEL (After Completion)                      │ │
│  │                                                                  │ │
│  │   ✓ Test Suite Complete!                                         │ │
│  │                                                                  │ │
│  │   ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │ │
│  │   │ Tests    │ │ Passed   │ │ Failed   │ │ Pass %   │           │ │
│  │   │   20     │ │   18     │ │   2      │ │  90%     │           │ │
│  │   └──────────┘ └──────────┘ └──────────┘ └──────────┘           │ │
│  │                                                                  │ │
│  │   [Download Report] [View Test Cases] [Run Again]                │ │
│  └────────────────────────────────────────────────────────────────┘ │
│                                                                      │
└────────────────────────────────────────────────────────────────────┘
```

---

## 3. API Integration

### CrewAI Enterprise Flow API

**Base URL:** `https://app.crewai.com` (via proxy at `http://localhost:3000`)

**Flow ID:** To be determined after deployment (placeholder: `{FLOW_ID}`)

### Kickoff Endpoint

```
POST /crewai_plus/api/v1/flow/{flow_id}/kickoff
```

**Headers:**
```json
{
  "Authorization": "Bearer {CREWAI_TOKEN}",
  "Content-Type": "application/json"
}
```

**Request Body:**
```json
{
  "inputs": {
    "RUN_MODE": "full",
    "RAG_BACKEND": "ragengine",
    "RAG_MCP_URL": "https://my-rag-engine.run.app/mcp",
    "RAG_MCP_TOKEN": "rag-token",
    "RAG_CORPUS": "my-knowledge-base",
    "TARGET_API_URL": "https://app.crewai.com/api/v1/crews/123/kickoff",
    "TARGET_API_TOKEN": "target-token",
    "CREW_DESCRIPTION": "Customer support assistant",
    "NUM_TESTS": "20"
  }
}
```

**Response:**
```json
{
  "kickoff_id": "abc123-task-id"
}
```

### Status Polling Endpoint

```
GET /crewai_plus/api/v1/flow/{flow_id}/tasks/{kickoff_id}/status
```

**Response (Pending):**
```json
{
  "state": "PENDING",
  "status": "Processing..."
}
```

**Response (Success):**
```json
{
  "state": "SUCCESS",
  "result": "## RAG Test Suite Quality Report\n\n..."
}
```

---

## 4. Configuration Forms

### RAG Backend Selection

The UI should display different form fields based on the selected RAG backend:

#### RAG Engine (MCP) Configuration

| Field | Input Type | Required | Placeholder |
|-------|------------|----------|-------------|
| MCP URL | text | Yes | `https://my-rag-engine.run.app/mcp` |
| MCP Token | password | Yes | `Bearer token for MCP` |
| Corpus | text | Yes | `my-knowledge-base` |

#### Qdrant Configuration

| Field | Input Type | Required | Placeholder |
|-------|------------|----------|-------------|
| Qdrant URL | text | Yes | `https://my-qdrant.cloud.qdrant.io:6333` |
| API Key | password | Yes | `Qdrant API key` |
| Collection | text | Yes | `my-collection` |

### Target Crew Configuration

| Field | Input Type | Required | Placeholder |
|-------|------------|----------|-------------|
| API URL | text | Yes* | `https://app.crewai.com/api/v1/crews/123/kickoff` |
| API Token | password | Yes* | `Bearer token for target crew` |
| Description | textarea | No | `Describe what this crew does...` |

*Required only for `full` and `execute_only` modes.

### Test Configuration

| Field | Input Type | Required | Default |
|-------|------------|----------|---------|
| Number of Tests | select | No | 20 |
| Test CSV (execute_only) | file | For execute_only | — |

**Number of Tests Options:** 5, 10, 15, 20, 25, 30, 50

---

## 5. Run Mode Workflows

### Mode Cards Description

| Mode | Icon | Title | Description | Estimated Time |
|------|------|-------|-------------|----------------|
| `prompt_only` | `fas fa-lightbulb` | Quick Analysis | Discover RAG content and get agent configuration suggestions | ~30s |
| `generate_only` | `fas fa-file-alt` | Generate Tests | Create test cases without execution | ~1 min |
| `full` | `fas fa-play-circle` | Full Analysis | Complete test cycle: discover → generate → execute → report | ~3–5 min |
| `execute_only` | `fas fa-upload` | Execute CSV | Run tests from uploaded CSV file | ~2–3 min |

### Mode-Specific Form Requirements

#### prompt_only Mode
- RAG Backend configuration (required)
- Crew Description (optional)
- **No target crew needed**
- **No NUM_TESTS needed**

#### generate_only Mode
- RAG Backend configuration (required)
- Crew Description (optional)
- Number of Tests (required)
- **No target crew needed**

#### full Mode
- RAG Backend configuration (required)
- Target Crew configuration (required)
- Crew Description (optional)
- Number of Tests (required)

#### execute_only Mode
- RAG Backend configuration (required)
- Target Crew configuration (required)
- CSV File Upload (required)
- **No NUM_TESTS needed** (count from CSV)

---

## 6. Results Display

### Result Types by Mode

#### prompt_only Results
Display agent configuration suggestions:
```
┌────────────────────────────────────────────────────────────────┐
│ ✓ Discovery Complete!                                          │
│                                                                 │
│ Suggested Agent Configuration:                                  │
│                                                                 │
│ Agent Name: Customer Experience Strategist                      │
│                                                                 │
│ System Prompt:                                                  │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ You are an AI assistant specialized in customer experience  ││
│ │ and CXM (Customer Experience Management)...                 ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│ Knowledge Domains:                                              │
│ • CXM and Contact Center                                        │
│ • Data & AI                                                     │
│ • Competitive Insights                                          │
│                                                                 │
│ [Copy System Prompt] [Start Over]                               │
└────────────────────────────────────────────────────────────────┘
```

#### generate_only Results
Display generated test cases:
```
┌────────────────────────────────────────────────────────────────┐
│ ✓ Test Cases Generated!                                         │
│                                                                 │
│ Generated 20 test cases across 4 categories:                    │
│                                                                 │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│ │ Factual  │ │ Reasoning│ │ Ambiguous│ │ Out-of-  │            │
│ │    8     │ │    5     │ │    4     │ │ Scope: 3 │            │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘            │
│                                                                 │
│ Sample Test Cases:                                              │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ TEST-001 (factual/easy)                                     ││
│ │ Q: What is composable customer service?                     ││
│ │ Expected: Composable customer service is...                 ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│ [Download CSV] [Run These Tests] [Start Over]                   │
└────────────────────────────────────────────────────────────────┘
```

#### full / execute_only Results
Display quality report:
```
┌────────────────────────────────────────────────────────────────┐
│ ✓ Test Suite Complete!                                          │
│                                                                 │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐            │
│ │ Total    │ │ Passed   │ │ Failed   │ │ Pass %   │            │
│ │   20     │ │   18     │ │   2      │ │  90%     │            │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘            │
│                                                                 │
│ Score Distribution:                                             │
│ █████████████████████░░░░ 4.2 / 5.0                             │
│                                                                 │
│ Category Breakdown:                                             │
│ • Factual: 8/8 (100%)                                           │
│ • Reasoning: 4/5 (80%)                                          │
│ • Ambiguous: 3/4 (75%)                                          │
│ • Out-of-scope: 3/3 (100%)                                      │
│                                                                 │
│ Quality Report Preview:                                         │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ ## Executive Summary                                        ││
│ │ The RAG-based assistant demonstrates strong performance...  ││
│ └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│ [Download Full Report] [View Failed Tests] [Run Again]          │
└────────────────────────────────────────────────────────────────┘
```

---

## 7. Implementation Plan

### Phase 1: Basic UI Structure

1. Create `rag-test-suite.html` following existing UI patterns
2. Add card to `index.html` marketplace
3. Implement mode selection cards
4. Create placeholder configuration forms

### Phase 2: Configuration Forms

1. Implement RAG backend toggle (RAG Engine / Qdrant)
2. Create dynamic form fields based on backend selection
3. Add target crew configuration section
4. Implement form validation

### Phase 3: API Integration

1. Set up API configuration (flow ID, token)
2. Implement kickoff function
3. Implement status polling
4. Add progress indicators

### Phase 4: Results Display

1. Parse flow results (markdown report)
2. Create results cards with metrics
3. Implement download functionality
4. Add "run again" workflow

### Phase 5: Polish & Testing

1. Error handling and user feedback
2. Loading states and animations
3. Mobile responsiveness
4. Integration testing with live flow

---

## 8. Code Examples

### Marketplace Card (index.html)

Add this card to the agent grid in `index.html`:

```html
<!-- RAG Test Suite Card -->
<a href="rag-test-suite.html" class="block">
    <div class="card-hover bg-konecta-card border border-konecta-border rounded-2xl p-6 h-full">
        <div class="flex items-start gap-4 mb-4">
            <div class="w-14 h-14 rounded-xl bg-gradient-to-br from-orange-600 to-red-500 flex items-center justify-center flex-shrink-0">
                <i class="fas fa-vial text-white text-2xl"></i>
            </div>
            <div class="flex-1">
                <div class="flex items-center gap-2 mb-1">
                    <h3 class="text-xl font-bold text-white">RAG Test Suite</h3>
                    <span class="px-2 py-0.5 rounded-md bg-konecta-green/20 border border-konecta-green/30 text-konecta-green text-xs font-medium">LIVE</span>
                </div>
                <p class="text-konecta-gray-400 text-sm">Automated RAG quality testing</p>
            </div>
        </div>
        <p class="text-konecta-gray-300 text-sm mb-4">
            Test your RAG-based crews automatically. Discover knowledge domains, generate test cases,
            and get quality reports with pass/fail metrics.
        </p>
        <div class="flex flex-wrap gap-2 mb-4">
            <span class="px-2.5 py-1 rounded-lg bg-konecta-bg text-konecta-gray-300 text-xs">RAG Engine</span>
            <span class="px-2.5 py-1 rounded-lg bg-konecta-bg text-konecta-gray-300 text-xs">Qdrant</span>
            <span class="px-2.5 py-1 rounded-lg bg-konecta-bg text-konecta-gray-300 text-xs">Quality Reports</span>
            <span class="px-2.5 py-1 rounded-lg bg-konecta-bg text-konecta-gray-300 text-xs">CSV Export</span>
        </div>
        <div class="flex items-center justify-between pt-4 border-t border-konecta-border">
            <div class="flex items-center gap-2 text-konecta-gray-400 text-sm">
                <i class="fas fa-robot"></i>
                <span>5 crews</span>
            </div>
            <div class="flex items-center gap-2 text-konecta-purple font-medium text-sm">
                <span>Launch Agent</span>
                <i class="fas fa-arrow-right"></i>
            </div>
        </div>
    </div>
</a>
```

### API Configuration

```javascript
// Configuration
const config = {
    apiUrl: 'http://localhost:3000',  // Proxy server
    flowId: 'YOUR_FLOW_ID_HERE',      // RAG Test Suite Flow ID
    token: 'YOUR_CREWAI_TOKEN',       // CrewAI Enterprise token
};
```

### Kickoff Function

```javascript
async function kickoffTestSuite(inputs) {
    const url = `${config.apiUrl}/crewai_plus/api/v1/flow/${config.flowId}/kickoff`;

    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${config.token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ inputs })
    });

    if (!response.ok) {
        const text = await response.text();
        throw new Error(`Kickoff failed (${response.status}): ${text}`);
    }

    return await response.json();
}
```

### Polling Function

```javascript
async function pollForStatus(kickoffId, onProgress) {
    const pollInterval = 3000; // 3 seconds

    while (true) {
        await sleep(pollInterval);

        const url = `${config.apiUrl}/crewai_plus/api/v1/flow/${config.flowId}/tasks/${kickoffId}/status`;

        const response = await fetch(url, {
            headers: { 'Authorization': `Bearer ${config.token}` }
        });

        const status = await response.json();

        if (status.state === 'SUCCESS') {
            return status;
        } else if (status.state === 'FAILURE' || status.state === 'REVOKED') {
            throw new Error(`Test suite failed: ${status.error || status.status}`);
        }

        // Update progress
        if (onProgress) {
            onProgress(status);
        }
    }
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
```

### Form Data Collection

```javascript
function collectFormData() {
    const runMode = currentMode; // 'prompt_only', 'generate_only', 'full', 'execute_only'
    const ragBackend = document.getElementById('rag-backend').value;

    const inputs = {
        RUN_MODE: runMode
    };

    // RAG Backend configuration
    if (ragBackend === 'ragengine') {
        inputs.RAG_BACKEND = 'ragengine';
        inputs.RAG_MCP_URL = document.getElementById('mcp-url').value;
        inputs.RAG_MCP_TOKEN = document.getElementById('mcp-token').value;
        inputs.RAG_CORPUS = document.getElementById('corpus').value;
    } else {
        inputs.RAG_BACKEND = 'qdrant';
        inputs.RAG_QDRANT_URL = document.getElementById('qdrant-url').value;
        inputs.RAG_QDRANT_API_KEY = document.getElementById('qdrant-key').value;
        inputs.RAG_QDRANT_COLLECTION = document.getElementById('qdrant-collection').value;
    }

    // Target crew (for full and execute_only modes)
    if (runMode === 'full' || runMode === 'execute_only') {
        inputs.TARGET_API_URL = document.getElementById('target-url').value;
        inputs.TARGET_API_TOKEN = document.getElementById('target-token').value;
    }

    // Optional fields
    const description = document.getElementById('crew-description').value;
    if (description) {
        inputs.CREW_DESCRIPTION = description;
    }

    // Number of tests (for generate_only and full modes)
    if (runMode === 'generate_only' || runMode === 'full') {
        inputs.NUM_TESTS = document.getElementById('num-tests').value;
    }

    return inputs;
}
```

### Results Parsing

```javascript
function parseResults(result) {
    // Extract markdown report
    const report = result.result || '';

    // Parse metrics from report (example patterns)
    const metrics = {
        total: 0,
        passed: 0,
        failed: 0,
        passRate: 0
    };

    // Look for patterns like "Total Tests: 20"
    const totalMatch = report.match(/Total Tests?:\s*(\d+)/i);
    if (totalMatch) metrics.total = parseInt(totalMatch[1]);

    const passedMatch = report.match(/Passed:\s*(\d+)/i);
    if (passedMatch) metrics.passed = parseInt(passedMatch[1]);

    const failedMatch = report.match(/Failed:\s*(\d+)/i);
    if (failedMatch) metrics.failed = parseInt(failedMatch[1]);

    if (metrics.total > 0) {
        metrics.passRate = Math.round((metrics.passed / metrics.total) * 100);
    }

    return { report, metrics };
}
```

---

## Appendix: File Locations

| File | Purpose |
|------|---------|
| `/demo/IQ-diagram-demo/index.html` | Marketplace home page |
| `/demo/IQ-diagram-demo/rag-test-suite.html` | RAG Test Suite UI (to create) |
| `/demo/IQ-diagram-demo/proxy-server.js` | CORS proxy server |
| `/code/Crews/flows/rag-test-suite/` | RAG Test Suite Flow source |

---

## Appendix: Environment Variables

### CrewAI Studio (Required)

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | LiteLLM proxy API key |
| `OPENAI_API_BASE` | LiteLLM proxy URL |

### Runtime API Inputs

All other configuration is passed at runtime via API inputs:

| Input | Example |
|-------|---------|
| `RUN_MODE` | `full` |
| `RAG_BACKEND` | `ragengine` or `qdrant` |
| `RAG_MCP_URL` | `https://...` |
| `RAG_MCP_TOKEN` | `token` |
| `RAG_CORPUS` | `corpus-name` |
| `RAG_QDRANT_URL` | `https://...` |
| `RAG_QDRANT_API_KEY` | `key` |
| `RAG_QDRANT_COLLECTION` | `collection` |
| `TARGET_API_URL` | `https://...` |
| `TARGET_API_TOKEN` | `token` |
| `CREW_DESCRIPTION` | `description` |
| `NUM_TESTS` | `20` |

---

*Document Version: 1.0*
*Last Updated: January 2026*
