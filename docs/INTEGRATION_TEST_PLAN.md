# CrewAI Test Suite — Integration Test Plan

*Created: January 12, 2026*

---

## Overview

This plan outlines the steps to test the rag-test-suite against a real RAG Engine MCP backend. We'll use the Market Intelligence (MI) RAG corpus as our test target.

---

## Prerequisites

### 1. Environment Variables Required

| Variable | Description | Source |
|----------|-------------|--------|
| `PG_RAG_MCP_URL` | RAG Engine MCP server URL | MI RAG server |
| `PG_RAG_TOKEN` | Bearer token for authentication | MI credentials |
| `PG_RAG_CORPUS` | Vertex AI RAG corpus path | MI corpus |
| `OPENAI_API_KEY` | LiteLLM proxy key | Konecta LiteLLM |
| `OPENAI_API_BASE` | LiteLLM proxy URL | Konecta LiteLLM |

### 2. RAG Backend Details

**Server:** `https://kon-mcp-ragengine-xzxewckhqa-ez.a.run.app`
**Corpus:** `projects/kd-lab-464110/locations/europe-west4/ragCorpora/7454583283205013504`
**Content:** Market Intelligence documents (industry reports, competitor analysis, market trends)

---

## Test Phases

### Phase 1: Verify RAG Connectivity

**Goal:** Confirm the RagQueryTool can connect and query the RAG Engine MCP.

**Steps:**
1. Create `.env` file with MI RAG credentials
2. Run a simple Python test to verify connectivity:
   ```python
   from rag_test_suite.tools.rag_query import RagQueryTool

   tool = RagQueryTool(
       backend="ragengine",
       mcp_url="https://kon-mcp-ragengine-xzxewckhqa-ez.a.run.app",
       corpus="projects/kd-lab-464110/locations/europe-west4/ragCorpora/7454583283205013504",
   )
   result = tool._run("What is BPO?")
   print(result)
   ```
3. Expected: Receive formatted search results

**Success Criteria:**
- [ ] Connection established
- [ ] Query returns results
- [ ] Results are properly formatted

---

### Phase 2: Run Discovery Mode

**Goal:** Test the Discovery Crew against the MI RAG.

**Command:**
```bash
python -m rag_test_suite.main --run-mode prompt_only
```

**Expected Output:**
1. RAG knowledge domains identified
2. Prompt suggestions generated
3. No errors in execution

**Success Criteria:**
- [ ] Discovery Crew runs successfully
- [ ] Topics extracted from RAG content
- [ ] Prompt suggestions match domain knowledge

---

### Phase 3: Generate Test Cases

**Goal:** Test the Test Generation Crew.

**Command:**
```bash
python -m rag_test_suite.main --run-mode generate_only --num-tests 5
```

**Expected Output:**
1. 5 test cases generated
2. Each test has: question, expected_answer, category, difficulty
3. Test cases saved to CSV

**Success Criteria:**
- [ ] Test cases generated
- [ ] Categories: factual, reasoning, edge_case, out_of_scope, ambiguous
- [ ] Expected answers based on RAG content

---

### Phase 4: Execute Tests (CSV Mode)

**Goal:** Test execution using pre-defined test cases.

**Steps:**
1. Create `tests/integration/mi_tests.csv` with MI-specific questions:
   ```csv
   id,question,expected_answer,category,difficulty,rationale
   MI-001,What is BPO?,Business Process Outsourcing...,factual,easy,Basic domain definition
   MI-002,What are the top CX trends for 2025?,AI integration and automation...,reasoning,medium,Market trend analysis
   ```

2. Run:
   ```bash
   python -m rag_test_suite.main \
     --run-mode execute_only \
     --test-csv tests/integration/mi_tests.csv \
     --target-api-url <MI_GURU_API_URL>
   ```

**Note:** This phase requires a deployed MI Guru crew to test against. If not available, we can test with a local crew.

**Success Criteria:**
- [ ] CSV loaded correctly
- [ ] Tests executed against target
- [ ] Results evaluated
- [ ] Report generated

---

### Phase 5: Full Cycle Test

**Goal:** Run complete test cycle (Discovery → Generation → Execution → Report).

**Command:**
```bash
python -m rag_test_suite.main \
  --run-mode full \
  --num-tests 10 \
  --crew-description "Market Intelligence assistant for BPO industry analysis" \
  --target-api-url <TARGET_CREW_URL>
```

**Success Criteria:**
- [ ] All phases complete without errors
- [ ] Report contains quality metrics
- [ ] Recommendations are actionable

---

## Test Environment Setup

### Option A: Use MI RAG with simple-rag Crew (Recommended)

1. Deploy `simple-rag` crew with MI RAG configuration
2. Set `TARGET_API_URL` to the deployed crew's kickoff URL
3. Run test suite against it

### Option B: Local Testing

1. Configure `simple-rag` locally with MI RAG
2. Set test suite to use local mode:
   ```bash
   python -m rag_test_suite.main \
     --run-mode full \
     --target-crew-path /path/to/simple-rag
   ```

---

## .env Template for Integration Testing

```bash
# LLM Configuration
OPENAI_API_KEY=sk-58992341d04ded6c9d736c79acbdd3347cf4daccd239413fde711480a0ce3558
OPENAI_API_BASE=https://litellm-proxy-805102662749.us-central1.run.app/v1

# RAG Engine (MI RAG)
PG_RAG_MCP_URL=https://kon-mcp-ragengine-xzxewckhqa-ez.a.run.app
PG_RAG_TOKEN=<MI_RAG_TOKEN>
PG_RAG_CORPUS=projects/kd-lab-464110/locations/europe-west4/ragCorpora/7454583283205013504

# Target Crew (when testing against deployed crew)
# TARGET_API_URL=https://app.crewai.com/api/v1/crews/<crew_id>/kickoff
# TARGET_API_TOKEN=<crewai_token>
```

---

## Execution Checklist

- [ ] **Phase 1:** RAG connectivity verified
- [ ] **Phase 2:** Discovery mode works
- [ ] **Phase 3:** Test generation works
- [ ] **Phase 4:** CSV execution works
- [ ] **Phase 5:** Full cycle completes

---

## Known Considerations

1. **MI RAG Content:** The MI corpus contains market intelligence documents. Test questions should be relevant to BPO/CX industry.

2. **Rate Limits:** The RAG Engine MCP may have rate limits. Space out requests if needed.

3. **Token Sensitivity:** Never commit tokens to git. Use `.env` files.

4. **Target Crew:** For execution phases, need a deployed crew. Can use:
   - `simple-rag` configured with same MI RAG
   - Any RAG-based crew deployed to CrewAI Enterprise

---

## Next Steps After Testing

1. Document findings in STATUS.md
2. Create sample test cases for MI domain
3. Update README with integration test instructions
4. Deploy test suite to CrewAI Enterprise
