# RAG Test Suite UI Integration Plan

## Overview

Create a web UI that allows users to configure and run the RAG Test Suite flow through a visual interface. The UI will call the CrewAI Enterprise Flow API.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (UI)                            │
│   Nuxt/Vue + Tailwind CSS                                        │
│   ├── RAG Backend Selector (ragengine / qdrant)                  │
│   ├── Configuration Forms (dynamic based on selection)           │
│   ├── Run Mode Selector                                          │
│   ├── Test Parameters                                            │
│   └── Results Dashboard                                          │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ HTTP POST
┌─────────────────────────────────────────────────────────────────┐
│                    CrewAI Enterprise API                         │
│   POST /api/v1/flows/{flow_id}/kickoff                          │
│   GET  /api/v1/flows/{flow_id}/runs/{run_id}                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    RAG Test Suite Flow                           │
│   Deployed to CrewAI Enterprise                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## API Endpoints

### 1. Kickoff Flow (Start Test Run)

**Request:**
```http
POST https://app.crewai.com/api/v1/flows/{flow_id}/kickoff
Authorization: Bearer {CREWAI_API_TOKEN}
Content-Type: application/json

{
  "inputs": {
    "RUN_MODE": "full",
    "RAG_BACKEND": "ragengine",
    "RAG_MCP_URL": "https://...",
    "RAG_MCP_TOKEN": "...",
    "RAG_CORPUS": "...",
    "TARGET_API_URL": "https://...",
    "TARGET_API_TOKEN": "...",
    "NUM_TESTS": 20,
    "CREW_DESCRIPTION": "..."
  }
}
```

**Response:**
```json
{
  "id": "run_abc123",
  "status": "pending",
  "created_at": "2026-01-12T18:00:00Z"
}
```

### 2. Poll Run Status

**Request:**
```http
GET https://app.crewai.com/api/v1/flows/{flow_id}/runs/{run_id}
Authorization: Bearer {CREWAI_API_TOKEN}
```

**Response (in progress):**
```json
{
  "id": "run_abc123",
  "status": "running",
  "progress": 45,
  "current_phase": "executing_tests"
}
```

**Response (complete):**
```json
{
  "id": "run_abc123",
  "status": "completed",
  "result": "# Quality Report\n\n## Summary\n...",
  "completed_at": "2026-01-12T18:15:00Z"
}
```

---

## UI Components

### 1. RAG Backend Selector

```vue
<template>
  <div class="rag-backend-selector">
    <h3>Select RAG Backend</h3>
    <div class="radio-group">
      <label>
        <input type="radio" v-model="backend" value="ragengine" />
        RAG Engine (MCP)
      </label>
      <label>
        <input type="radio" v-model="backend" value="qdrant" />
        Qdrant Vector Store
      </label>
    </div>
  </div>
</template>
```

### 2. Dynamic Configuration Form

**RAG Engine Fields (when backend = ragengine):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| MCP URL | URL | Yes | RAG Engine MCP server URL |
| MCP Token | Password | Yes | Bearer token for authentication |
| Corpus | Text | Yes | Corpus path (projects/xxx/locations/xxx/ragCorpora/xxx) |

**Qdrant Fields (when backend = qdrant):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Qdrant URL | URL | Yes | Qdrant server URL (https://...:6333) |
| API Key | Password | Yes | Qdrant API key |
| Collection | Text | Yes | Collection name |

### 3. Run Mode Selector

```vue
<template>
  <div class="run-mode-selector">
    <h3>Run Mode</h3>
    <select v-model="runMode">
      <option value="full">Full Test Run (Discovery → Execute → Report)</option>
      <option value="prompt_only">Prompt Suggestions Only</option>
      <option value="generate_only">Generate Tests Only (No Execution)</option>
      <option value="execute_only">Execute from CSV</option>
    </select>

    <!-- Show CSV upload if execute_only -->
    <div v-if="runMode === 'execute_only'">
      <input type="file" accept=".csv" @change="handleCsvUpload" />
    </div>
  </div>
</template>
```

### 4. Target Crew Configuration

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Target Crew URL | URL | For full/execute modes | CrewAI Enterprise kickoff URL |
| Target Crew Token | Password | For full/execute modes | Bearer token for target crew |
| Crew Description | Textarea | Recommended | What the crew does (helps test generation) |

### 5. Test Parameters

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| Number of Tests | Number | 20 | Tests to generate (5-100) |
| Pass Threshold | Slider | 0.7 | Similarity score for pass (0.5-1.0) |
| Max Retries | Number | 2 | Retries per test (0-5) |

---

## UI Flow

### Step 1: Configuration

```
┌─────────────────────────────────────────────────────────────┐
│  RAG Test Suite                                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Select RAG Backend                                      │
│     ○ RAG Engine (MCP)    ● Qdrant                          │
│                                                             │
│  2. Qdrant Configuration                                    │
│     URL:        [https://xxx.cloud.qdrant.io:6333    ]     │
│     API Key:    [••••••••••••••••                    ]     │
│     Collection: [my-knowledge-base                   ]     │
│                                                             │
│  3. Run Mode                                                │
│     [▼ Full Test Run                              ]        │
│                                                             │
│  4. Target Crew (Optional for prompt_only)                  │
│     URL:   [https://app.crewai.com/api/v1/crews/... ]     │
│     Token: [••••••••••••••••                        ]     │
│                                                             │
│  5. Test Parameters                                         │
│     Tests: [20]  Threshold: [0.7]  Retries: [2]            │
│     Description: [Customer support assistant        ]       │
│                                                             │
│  [Run Test Suite]                                           │
└─────────────────────────────────────────────────────────────┘
```

### Step 2: Running

```
┌─────────────────────────────────────────────────────────────┐
│  RAG Test Suite - Running                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ████████████░░░░░░░░░░░░░░░░░░  40%                       │
│                                                             │
│  Current Phase: Executing Tests                             │
│                                                             │
│  ✓ Phase 1: Discovery Complete                              │
│  ✓ Phase 2: Prompt Generation Complete                      │
│  ✓ Phase 3: Test Generation Complete (20 tests)             │
│  ⟳ Phase 4: Executing Tests (8/20)                          │
│  ○ Phase 5: Evaluation                                      │
│  ○ Phase 6: Report Generation                               │
│                                                             │
│  Elapsed: 2m 45s                                            │
│                                                             │
│  [Cancel]                                                   │
└─────────────────────────────────────────────────────────────┘
```

### Step 3: Results

```
┌─────────────────────────────────────────────────────────────┐
│  RAG Test Suite - Results                                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ✓ Test Run Complete                                        │
│                                                             │
│  Overall Pass Rate: 85% (17/20)                             │
│                                                             │
│  Category Breakdown:                                        │
│  ├── Factual:     90% (9/10)                                │
│  ├── Reasoning:   80% (4/5)                                 │
│  ├── Edge Cases:  75% (3/4)                                 │
│  └── Out of Scope: 100% (1/1)                               │
│                                                             │
│  [View Full Report]  [Download CSV]  [Run Again]            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Implementation Steps

### Phase 1: Backend API Wrapper (Cloud Function)

Create a Cloud Function to proxy requests and handle auth:

```python
# functions/rag-test-suite-api/main.py
import functions_framework
from flask import jsonify, request
import requests

FLOW_ID = "your-flow-id"
CREWAI_API_BASE = "https://app.crewai.com/api/v1"

@functions_framework.http
def kickoff_test_suite(request):
    """Kickoff the RAG Test Suite flow."""
    # Get CrewAI token from request or Secret Manager
    crewai_token = get_crewai_token()

    # Build inputs from request body
    data = request.get_json()
    inputs = {
        "RUN_MODE": data.get("run_mode", "full"),
        "RAG_BACKEND": data.get("rag_backend"),
        "RAG_MCP_URL": data.get("rag_mcp_url", ""),
        "RAG_MCP_TOKEN": data.get("rag_mcp_token", ""),
        "RAG_CORPUS": data.get("rag_corpus", ""),
        "RAG_QDRANT_URL": data.get("rag_qdrant_url", ""),
        "RAG_QDRANT_API_KEY": data.get("rag_qdrant_api_key", ""),
        "RAG_QDRANT_COLLECTION": data.get("rag_qdrant_collection", ""),
        "TARGET_API_URL": data.get("target_api_url", ""),
        "TARGET_API_TOKEN": data.get("target_api_token", ""),
        "NUM_TESTS": data.get("num_tests", 20),
        "CREW_DESCRIPTION": data.get("crew_description", ""),
    }

    # Call CrewAI Enterprise API
    response = requests.post(
        f"{CREWAI_API_BASE}/flows/{FLOW_ID}/kickoff",
        headers={"Authorization": f"Bearer {crewai_token}"},
        json={"inputs": inputs}
    )

    return jsonify(response.json())


@functions_framework.http
def get_run_status(request):
    """Get status of a test run."""
    run_id = request.args.get("run_id")
    crewai_token = get_crewai_token()

    response = requests.get(
        f"{CREWAI_API_BASE}/flows/{FLOW_ID}/runs/{run_id}",
        headers={"Authorization": f"Bearer {crewai_token}"}
    )

    return jsonify(response.json())
```

### Phase 2: Frontend UI (Nuxt/Vue)

```
ui/
├── pages/
│   └── test-suite.vue           # Main test suite page
├── components/
│   ├── RagBackendSelector.vue   # RAG backend radio buttons
│   ├── RagEngineForm.vue        # MCP URL/token/corpus fields
│   ├── QdrantForm.vue           # Qdrant URL/key/collection fields
│   ├── RunModeSelector.vue      # Run mode dropdown
│   ├── TargetCrewForm.vue       # Target crew URL/token
│   ├── TestParameters.vue       # Num tests, threshold, retries
│   ├── RunProgress.vue          # Progress bar + phases
│   └── ResultsDashboard.vue     # Pass rates, category breakdown
├── composables/
│   └── useTestSuite.ts          # API calls + state management
└── stores/
    └── testSuite.ts             # Pinia store for test suite state
```

### Phase 3: State Management

```typescript
// stores/testSuite.ts
export const useTestSuiteStore = defineStore('testSuite', {
  state: () => ({
    // Configuration
    ragBackend: 'ragengine' as 'ragengine' | 'qdrant',
    ragEngineConfig: { url: '', token: '', corpus: '' },
    qdrantConfig: { url: '', apiKey: '', collection: '' },
    runMode: 'full',
    targetCrew: { url: '', token: '' },
    testParams: { numTests: 20, threshold: 0.7, retries: 2 },
    crewDescription: '',

    // Run state
    currentRunId: null as string | null,
    status: 'idle' as 'idle' | 'running' | 'completed' | 'error',
    progress: 0,
    currentPhase: '',
    result: null as string | null,
  }),

  actions: {
    async kickoff() {
      this.status = 'running';
      const response = await $fetch('/api/test-suite/kickoff', {
        method: 'POST',
        body: this.buildInputs(),
      });
      this.currentRunId = response.id;
      this.pollStatus();
    },

    async pollStatus() {
      while (this.status === 'running') {
        await new Promise(r => setTimeout(r, 5000));
        const response = await $fetch(`/api/test-suite/status?run_id=${this.currentRunId}`);
        this.progress = response.progress;
        this.currentPhase = response.current_phase;
        if (response.status === 'completed') {
          this.status = 'completed';
          this.result = response.result;
        }
      }
    },

    buildInputs() {
      return {
        run_mode: this.runMode,
        rag_backend: this.ragBackend,
        ...(this.ragBackend === 'ragengine' ? {
          rag_mcp_url: this.ragEngineConfig.url,
          rag_mcp_token: this.ragEngineConfig.token,
          rag_corpus: this.ragEngineConfig.corpus,
        } : {
          rag_qdrant_url: this.qdrantConfig.url,
          rag_qdrant_api_key: this.qdrantConfig.apiKey,
          rag_qdrant_collection: this.qdrantConfig.collection,
        }),
        target_api_url: this.targetCrew.url,
        target_api_token: this.targetCrew.token,
        num_tests: this.testParams.numTests,
        crew_description: this.crewDescription,
      };
    },
  },
});
```

---

## Validation Rules

### RAG Engine
- MCP URL: Required, must be valid HTTPS URL ending in `/mcp`
- Token: Required, non-empty
- Corpus: Required, must match pattern `projects/*/locations/*/ragCorpora/*`

### Qdrant
- URL: Required, must be valid HTTPS URL with port (e.g., `:6333`)
- API Key: Required, non-empty
- Collection: Required, alphanumeric with underscores

### Target Crew
- Required for `full`, `execute_only`, `generate_and_execute` modes
- Optional for `prompt_only`, `generate_only` modes
- URL must match CrewAI Enterprise pattern

---

## Security Considerations

1. **Token Storage** — Never store tokens in frontend state; pass through to backend
2. **Backend Proxy** — All API calls go through Cloud Function (not direct to CrewAI)
3. **Token Masking** — Show only last 4 characters of tokens in UI
4. **HTTPS Only** — All URLs must be HTTPS
5. **Rate Limiting** — Limit kickoff calls per user/minute

---

## Implementation Timeline

| Phase | Task | Duration |
|-------|------|----------|
| 1 | Deploy Flow to CrewAI Enterprise | 1 day |
| 2 | Create Cloud Function API wrapper | 1 day |
| 3 | Build UI components | 2-3 days |
| 4 | Integrate API + state management | 1 day |
| 5 | Add progress polling + results display | 1 day |
| 6 | Testing + polish | 1 day |

**Total: ~7-8 days**

---

## Files to Create

```
# Backend (Cloud Function)
functions/rag-test-suite-api/
├── main.py                      # HTTP handler
├── requirements.txt             # requests, flask, etc.
└── cloudbuild.yaml              # Deployment config

# Frontend (Nuxt)
ui/rag-test-suite/
├── nuxt.config.ts
├── pages/
│   └── index.vue                # Main page
├── components/
│   ├── ConfigForm.vue           # Combined configuration form
│   ├── RunProgress.vue          # Progress display
│   └── Results.vue              # Results dashboard
├── composables/
│   └── useTestSuite.ts          # API composable
└── stores/
    └── testSuite.ts             # Pinia store
```

---

## Summary

**Yes, this approach works.** The flow already supports all configuration via API inputs:

1. **RAG Backend Selection** → `RAG_BACKEND` input (ragengine or qdrant)
2. **Dynamic Fields** → Backend-specific fields (MCP URL vs Qdrant URL)
3. **Run Modes** → `RUN_MODE` input (full, prompt_only, generate_only, execute_only)
4. **Target Crew** → `TARGET_API_URL` + `TARGET_API_TOKEN`
5. **Test Parameters** → `NUM_TESTS`, `PASS_THRESHOLD`, `CREW_DESCRIPTION`

The UI just needs to:
1. Collect user input
2. Build the inputs JSON
3. POST to CrewAI Enterprise Flow API
4. Poll for status
5. Display results
