# AUREN Strategic Development Roadmap & Current Priorities

*   **Last Updated**: [Current Date]
*   **Current Phase**: Phase 1: Semantic Memory
*   **Status**: In Progress

---

## 🎯 **Executive Mandate: The Strategic Path Forward**

Based on the Executive Engineer's directive, we are moving from initial deployment to a structured, phased implementation of the full NEUROS vision. Our work is now guided by a four-phase strategic plan. We are not "behind"; we are building incrementally upon an already impressive foundation.

**The Reality Check:** NEUROS v3.1 is a functional, multi-modal agent with a solid foundation (cognitive modes, basic memory, protocol execution). The YAML profile is our North Star, not a list of failures. We are currently at Floor 4 of a 13-floor skyscraper.

---

## 🚀 **Phase 1: Semantic Memory (Current Focus)**

**Objective:** Unlock the agent's ability to understand long-term patterns and recall past interactions, making NEUROS feel significantly more intelligent. This phase is the highest impact for the least effort.

### **Deliverables & Tasks:**

*   [ ] **Infrastructure:**
    *   [ ] Integrate the `pgvector` extension into the existing PostgreSQL service.
    *   [ ] Update `docker-compose.yml` to ensure the extension is enabled.
*   [ ] **Data Pipeline:**
    *   [ ] Create an embedding pipeline using the OpenAI API.
    *   [ ] Develop a background job or a new node in the LangGraph that periodically extracts insights from conversation histories.
    *   [ ] Store the resulting text and its vector embedding in a new `semantic_memories` table in PostgreSQL.
*   [ ] **Agent Logic:**
    *   [ ] Create a new "Memory Retrieval" tool for the NEUROS agent.
    *   [ ] This tool will take a user's query, convert it to an embedding, and perform a similarity search against the `semantic_memories` table.
    *   [ ] Add a `memory_retrieval` node to the LangGraph state machine.
    *   [ ] Inject the retrieved memories into the agent's context for more insightful responses.
*   [ ] **Testing:**
    *   [ ] Create a test script to verify that memories are being created, embedded, and retrieved correctly.
    *   [ ] Add integration tests to confirm the agent can answer questions like "What did we discuss last week about my sleep?"

**Expected Outcome:** NEUROS will be able to track performance storylines, recognize patterns across time, and provide personalized insights based on a searchable life history.

---

## ⏳ **Phase 2: Complex Event Processing (Upcoming)**

**Objective:** Transform NEUROS from a reactive agent to a truly predictive and proactive system.

### **Deliverables & Tasks:**

*   [ ] **Infrastructure:**
    *   [ ] Add a stream processing service (e.g., Apache Flink or ksqlDB) to the Docker stack.
*   [ ] **Data Pipeline:**
    *   [ ] Create a new Kafka topic named `neuros_insights`.
    *   [ ] Develop CEP jobs that consume from the `biometric-events` topic, analyze patterns over time (e.g., 3-day HRV trends), and publish findings to the `neuros_insights` topic.
*   [ ] **Agent Logic:**
    *   [ ] Update the NEUROS Kafka consumer to subscribe to the `neuros_insights` topic.
    *   [ ] Modify the agent's state machine to react to these high-level patterns, not just raw events.

**Expected Outcome:** NEUROS will be able to provide predictive warnings (e.g., "Your HRV trend suggests a potential crash in the next 48 hours") and identify true biological patterns.

---

## 🧠 **Phase 3: Enhanced LangGraph Architecture (Upcoming)**

**Objective:** Evolve NEUROS from a linear responder to a recursive "thinker" capable of meta-reasoning and creative problem-solving.

### **Deliverables & Tasks:**

*   [ ] **Agent Logic:**
    *   [ ] Redesign the LangGraph with cycles and reflection nodes (e.g., a `critique_response` node).
    *   [ ] Enhance the `NEUROSState` to track confidence scores and multiple competing hypotheses.
    *   [ ] Implement a tool for creative scenario generation and an `evaluator` node to analyze the results.
    *   [ ] Add a self-critique loop to allow the agent to improve its own outputs.

**Expected Outcome:** NEUROS will be capable of meta-reasoning, creative forecasting, and more advanced problem-solving.

---

## 🤝 **Phase 4: Multi-Agent Foundation (Upcoming)**

**Objective:** Build the foundational infrastructure for future multi-agent collaboration without needing to build the other agents immediately.

### **Deliverables & Tasks:**

*   [ ] **Infrastructure:**
    *   [ ] Define a formal agent communication protocol using Kafka (e.g., a new `auren_agent_bus` topic with a defined schema).
*   [ ] **Agent Logic:**
    *   [ ] Create a "dispatcher" node within the NEUROS LangGraph.
    *   [ ] Define an abstract base class for all future AUREN specialist agents.
*   [ ] **Testing:**
    *   [ ] Develop "stub" agents for other specialists (e.g., Nutritionist) that can receive and acknowledge tasks from the dispatcher.
    *   [ ] Create integration tests for simulated multi-agent conversations.

**Expected Outcome:** The system will be ready for future specialist agents to be "plugged in" seamlessly, enabling collaborative intelligence. 