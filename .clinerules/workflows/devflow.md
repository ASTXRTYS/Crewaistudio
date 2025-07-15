# workflow: devflow
# description: AUREN Development Workflow (Junior Engineer Kimi K2)

## Phase 1 – Understanding the Task
1. **Read** the Senior Engineer's guidance carefully  
2. **Identify** the core objective of the current task  
3. **Review** relevant existing code if any  
4. **Ask** clarifying questions if anything is unclear  

## Phase 2 – Planning Implementation
1. **Break down** the task into smaller components  
2. **Identify** dependencies between components  
3. **Create** a mental model of data flow  
4. **Consider** edge cases and error scenarios  

## Phase 3 – Implementation
1. **Start** with the simplest version that works  
2. **Add type hints** to all functions  
3. **Write** comprehensive docstrings with examples  
4. **Use async/await** for all database operations  
5. **Test** each component before moving to the next  

## Phase 4 – Testing & Validation
1. **Create** test data that represents real scenarios  
2. **Test** happy path first  
3. **Test** edge cases and error conditions  
4. **Verify** memory persistence (crucial for AUREN)  
5. **Check** performance with larger datasets  

## Phase 5 – Integration
1. **Connect** components following the architecture  
2. **Verify** data flow between systems  
3. **Test** the complete workflow end-to-end  
4. **Document** any assumptions or decisions made  

---

### Communication Protocol  
- **Status Updates** - every 30-45 min  
- **Blockers** - raise immediately  
- **Questions** - ask specific, technical questions  
- **Code Reviews** - request review after each major component  

### Current Task Priority Order  
1. Database Setup (PostgreSQL schema)  
2. CognitiveTwinProfile (core memory)  
3. UI Orchestrator (AUREN interface)  
4. Memory Tools  
5. Temporal RAG  
6. One Specialist (federated model PoC)  
7. Compound Memory (hypothesis testing engine)  

### Key Questions to Ask Yourself  
- Does this support long-term memory?  
- Is it personalized to the user?  
- Can it scale with growing data?  
- Does it feel natural in conversation?  
- Have I tested it thoroughly?  

### Red Flags to Watch For  
- Generic, non-personalized responses  
- Memory limited to recent interactions  
- Synchronous DB operations  
- Missing error handling  
- Untested code paths  

### Definition of Done  
- [ ] Requirement implemented fully  
- [ ] All functions have type hints  
- [ ] Comprehensive docstrings with examples  
- [ ] Error handling implemented  
- [ ] Tests written **and passing**  
- [ ] Integration verified  
- [ ] Senior Engineer has reviewed  
EOF

## Phase 6 – Reflection & Mentorship  (🔄 run after any major milestone)

1. **Self-Review**  
   – Summarise what was built (≤ 120 words).  
   – List any trade-offs or shortcuts taken.

2. **Questions for Opus 4**  
   – Prepare up to **3** specific, technical questions that would deepen understanding.  
   – Format as bullet Q&A placeholders:
     • Q1: …  • A1: ___  
     • Q2: …  • A2: ___

3. **Improvement Proposals**  
   – Suggest ≤ 2 optimisations or refactors (cite the lines or modules).  
   – Mark each with **[PROPOSAL]** so the senior engineer can grep quickly.

4. **Await Feedback**  
   – Pause execution until Opus 4 (or you) answers.  
   – If no response in 15 min, continue with default plan but log “no feedback”.