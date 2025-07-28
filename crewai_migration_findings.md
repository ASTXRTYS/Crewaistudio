# CrewAI → LangGraph Migration Investigation Report
Generated: Mon Jul 28 10:05:53 EDT 2025

## 1. CrewAI Dependencies Check

### Requirements Files:
✅ FOUND: CrewAI in requirements.txt
crewai>=0.55.2

✅ FOUND: CrewAI in setup.py
        "crewai>=0.8.0",

### Docker Container Dependencies:

## 2. CrewAI Code Artifacts

### CrewAI Import/Usage Patterns:
✅ FOUND files with 'from crewai import':
./venv_new/lib/python3.11/site-packages/crewai/cli/templates/pipeline/crews/research_crew/research_crew.py
./venv_new/lib/python3.11/site-packages/crewai/cli/templates/pipeline/crews/write_linkedin_crew/write_linkedin_crew.py
./venv_new/lib/python3.11/site-packages/crewai/cli/templates/pipeline/crews/write_x_crew/write_x_crew.py
./venv_new/lib/python3.11/site-packages/crewai/cli/templates/pipeline/pipelines/pipeline.py
./venv_new/lib/python3.11/site-packages/crewai/cli/templates/pipeline_router/crews/urgent_crew/urgent_crew.py
./venv_new/lib/python3.11/site-packages/crewai/cli/templates/pipeline_router/crews/classifier_crew/classifier_crew.py
./venv_new/lib/python3.11/site-packages/crewai/cli/templates/pipeline_router/crews/normal_crew/normal_crew.py
./venv_new/lib/python3.11/site-packages/crewai/cli/templates/pipeline_router/pipelines/pipeline_classifier.py
./venv_new/lib/python3.11/site-packages/crewai/cli/templates/pipeline_router/pipelines/pipeline_urgent.py
./venv_new/lib/python3.11/site-packages/crewai/cli/templates/pipeline_router/pipelines/pipeline_normal.py
./venv_new/lib/python3.11/site-packages/crewai/cli/templates/crew/crew.py
./auren/core/streaming/crewai_instrumentation.py
./auren/realtime/crewai_instrumentation.py
./auren/data_layer/crewai_integration.py
./auren/src/agents/neuroscientist.py
./auren/src/agents/specialists/neuroscientist.py
./auren/src/agents/ui_orchestrator.py
./auren/src/rag/agentic_rag.py
./agents/my_agent.py
./.venv/lib/python3.11/site-packages/crewai/experimental/evaluation/experiment/runner.py
./.venv/lib/python3.11/site-packages/crewai/experimental/evaluation/testing.py
./.venv/lib/python3.11/site-packages/crewai/cli/templates/crew/crew.py
./.venv/lib/python3.11/site-packages/crewai/cli/templates/flow/crews/poem_crew/poem_crew.py
./.venv/lib/python3.11/site-packages/crewai/project/annotations.py
./src/auren/crews/whatsapp_crew.py
./src/auren/app/app/my_task.py
./src/auren/app/app/pg_export_crew.py
./src/auren/app/app/utils.py
./src/auren/app/app/llms.py
./src/auren/app/app/pg_crew_run.py
./src/auren/app/my_task.py
./src/auren/app/pg_export_crew.py
./src/auren/app/utils.py
./src/auren/app/llms.py
./src/auren/app/pg_crew_run.py
./src/auren/agents/whatsapp_message_handler.py
./src/auren/agents/my_agent.py

Context:
File: ./venv_new/lib/python3.11/site-packages/crewai/cli/templates/pipeline/crews/research_crew/research_crew.py
1-from pydantic import BaseModel
2:from crewai import Agent, Crew, Process, Task
3-from crewai.project import CrewBase, agent, crew, task
4-
---
File: ./venv_new/lib/python3.11/site-packages/crewai/cli/templates/pipeline/crews/write_linkedin_crew/write_linkedin_crew.py
1:from crewai import Agent, Crew, Process, Task
2-from crewai.project import CrewBase, agent, crew, task
3-
---
File: ./venv_new/lib/python3.11/site-packages/crewai/cli/templates/pipeline/crews/write_x_crew/write_x_crew.py
1:from crewai import Agent, Crew, Process, Task
2-from crewai.project import CrewBase, agent, crew, task
3-
---
File: ./venv_new/lib/python3.11/site-packages/crewai/cli/templates/pipeline/pipelines/pipeline.py
28-
29-# Common imports for both examples
30:from crewai import Pipeline
31-
32-
---
File: ./venv_new/lib/python3.11/site-packages/crewai/cli/templates/pipeline_router/crews/urgent_crew/urgent_crew.py
1:from crewai import Agent, Crew, Process, Task
2-from crewai.project import CrewBase, agent, crew, task
3-
---
File: ./venv_new/lib/python3.11/site-packages/crewai/cli/templates/pipeline_router/crews/classifier_crew/classifier_crew.py
1:from crewai import Agent, Crew, Process, Task
2-from crewai.project import CrewBase, agent, crew, task
3-from pydantic import BaseModel
---
File: ./venv_new/lib/python3.11/site-packages/crewai/cli/templates/pipeline_router/crews/normal_crew/normal_crew.py
1:from crewai import Agent, Crew, Process, Task
2-from crewai.project import CrewBase, agent, crew, task
3-
---
File: ./venv_new/lib/python3.11/site-packages/crewai/cli/templates/pipeline_router/pipelines/pipeline_classifier.py
1:from crewai import Pipeline
2-from crewai.project import PipelineBase
3-from ..crews.classifier_crew.classifier_crew import ClassifierCrew
---
File: ./venv_new/lib/python3.11/site-packages/crewai/cli/templates/pipeline_router/pipelines/pipeline_urgent.py
1:from crewai import Pipeline
2-from crewai.project import PipelineBase
3-from ..crews.urgent_crew.urgent_crew import UrgentCrew
---
File: ./venv_new/lib/python3.11/site-packages/crewai/cli/templates/pipeline_router/pipelines/pipeline_normal.py
1:from crewai import Pipeline
2-from crewai.project import PipelineBase
3-from ..crews.normal_crew.normal_crew import NormalCrew
---
File: ./venv_new/lib/python3.11/site-packages/crewai/cli/templates/crew/crew.py
1:from crewai import Agent, Crew, Process, Task
2-from crewai.project import CrewBase, agent, crew, task
3-
---
File: ./auren/core/streaming/crewai_instrumentation.py
14-
15-# CrewAI imports
16:from crewai import Agent, Task, Crew, Process
17-
18-# Note: CrewAI event system has changed - using custom event capturing instead
---
File: ./auren/realtime/crewai_instrumentation.py
14-
15-# CrewAI imports
16:from crewai import Agent, Task, Crew, Process
17-
18-# Note: CrewAI event system has changed - using custom event capturing instead
---
File: ./auren/data_layer/crewai_integration.py
10-from datetime import datetime, timezone
11-
12:from crewai import Agent, Task, Crew
13-from crewai_tools import BaseTool
14-
---
File: ./auren/src/agents/neuroscientist.py
11-
12-import os
13:from crewai import Agent, Task, Crew
14-from typing import Dict, List, Optional, Any
15-import logging
---
File: ./auren/src/agents/specialists/neuroscientist.py
12-from typing import Dict, List, Optional, Any
13-from datetime import datetime, timedelta
14:from crewai import Agent, Task
15-from pathlib import Path
16-
---
File: ./auren/src/agents/ui_orchestrator.py
15-from pydantic import Field
16-
17:from crewai import Agent, Task, Crew
18-from crewai.tools.agent_tools import StructuredTool as BaseTool
19-
---
File: ./auren/src/rag/agentic_rag.py
7-from typing import Any, Dict, List, Optional, Tuple
8-
9:from crewai import Agent, Crew, Task
10-
11-from ..agents.biometric_aware_agents import BiometricAwareAgentFactory
---
File: ./agents/my_agent.py
7-    sys.path.insert(0, APP_DIR)
8-
9:from crewai import Agent
10-import streamlit as st
11-from utils import rnd_id, fix_columns_width
---
File: ./.venv/lib/python3.11/site-packages/crewai/experimental/evaluation/experiment/runner.py
3-from typing import Any
4-
5:from crewai import Crew, Agent
6-from crewai.experimental.evaluation import AgentEvaluator, create_default_evaluator
7-from crewai.experimental.evaluation.experiment.result_display import ExperimentResultsDisplay
---
File: ./.venv/lib/python3.11/site-packages/crewai/experimental/evaluation/testing.py
4-import warnings
5-from crewai.experimental.evaluation.experiment import ExperimentResults, ExperimentRunner
6:from crewai import Crew, Agent
7-
8-def assert_experiment_successfully(experiment_results: ExperimentResults, baseline_filepath: str | None = None) -> None:
---
File: ./.venv/lib/python3.11/site-packages/crewai/cli/templates/crew/crew.py
1:from crewai import Agent, Crew, Process, Task
2-from crewai.project import CrewBase, agent, crew, task
3-from crewai.agents.agent_builder.base_agent import BaseAgent
---
File: ./.venv/lib/python3.11/site-packages/crewai/cli/templates/flow/crews/poem_crew/poem_crew.py
1:from crewai import Agent, Crew, Process, Task
2-from crewai.project import CrewBase, agent, crew, task
3-from crewai.agents.agent_builder.base_agent import BaseAgent
---
File: ./.venv/lib/python3.11/site-packages/crewai/project/annotations.py
2-from typing import Callable
3-
4:from crewai import Crew
5-from crewai.project.utils import memoize
6-
---
File: ./src/auren/crews/whatsapp_crew.py
1:from crewai import Crew
2-from auren.agents.whatsapp_message_handler import WhatsAppMessageHandler
3-from auren.repositories import Database, AgentRepository, TaskRepository, CrewRepository
--
42-    def _create_tasks(self, user_id: str, message: str):
43-        """Create tasks for the crew based on the message"""
44:        from crewai import Task
45-        
46-        tasks = [
---
File: ./src/auren/app/app/my_task.py
4-
5-sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
6:from crewai import Task
7-import streamlit as st
8-from utils import rnd_id, fix_columns_width  # type: ignore
---
File: ./src/auren/app/app/pg_export_crew.py
81-        app_content = f"""
82-import streamlit as st
83:from crewai import Agent, Task, Crew, Process
84-from langchain_openai import ChatOpenAI
85-from langchain_groq import ChatGroq
---
File: ./src/auren/app/app/utils.py
5-from datetime import datetime
6-import re
7:from crewai import TaskOutput
8-
9-
---
File: ./src/auren/app/app/llms.py
5-from langchain_groq import ChatGroq
6-from langchain_anthropic import ChatAnthropic
7:from crewai import LLM
8-from langchain_openai.chat_models.base import BaseChatOpenAI
9-from litellm import completion
---
File: ./src/auren/app/app/pg_crew_run.py
1-import re
2-import streamlit as st
3:from crewai import TaskOutput
4-from streamlit import session_state as ss
5-import threading
---
File: ./src/auren/app/my_task.py
4-
5-sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
6:from crewai import Task
7-import streamlit as st
8-from utils import rnd_id, fix_columns_width  # type: ignore
---
File: ./src/auren/app/pg_export_crew.py
82-        app_content = f"""
83-import streamlit as st
84:from crewai import Agent, Task, Crew, Process
85-from langchain_openai import ChatOpenAI
86-from langchain_groq import ChatGroq
---
File: ./src/auren/app/utils.py
5-from datetime import datetime
6-import re
7:from crewai import TaskOutput
8-
9-
---
File: ./src/auren/app/llms.py
5-from langchain_groq import ChatGroq
6-from langchain_anthropic import ChatAnthropic
7:from crewai import LLM
8-from langchain_openai.chat_models.base import BaseChatOpenAI
9-from litellm import completion
---
File: ./src/auren/app/pg_crew_run.py
1-import re
2-import streamlit as st
3:from crewai import TaskOutput
4-from streamlit import session_state as ss
5-import threading
---
File: ./src/auren/agents/whatsapp_message_handler.py
1:from crewai import Agent
2-from auren.tools.IntentClassifierTool import IntentClassifierTool
3-from auren.tools.WhatsAppWebhookTool import WhatsAppWebhookTool
--
78-            
79-            # Create a simple task for the specialist
80:            from crewai import Task
81-            task = Task(
82-                description=f"User message: {message}\nUser ID: {user_id}\nPlease provide a helpful response.",
---
File: ./src/auren/agents/my_agent.py
9-    sys.path.insert(0, APP_DIR)
10-
11:from crewai import Agent
12-import streamlit as st
13-from utils import rnd_id, fix_columns_width
---
✅ FOUND files with 'import crewai':
./.venv/lib/python3.11/site-packages/crewai/experimental/evaluation/agent_evaluator.py
./.venv/lib/python3.11/site-packages/crewai/experimental/evaluation/evaluation_listener.py
./.venv/lib/python3.11/site-packages/crewai/task.py
./.venv/lib/python3.11/site-packages/crewai/tools/tool_usage.py
./.venv/lib/python3.11/site-packages/crewai/memory/short_term/short_term_memory.py
./.venv/lib/python3.11/site-packages/crewai/memory/long_term/long_term_memory.py
./.venv/lib/python3.11/site-packages/crewai/memory/entity/entity_memory.py
./.venv/lib/python3.11/site-packages/crewai/memory/external/external_memory.py
./.venv/lib/python3.11/site-packages/crewai/agents/crew_agent_executor.py
./.venv/lib/python3.11/site-packages/crewai/agents/agent_adapters/langgraph/langgraph_adapter.py
./.venv/lib/python3.11/site-packages/crewai/agents/agent_adapters/openai_agents/openai_adapter.py
./.venv/lib/python3.11/site-packages/crewai/llm.py
./.venv/lib/python3.11/site-packages/crewai/utilities/evaluators/crew_evaluator_handler.py
./.venv/lib/python3.11/site-packages/crewai/utilities/guardrail.py
./.venv/lib/python3.11/site-packages/crewai/utilities/reasoning_handler.py
./.venv/lib/python3.11/site-packages/crewai/crew.py
./.venv/lib/python3.11/site-packages/crewai/agent.py
./.venv/lib/python3.11/site-packages/crewai/lite_agent.py
./.venv/lib/python3.11/site-packages/crewai/flow/flow.py

Context:
File: ./.venv/lib/python3.11/site-packages/crewai/experimental/evaluation/agent_evaluator.py
9-from crewai.experimental.evaluation import BaseEvaluator, create_evaluation_callbacks
10-from collections.abc import Sequence
11:from crewai.utilities.events.crewai_event_bus import crewai_event_bus
12-from crewai.utilities.events.utils.console_formatter import ConsoleFormatter
13-from crewai.utilities.events.task_events import TaskCompletedEvent
---
File: ./.venv/lib/python3.11/site-packages/crewai/experimental/evaluation/evaluation_listener.py
228-
229-def create_evaluation_callbacks() -> EvaluationTraceCallback:
230:    from crewai.utilities.events.crewai_event_bus import crewai_event_bus
231-
232-    callback = EvaluationTraceCallback()
---
File: ./.venv/lib/python3.11/site-packages/crewai/task.py
48-    TaskStartedEvent,
49-)
50:from crewai.utilities.events.crewai_event_bus import crewai_event_bus
51-from crewai.utilities.i18n import I18N
52-from crewai.utilities.printer import Printer
--
511-            LLMGuardrailStartedEvent,
512-        )
513:        from crewai.utilities.events.crewai_event_bus import crewai_event_bus
514-
515-        crewai_event_bus.emit(
---
File: ./.venv/lib/python3.11/site-packages/crewai/tools/tool_usage.py
21-    render_text_description_and_args,
22-)
23:from crewai.utilities.events.crewai_event_bus import crewai_event_bus
24-from crewai.utilities.events.tool_usage_events import (
25-    ToolSelectionErrorEvent,
---
File: ./.venv/lib/python3.11/site-packages/crewai/memory/short_term/short_term_memory.py
7-from crewai.memory.short_term.short_term_memory_item import ShortTermMemoryItem
8-from crewai.memory.storage.rag_storage import RAGStorage
9:from crewai.utilities.events.crewai_event_bus import crewai_event_bus
10-from crewai.utilities.events.memory_events import (
11-    MemoryQueryStartedEvent,
---
File: ./.venv/lib/python3.11/site-packages/crewai/memory/long_term/long_term_memory.py
4-from crewai.memory.long_term.long_term_memory_item import LongTermMemoryItem
5-from crewai.memory.memory import Memory
6:from crewai.utilities.events.crewai_event_bus import crewai_event_bus
7-from crewai.utilities.events.memory_events import (
8-    MemoryQueryStartedEvent,
---
File: ./.venv/lib/python3.11/site-packages/crewai/memory/entity/entity_memory.py
7-from crewai.memory.memory import Memory
8-from crewai.memory.storage.rag_storage import RAGStorage
9:from crewai.utilities.events.crewai_event_bus import crewai_event_bus
10-from crewai.utilities.events.memory_events import (
11-    MemoryQueryStartedEvent,
---
File: ./.venv/lib/python3.11/site-packages/crewai/memory/external/external_memory.py
5-from crewai.memory.memory import Memory
6-from crewai.memory.storage.interface import Storage
7:from crewai.utilities.events.crewai_event_bus import crewai_event_bus
8-from crewai.utilities.events.memory_events import (
9-    MemoryQueryStartedEvent,
---
File: ./.venv/lib/python3.11/site-packages/crewai/agents/crew_agent_executor.py
35-    AgentLogsExecutionEvent,
36-)
37:from crewai.utilities.events.crewai_event_bus import crewai_event_bus
38-
39-
---
File: ./.venv/lib/python3.11/site-packages/crewai/agents/agent_adapters/langgraph/langgraph_adapter.py
15-from crewai.utilities import Logger
16-from crewai.utilities.converter import Converter
17:from crewai.utilities.events import crewai_event_bus
18-from crewai.utilities.events.agent_events import (
19-    AgentExecutionCompletedEvent,
---
File: ./.venv/lib/python3.11/site-packages/crewai/agents/agent_adapters/openai_agents/openai_adapter.py
11-from crewai.tools.agent_tools.agent_tools import AgentTools
12-from crewai.utilities import Logger
13:from crewai.utilities.events import crewai_event_bus
14-from crewai.utilities.events.agent_events import (
15-    AgentExecutionCompletedEvent,
---
File: ./.venv/lib/python3.11/site-packages/crewai/llm.py
53-
54-from crewai.llms.base_llm import BaseLLM
55:from crewai.utilities.events import crewai_event_bus
56-from crewai.utilities.exceptions.context_window_exceeding_exception import (
57-    LLMContextLengthExceededException,
---
File: ./.venv/lib/python3.11/site-packages/crewai/utilities/evaluators/crew_evaluator_handler.py
10-from crewai.task import Task
11-from crewai.tasks.task_output import TaskOutput
12:from crewai.utilities.events import crewai_event_bus
13-from crewai.utilities.events.crew_events import CrewTestResultEvent
14-
---
File: ./.venv/lib/python3.11/site-packages/crewai/utilities/guardrail.py
69-        LLMGuardrailStartedEvent,
70-    )
71:    from crewai.utilities.events.crewai_event_bus import crewai_event_bus
72-
73-    crewai_event_bus.emit(
---
File: ./.venv/lib/python3.11/site-packages/crewai/utilities/reasoning_handler.py
9-from crewai.utilities import I18N
10-from crewai.llm import LLM
11:from crewai.utilities.events.crewai_event_bus import crewai_event_bus
12-from crewai.utilities.events.reasoning_events import (
13-    AgentReasoningStartedEvent,
---
File: ./.venv/lib/python3.11/site-packages/crewai/crew.py
72-    CrewTrainStartedEvent,
73-)
74:from crewai.utilities.events.crewai_event_bus import crewai_event_bus
75-from crewai.utilities.events.event_listener import EventListener
76-from crewai.utilities.formatter import (
---
File: ./.venv/lib/python3.11/site-packages/crewai/agent.py
33-    AgentExecutionStartedEvent,
34-)
35:from crewai.utilities.events.crewai_event_bus import crewai_event_bus
36-from crewai.utilities.events.memory_events import (
37-    MemoryRetrievalStartedEvent,
---
File: ./.venv/lib/python3.11/site-packages/crewai/lite_agent.py
69-    LiteAgentExecutionStartedEvent,
70-)
71:from crewai.utilities.events.crewai_event_bus import crewai_event_bus
72-from crewai.utilities.events.llm_events import (
73-    LLMCallCompletedEvent,
---
File: ./.venv/lib/python3.11/site-packages/crewai/flow/flow.py
23-from crewai.flow.persistence.base import FlowPersistence
24-from crewai.flow.utils import get_possible_return_constants
25:from crewai.utilities.events.crewai_event_bus import crewai_event_bus
26-from crewai.utilities.events.flow_events import (
27-    FlowCreatedEvent,
---
✅ FOUND files with 'CrewAI':
./venv_new/lib/python3.11/site-packages/crewai/agents/agent_builder/base_agent.py
./venv_new/lib/python3.11/site-packages/crewai/cli/deploy/api.py
./venv_new/lib/python3.11/site-packages/crewai/cli/deploy/main.py
./venv_new/lib/python3.11/site-packages/crewai/cli/cli.py
./venv_new/lib/python3.11/site-packages/crewai/cli/authentication/main.py
./venv_new/lib/python3.11/site-packages/crewai/project/pipeline_base.py
./venv_new/lib/python3.11/site-packages/crewai/utilities/paths.py
./venv_new/lib/python3.11/site-packages/crewai/agent.py
./auren/demo/demo_neuroscientist.py
./auren/main_clean.py
./auren/core/streaming/crewai_instrumentation.py
./auren/core/streaming/memory_tier_integration.py
./auren/core/streaming/test_event_pipeline.py
./auren/core/streaming/performance_optimizer_integration.py
./auren/core/streaming/secure_integration.py
./auren/core/streaming/generate_test_events.py
./auren/core/streaming/test_integration_module_d_c.py
./auren/start_auren.py
./auren/config/agents/base_config.yaml
./auren/config/production_settings.py
./auren/config/neuros.yaml
./auren/tests/test_postgresql_integration.py
./auren/tests/test_ai_gateway.py
./auren/tests/test_neuroscientist_integration.py
./auren/agents/neuros/neuros_agent_profile.yaml
./auren/utils/check_system_health.py
./auren/realtime/crewai_instrumentation.py
./auren/realtime/memory_tier_integration.py
./auren/realtime/test_event_pipeline.py
./auren/realtime/performance_optimizer_integration.py
./auren/realtime/secure_integration.py
./auren/realtime/generate_test_events.py
./auren/realtime/test_integration_module_d_c.py
./auren/scripts/test_redis_tracking.py
./auren/scripts/refactor_imports.py
./auren/data_layer/crewai_integration.py
./auren/src/tools/__init__.py
./auren/src/tools/routing_tools.py
./auren/src/auren/ai/gateway.py
./auren/src/auren/ai/crewai_gateway_adapter.py
./auren/src/auren/ai/security_audit.py
./auren/src/auren/ai/neuroscientist_integration_example.py
./auren/src/auren/ai/__init__.py
./auren/src/auren/data_layer/crewai_integration.py
./auren/src/auren/monitoring/decorators.py
./auren/src/config/settings.py
./auren/src/agents/neuroscientist.py
./auren/src/agents/specialists/neuroscientist.py
./auren/src/agents/specialists/base_specialist_postgresql.py
./auren/src/agents/specialists/base_specialist.py
./auren/src/agents/ui_orchestrator.py
./config/agents/neuros_agent_profile.yaml
./agents/my_agent.py
./validate_tools.py
./.venv/bin/pdf2txt.py
./.venv/bin/dumppdf.py
./.venv/bin/jp.py
./.venv/lib/python3.11/site-packages/crewai/experimental/evaluation/evaluation_listener.py
./.venv/lib/python3.11/site-packages/crewai/tasks/hallucination_guardrail.py
./.venv/lib/python3.11/site-packages/crewai/tools/structured_tool.py
./.venv/lib/python3.11/site-packages/crewai/security/fingerprint.py
./.venv/lib/python3.11/site-packages/crewai/security/__init__.py
./.venv/lib/python3.11/site-packages/crewai/security/security_config.py
./.venv/lib/python3.11/site-packages/crewai/__init__.py
./.venv/lib/python3.11/site-packages/crewai/agents/agent_adapters/langgraph/langgraph_adapter.py
./.venv/lib/python3.11/site-packages/crewai/agents/agent_adapters/langgraph/langgraph_tool_adapter.py
./.venv/lib/python3.11/site-packages/crewai/agents/agent_adapters/base_tool_adapter.py
./.venv/lib/python3.11/site-packages/crewai/agents/agent_adapters/openai_agents/openai_agent_tool_adapter.py
./.venv/lib/python3.11/site-packages/crewai/agents/agent_adapters/base_converter_adapter.py
./.venv/lib/python3.11/site-packages/crewai/agents/agent_adapters/base_agent_adapter.py
./.venv/lib/python3.11/site-packages/crewai/agents/agent_builder/base_agent.py
./.venv/lib/python3.11/site-packages/crewai/cli/tools/main.py
./.venv/lib/python3.11/site-packages/crewai/cli/command.py
./.venv/lib/python3.11/site-packages/crewai/cli/version.py
./.venv/lib/python3.11/site-packages/crewai/cli/deploy/main.py
./.venv/lib/python3.11/site-packages/crewai/cli/crew_chat.py
./.venv/lib/python3.11/site-packages/crewai/cli/cli.py
./.venv/lib/python3.11/site-packages/crewai/cli/plus_api.py
./.venv/lib/python3.11/site-packages/crewai/cli/templates/flow/crews/poem_crew/config/agents.yaml
./.venv/lib/python3.11/site-packages/crewai/cli/templates/flow/crews/poem_crew/config/tasks.yaml
./.venv/lib/python3.11/site-packages/crewai/cli/authentication/main.py
./.venv/lib/python3.11/site-packages/crewai/utilities/paths.py
./.venv/lib/python3.11/site-packages/crewai/utilities/agent_utils.py
./.venv/lib/python3.11/site-packages/crewai/utilities/crew_json_encoder.py
./.venv/lib/python3.11/site-packages/crewai/utilities/i18n.py
./.venv/lib/python3.11/site-packages/crewai/utilities/errors.py
./.venv/lib/python3.11/site-packages/crewai/utilities/events/crewai_event_bus.py
./.venv/lib/python3.11/site-packages/crewai/utilities/events/base_event_listener.py
./.venv/lib/python3.11/site-packages/crewai/utilities/events/__init__.py
./.venv/lib/python3.11/site-packages/crewai/flow/persistence/__init__.py
./.venv/lib/python3.11/site-packages/crewai/flow/path_utils.py
./scripts/test_whatsapp_flow.py
./src/auren/app/pg_knowledge.py
./src/auren/app/app/pg_knowledge.py
./src/auren/app/app/my_tools.py
./src/auren/app/app/utils.py
./src/auren/app/app/app.py
./src/auren/app/my_tools.py
./src/auren/app/utils.py
./src/auren/app/app.py
./src/auren/agents/my_agent.py

Context:
File: ./venv_new/lib/python3.11/site-packages/crewai/agents/agent_builder/base_agent.py
26-
27-class BaseAgent(ABC, BaseModel):
28:    """Abstract Base Class for all third party agents compatible with CrewAI.
29-
30-    Attributes:
---
File: ./venv_new/lib/python3.11/site-packages/crewai/cli/deploy/api.py
16-            "Authorization": f"Bearer {api_key}",
17-            "Content-Type": "application/json",
18:            "User-Agent": f"CrewAI-CLI/{get_crewai_version()}",
19-        }
20-        self.base_url = getenv(
---
File: ./venv_new/lib/python3.11/site-packages/crewai/cli/deploy/main.py
17-class DeployCommand:
18-    """
19:    A class to handle deployment-related operations for CrewAI projects.
20-    """
21-
--
31-            self._deploy_signup_error_span = self._telemetry.deploy_signup_error_span()
32-            console.print(
33:                "Please sign up/login to CrewAI+ before using the CLI.",
34-                style="bold red",
35-            )
---
File: ./venv_new/lib/python3.11/site-packages/crewai/cli/cli.py
186-@crewai.command()
187-def signup():
188:    """Sign Up/Login to CrewAI+."""
189-    AuthenticationCommand().signup()
190-
--
192-@crewai.command()
193-def login():
194:    """Sign Up/Login to CrewAI+."""
195-    AuthenticationCommand().signup()
196-
---
File: ./venv_new/lib/python3.11/site-packages/crewai/cli/authentication/main.py
20-
21-    def signup(self) -> None:
22:        """Sign up to CrewAI+"""
23:        console.print("Signing Up to CrewAI+ \n", style="bold blue")
24-        device_code_data = self._get_device_code()
25-        self._display_auth_instructions(device_code_data)
--
62-                expires_in = 360000  # Token expiration time in seconds
63-                self.token_manager.save_tokens(token_data["access_token"], expires_in)
64:                console.print("\nWelcome to CrewAI+ !!", style="green")
65-                return
66-
---
File: ./venv_new/lib/python3.11/site-packages/crewai/project/pipeline_base.py
8-
9-
10:# TODO: Could potentially remove. Need to check with @joao and @gui if this is needed for CrewAI+
11-def PipelineBase(cls: Type[Any]) -> Type[Any]:
12-    class WrappedClass(cls):
---
File: ./venv_new/lib/python3.11/site-packages/crewai/utilities/paths.py
7-def db_storage_path():
8-    app_name = get_project_directory_name()
9:    app_author = "CrewAI"
10-
11-    data_dir = Path(appdirs.user_data_dir(app_name, app_author))
---
File: ./venv_new/lib/python3.11/site-packages/crewai/agent.py
335-        tools_list = []
336-        try:
337:            # tentatively try to import from crewai_tools import BaseTool as CrewAITool
338:            from crewai_tools import BaseTool as CrewAITool
339-
340-            for tool in tools:
341:                if isinstance(tool, CrewAITool):
342-                    tools_list.append(tool.to_langchain())
343-                else:
---
File: ./auren/demo/demo_neuroscientist.py
22-# Import AUREN components
23-from auren.realtime.crewai_instrumentation import (
24:    CrewAIEventInstrumentation,
25-    AURENStreamEvent,
26-    AURENEventType,
--
89-        await self.redis_streamer.initialize()
90-        
91:        self.event_instrumentation = CrewAIEventInstrumentation(
92-            event_streamer=self.redis_streamer
93-        )
---
File: ./auren/main_clean.py
2-# SECTION 12: MAIN EXECUTION - CLEAN IMPLEMENTATION (NO CREWAI)
3-# =============================================================================
4:# Purpose: Production-ready runtime without CrewAI dependencies
5-# Last Updated: 2025-01-29
6-# =============================================================================
--
58-    # Startup
59-    logger.info("🚀 Starting AUREN Production Runtime (Section 12)...")
60:    logger.info("Clean implementation without CrewAI dependencies")
61-    
62-    try:
--
144-app = FastAPI(
145-    title="AUREN Production Runtime",
146:    description="Clean production runtime without CrewAI dependencies",
147-    version="12.0.0",
148-    lifespan=lifespan
---
File: ./auren/core/streaming/crewai_instrumentation.py
1-"""
2:Complete CrewAI instrumentation for event generation
3-This is the source of all events that get streamed to dashboards
4-"""
--
13-import uuid
14-
15:# CrewAI imports
16-from crewai import Agent, Task, Crew, Process
17-
18:# Note: CrewAI event system has changed - using custom event capturing instead
19-# from crewai.agents.events import (
20-#     AgentExecutionStartedEvent,
--
78-    user_id: Optional[str] = None
79-
80:class CrewAIEventInstrumentation:
81-    """
82:    Complete instrumentation system for CrewAI agents
83-    Captures all agent activities and generates standardized events
84-    """
--
96-    def _setup_event_listeners(self):
97-        """Register comprehensive event listeners"""
98:        # Since CrewAI doesn't expose events directly in current version,
99-        # we'll need to instrument agents manually when they're created
100-        logger.info("Event instrumentation initialized - manual tracking mode")
---
File: ./auren/core/streaming/memory_tier_integration.py
13-
14-# Import from Module C
15:from auren.realtime.crewai_instrumentation import CrewAIEventInstrumentation, AURENEventType
16-from auren.realtime.multi_protocol_streaming import RedisStreamEventStreamer
17-
--
64-            )
65-            
66:            # Also perform standard CrewAI operations
67-            crew_memories = []
68-            for memory in memories:
--
102-    
103-    # 3. Create event instrumentation
104:    event_instrumentation = CrewAIEventInstrumentation(
105-        event_streamer=redis_streamer
106-    )
---
File: ./auren/core/streaming/test_event_pipeline.py
9-
10-from auren.realtime.crewai_instrumentation import (
11:    CrewAIEventInstrumentation, 
12-    AURENStreamEvent, 
13-    AURENEventType,
--
32-    logger.info("✅ Redis streamer initialized")
33-    
34:    # 2. Initialize CrewAI Instrumentation
35:    instrumentation = CrewAIEventInstrumentation(
36-        event_streamer=redis_streamer
37-    )
38:    logger.info("✅ CrewAI instrumentation initialized")
39-    
40-    # 3. Create and send test events
---
File: ./auren/core/streaming/performance_optimizer_integration.py
17-# Import from Module C
18-from auren.realtime.crewai_instrumentation import (
19:    CrewAIEventInstrumentation, 
20-    AURENStreamEvent,
21-    AURENEventType
--
58-    
59-    # 4. Create event instrumentation with optimized streamer
60:    event_instrumentation = CrewAIEventInstrumentation(
61-        event_streamer=optimized_streamer  # All events now batched!
62-    )
---
File: ./auren/core/streaming/secure_integration.py
14-
15-# Import from Module C
16:from auren.realtime.crewai_instrumentation import CrewAIEventInstrumentation
17-from auren.realtime.multi_protocol_streaming import RedisStreamEventStreamer
18-from auren.realtime.enhanced_websocket_streamer import EnhancedWebSocketEventStreamer, ClientSubscription
--
57-    
58-    # 3. Initialize event instrumentation with secure streamer
59:    event_instrumentation = CrewAIEventInstrumentation(
60-        event_streamer=secure_streamer  # Now all events go through security!
61-    )
---
File: ./auren/core/streaming/generate_test_events.py
7-from datetime import datetime, timezone
8-from auren.realtime.crewai_instrumentation import (
9:    CrewAIEventInstrumentation, 
10-    AURENStreamEvent, 
11-    AURENEventType,
--
30-    
31-    # Initialize instrumentation
32:    instrumentation = CrewAIEventInstrumentation(
33-        event_streamer=redis_streamer
34-    )
---
File: ./auren/core/streaming/test_integration_module_d_c.py
18-from realtime.enhanced_websocket_streamer import EnhancedWebSocketStreamer
19-from realtime.crewai_instrumentation import (
20:    CrewAIEventInstrumentation,
21-    AURENStreamEvent,
22-    AURENEventType,
--
54-    async def event_instrumentation(self, redis_client):
55-        """Create event instrumentation instance"""
56:        instrumentation = CrewAIEventInstrumentation(
57-            redis_url="redis://localhost:6379",
58-            enable_streaming=True
--
378-    await redis_client.delete("auren:events:analytical")
379-    
380:    instrumentation = CrewAIEventInstrumentation(
381-        redis_url="redis://localhost:6379",
382-        enable_streaming=True
---
File: ./auren/start_auren.py
94-    print("   • Biometric Analysis: Facial landmark detection")
95-    print("   • Alert Management: Real-time monitoring")
96:    print("   • CrewAI Agents: Multi-agent coordination")
97-    print("   • Agentic RAG: Intelligent information retrieval")
98-    print("   • WhatsApp: Mobile interface ready")
---
File: ./auren/config/agents/base_config.yaml
1-# AUREN 2.0 Agent Configuration
2:# Based on CrewAI best practices from knowledge base
3-
4-agents:
---
File: ./auren/config/production_settings.py
20-    chromadb_port: int = Field(default=8000, env="CHROMADB_PORT")
21-    chromadb_path: str = Field(
22:        default="/Users/Jason/Downloads/CrewAI-Studio-main/data/chromadb",
23-        env="CHROMADB_PATH"
24-    )
---
File: ./auren/config/neuros.yaml
1-# NEUROS Complete Agent Profile - AUREN Framework
2:# This YAML is designed to plug directly into CrewAI with AUREN's custom extensions
3-
4-agent_profile:
--
7-  model_type: Elite cognitive and biometric optimization agent
8-  version: 1.0.0
9:  framework_compatibility: AUREN_CrewAI_v1
10-
11-  # Specializations
---
File: ./auren/tests/test_postgresql_integration.py
185-@pytest.mark.asyncio
186-async def test_crewai_integration(db_setup):
187:    """Test CrewAI integration layer"""
188-    integration = db_setup['integration']
189-    
---
File: ./auren/tests/test_ai_gateway.py
18-from auren.ai import (
19-    AIGateway,
20:    CrewAIGateway,
21-    GatewayRequest,
22-    AdaptiveCircuitBreaker,
---
File: ./auren/tests/test_neuroscientist_integration.py
22-from auren.src.cep.hrv_rules import HRVRuleEngine, BiometricEvent, HRVMonitoringService
23-from auren.ai.gateway import AIGateway
24:from auren.ai.crewai_gateway_adapter import CrewAIGatewayAdapter
25-from auren.monitoring.decorators import get_token_tracker
26-from auren.src.config.settings import get_settings
--
52-        # Initialize AI components
53-        cls.gateway = AIGateway()
54:        cls.adapter = CrewAIGatewayAdapter(cls.gateway)
55-        cls.neuroscientist = create_neuroscientist(cls.adapter)
56-        
---
File: ./auren/agents/neuros/neuros_agent_profile.yaml
1-# NEUROS Complete Agent Profile - AUREN Framework
2:# This YAML is designed to plug directly into CrewAI with AUREN's custom extensions
3-
4-agent_profile:
--
7-  model_type: Elite cognitive and biometric optimization agent
8-  version: 1.0.0
9:  framework_compatibility: AUREN_CrewAI_v1
10-
11-  # Specializations
---
File: ./auren/utils/check_system_health.py
234-        try:
235-            # Check if instrumentation module exists
236:            from auren.realtime.crewai_instrumentation import CrewAIEventInstrumentation
237-            
238-            # Check if streaming module exists
--
240-            
241-            return True, "Event streaming modules available", [
242:                "CrewAI instrumentation ready",
243-                "Multi-protocol streaming ready"
244-            ]
---
File: ./auren/realtime/crewai_instrumentation.py
1-"""
2:Complete CrewAI instrumentation for event generation
3-This is the source of all events that get streamed to dashboards
4-"""
--
13-import uuid
14-
15:# CrewAI imports
16-from crewai import Agent, Task, Crew, Process
17-
18:# Note: CrewAI event system has changed - using custom event capturing instead
19-# from crewai.agents.events import (
20-#     AgentExecutionStartedEvent,
--
78-    user_id: Optional[str] = None
79-
80:class CrewAIEventInstrumentation:
81-    """
82:    Complete instrumentation system for CrewAI agents
83-    Captures all agent activities and generates standardized events
84-    """
--
96-    def _setup_event_listeners(self):
97-        """Register comprehensive event listeners"""
98:        # Since CrewAI doesn't expose events directly in current version,
99-        # we'll need to instrument agents manually when they're created
100-        logger.info("Event instrumentation initialized - manual tracking mode")
---
File: ./auren/realtime/memory_tier_integration.py
13-
14-# Import from Module C
15:from auren.realtime.crewai_instrumentation import CrewAIEventInstrumentation, AURENEventType
16-from auren.realtime.multi_protocol_streaming import RedisStreamEventStreamer
17-
--
64-            )
65-            
66:            # Also perform standard CrewAI operations
67-            crew_memories = []
68-            for memory in memories:
--
102-    
103-    # 3. Create event instrumentation
104:    event_instrumentation = CrewAIEventInstrumentation(
105-        event_streamer=redis_streamer
106-    )
---
File: ./auren/realtime/test_event_pipeline.py
9-
10-from auren.realtime.crewai_instrumentation import (
11:    CrewAIEventInstrumentation, 
12-    AURENStreamEvent, 
13-    AURENEventType,
--
32-    logger.info("✅ Redis streamer initialized")
33-    
34:    # 2. Initialize CrewAI Instrumentation
35:    instrumentation = CrewAIEventInstrumentation(
36-        event_streamer=redis_streamer
37-    )
38:    logger.info("✅ CrewAI instrumentation initialized")
39-    
40-    # 3. Create and send test events
---
File: ./auren/realtime/performance_optimizer_integration.py
17-# Import from Module C
18-from auren.realtime.crewai_instrumentation import (
19:    CrewAIEventInstrumentation, 
20-    AURENStreamEvent,
21-    AURENEventType
--
58-    
59-    # 4. Create event instrumentation with optimized streamer
60:    event_instrumentation = CrewAIEventInstrumentation(
61-        event_streamer=optimized_streamer  # All events now batched!
62-    )
---
File: ./auren/realtime/secure_integration.py
14-
15-# Import from Module C
16:from auren.realtime.crewai_instrumentation import CrewAIEventInstrumentation
17-from auren.realtime.multi_protocol_streaming import RedisStreamEventStreamer
18-from auren.realtime.enhanced_websocket_streamer import EnhancedWebSocketEventStreamer, ClientSubscription
--
57-    
58-    # 3. Initialize event instrumentation with secure streamer
59:    event_instrumentation = CrewAIEventInstrumentation(
60-        event_streamer=secure_streamer  # Now all events go through security!
61-    )
---
File: ./auren/realtime/generate_test_events.py
7-from datetime import datetime, timezone
8-from auren.realtime.crewai_instrumentation import (
9:    CrewAIEventInstrumentation, 
10-    AURENStreamEvent, 
11-    AURENEventType,
--
30-    
31-    # Initialize instrumentation
32:    instrumentation = CrewAIEventInstrumentation(
33-        event_streamer=redis_streamer
34-    )
---
File: ./auren/realtime/test_integration_module_d_c.py
18-from realtime.enhanced_websocket_streamer import EnhancedWebSocketStreamer
19-from realtime.crewai_instrumentation import (
20:    CrewAIEventInstrumentation,
21-    AURENStreamEvent,
22-    AURENEventType,
--
54-    async def event_instrumentation(self, redis_client):
55-        """Create event instrumentation instance"""
56:        instrumentation = CrewAIEventInstrumentation(
57-            redis_url="redis://localhost:6379",
58-            enable_streaming=True
--
378-    await redis_client.delete("auren:events:analytical")
379-    
380:    instrumentation = CrewAIEventInstrumentation(
381-        redis_url="redis://localhost:6379",
382-        enable_streaming=True
---
File: ./auren/scripts/test_redis_tracking.py
15-
16-
17:# Example CrewAI agent simulation
18-class MockNeuroscientist:
19-    def __init__(self):
---
File: ./auren/scripts/refactor_imports.py
76-def refactor_all():
77-    """Refactor all Python files in the project"""
78:    root = Path('/Users/Jason/Downloads/CrewAI-Studio-main/auren')
79-    refactored_count = 0
80-    
---
File: ./auren/data_layer/crewai_integration.py
1-"""
2:CrewAI Integration for AUREN Intelligence System
3:Provides seamless integration between CrewAI agents and the intelligence system
4-"""
5-
--
23-
24-
25:class CrewAIIntelligenceAdapter:
26-    """
27:    Adapter for integrating CrewAI agents with AUREN intelligence system
28-    
29-    Features:
--
39-                 event_store: Optional[EventStore] = None):
40-        """
41:        Initialize CrewAI intelligence adapter
42-        
43-        Args:
--
66-            
67-            self._initialized = True
68:            logger.info("✅ CrewAI intelligence adapter initialized")
69-            return True
70-            
71-        except Exception as e:
72:            logger.error(f"❌ Failed to initialize CrewAI adapter: {e}")
73-            return False
74-    
--
83-                               verbose: bool = False) -> Agent:
84-        """
85:        Create an intelligent CrewAI agent with AUREN integration
86-        
87-        Args:
--
96-            
97-        Returns:
98:            Configured CrewAI agent
99-        """
100-        
--
549-
550-# Utility functions
551:async def create_intelligence_adapter() -> CrewAIIntelligenceAdapter:
552-    """
553-    Create and initialize intelligence adapter
--
556-        Initialized intelligence adapter
557-    """
558:    adapter = CrewAIIntelligenceAdapter()
559-    await adapter.initialize()
560-    return adapter
--
563-async def test_crewai_integration():
564-    """
565:    Test CrewAI integration
566-    """
567-    adapter = await create_intelligence_adapter()
---
File: ./auren/src/tools/__init__.py
25-
26-__all__ = [
27:    # Factory functions for CrewAI integration
28-    'create_routing_logic_tool',
29-    'create_direct_routing_tool',
---
File: ./auren/src/tools/routing_tools.py
585-
586-
587:# Tool factory functions for CrewAI integration
588-def create_routing_logic_tool() -> RoutingLogicTool:
589-    """Create a routing logic tool instance."""
---
File: ./auren/src/auren/ai/gateway.py
192-
193-
194:class CrewAIGateway:
195:    """CrewAI-compatible gateway interface."""
196-    
197-    def __init__(self, gateway: Optional[AIGateway] = None):
--
205-        **kwargs
206-    ) -> str:
207:        """CrewAI-compatible completion method."""
208-        request = GatewayRequest(
209-            prompt=prompt,
---
File: ./auren/src/auren/ai/crewai_gateway_adapter.py
1-"""
2:CrewAI Gateway Adapter - Bridges AI Gateway with CrewAI agent execution.
3-
4:This adapter enables CrewAI agents (specifically the Neuroscientist specialist)
5-to make LLM calls through the production-ready AI Gateway while maintaining
6-full observability, cost tracking, and memory integration.
--
44-
45-
46:class CrewAIGatewayAdapter:
47-    """
48:    Adapter that bridges CrewAI agents with the AI Gateway.
49-    
50-    This adapter handles:
--
95-    ) -> str:
96-        """
97:        Execute a prompt for a CrewAI agent with full tracking.
98-        
99-        This method is decorated with @track_tokens to automatically
--
281-        return "\n".join(summary_parts)
282-    
283:    # Synchronous wrapper for CrewAI compatibility
284-    def execute_for_agent_sync(
285-        self,
--
289-    ) -> str:
290-        """
291:        Synchronous wrapper for CrewAI integration.
292-        
293:        CrewAI tasks are synchronous, so this wrapper allows
294:        the adapter to be used in standard CrewAI workflows.
295-        """
296-        try:
---
File: ./auren/src/auren/ai/security_audit.py
18-
19-from .gateway import AIGateway
20:from .crewai_gateway_adapter import CrewAIGatewayAdapter, AgentContext
21-from .neuroscientist_integration_example import NeuroscientistSpecialist
22-from ..monitoring.otel_config import init_telemetry
--
180-            
181-            # Test adapter logging
182:            adapter = CrewAIGatewayAdapter(
183-                ai_gateway=MagicMock(),
184-                default_model="gpt-3.5-turbo"
--
224-        mock_gateway.complete.side_effect = Exception("Gateway error")
225-        
226:        adapter = CrewAIGatewayAdapter(ai_gateway=mock_gateway)
227-        
228-        for context_data in test_contexts:
--
283-        
284-        # Test that contexts don't leak
285:        adapter = CrewAIGatewayAdapter(ai_gateway=MagicMock())
286-        
287-        # Build prompts for both users
--
315-        # Check that gateway requests include proper authentication
316-        mock_gateway = MagicMock()
317:        adapter = CrewAIGatewayAdapter(ai_gateway=mock_gateway)
318-        
319-        context = AgentContext(
--
375-        try:
376-            # Create specialist with PHI in memory
377:            adapter = CrewAIGatewayAdapter(ai_gateway=MagicMock())
378-            specialist = NeuroscientistSpecialist(
379-                memory_path=memory_path,
---
File: ./auren/src/auren/ai/neuroscientist_integration_example.py
3-
4-This example shows how the Neuroscientist specialist uses the AI Gateway
5:through the CrewAI adapter with full observability and token tracking.
6-"""
7-
--
12-# Import the AI Gateway components
13-from .gateway import AIGateway
14:from .crewai_gateway_adapter import CrewAIGatewayAdapter, AgentContext
15-
16-# Import the BaseSpecialist framework
--
38-    """
39-    
40:    def __init__(self, memory_path: Path, gateway_adapter: CrewAIGatewayAdapter):
41-        """Initialize the Neuroscientist with gateway integration."""
42-        # Define the Neuroscientist's genesis configuration
--
280-    
281-    # Create gateway adapter
282:    adapter = CrewAIGatewayAdapter(
283-        ai_gateway=gateway,
284-        memory_profile=memory_profile,
---
File: ./auren/src/auren/ai/__init__.py
8-from typing import Optional
9-
10:from .gateway import AIGateway, CrewAIGateway, GatewayRequest, GatewayResponse
11-from .providers import (
12-    BaseLLMProvider,
--
25-__all__ = [
26-    "AIGateway",
27:    "CrewAIGateway",
28-    "GatewayRequest",
29-    "GatewayResponse",
---
File: ./auren/src/auren/data_layer/crewai_integration.py
1-"""
2:CrewAI Integration Layer
3:Provides seamless integration between PostgreSQL memory backend and CrewAI agents
4-"""
5-
--
16-class AURENMemoryStorage:
17-    """
18:    Memory storage implementation for CrewAI agents
19-    Provides unlimited memory storage with PostgreSQL backend
20-    """
--
95-class AURENCrewMemoryIntegration:
96-    """
97:    Integration layer for CrewAI agents
98-    Provides factory methods for creating memory storage instances
99-    """
---
File: ./auren/src/auren/monitoring/decorators.py
1-"""
2:Token tracking decorators for easy integration with CrewAI agents
3-"""
4-
--
175-    context["conversation_id"] = kwargs.get("conversation_id", context["conversation_id"])
176-    
177:    # For CrewAI integration: check if first arg is self with agent info
178-    if args and hasattr(args[0], "__class__"):
179-        obj = args[0]
180:        if hasattr(obj, "role"):  # CrewAI agent
181-            context["agent_id"] = getattr(obj, "role", context["agent_id"])
182-        if hasattr(obj, "id"):
---
File: ./auren/src/config/settings.py
85-    debug: bool = Field(default=False, env="DEBUG")
86-    
87:    # CrewAI settings
88-    crewai_max_iterations: int = Field(default=3, env="CREWAI_MAX_ITERATIONS")
89-    crewai_memory_enabled: bool = Field(default=True, env="CREWAI_MEMORY_ENABLED")
---
File: ./auren/src/agents/neuroscientist.py
60-        os.environ["OPENAI_MODEL_NAME"] = "gpt-4"
61-        
62:        # Initialize the CrewAI agent with comprehensive backstory
63-        self.crew_agent = Agent(
64-            role='Neuroscientist - CNS Optimization Specialist',
--
79-            - Build long-term profiles of athlete patterns""",
80-            verbose=True,
81:            memory=True,   # CrewAI memory still enabled for session context
82-            max_iter=3,
83-            allow_delegation=False
--
236-    
237-    async def _execute_crew_task(self, task_description: str) -> str:
238:        """Execute a CrewAI task and return the result."""
239-        task = Task(
240-            description=task_description,
---
File: ./auren/src/agents/specialists/neuroscientist.py
17-# Import our custom components
18-from src.agents.specialists.base_specialist import BaseSpecialist
19:from src.auren.ai.crewai_gateway_adapter import CrewAIGatewayAdapter
20-from src.database.connection import DatabaseConnection
21-from src.auren.monitoring.decorators import track_tokens
--
40-    """
41-    
42:    def __init__(self, gateway_adapter: CrewAIGatewayAdapter):
43-        """
44-        Initialize the Neuroscientist specialist
45-        
46-        Args:
47:            gateway_adapter: The CrewAI-AI Gateway adapter for LLM interactions
48-        """
49-        # Initialize with comprehensive backstory and capabilities
--
688-    def as_crewai_agent(self) -> Agent:
689-        """
690:        Convert to CrewAI Agent format for crew integration
691-        
692-        This allows the Neuroscientist to participate in multi-agent
--
706-
707-# Convenience function for creating Neuroscientist agent
708:def create_neuroscientist(gateway_adapter: CrewAIGatewayAdapter) -> Neuroscientist:
709-    """
710-    Factory function to create a configured Neuroscientist agent
--
723-    import asyncio
724-    from src.auren.ai.gateway import AIGateway
725:    from src.auren.ai.crewai_gateway_adapter import CrewAIGatewayAdapter
726-    
727-    async def test_neuroscientist():
--
729-        # Initialize components
730-        gateway = AIGateway()
731:        adapter = CrewAIGatewayAdapter(gateway)
732-        
733-        # Create Neuroscientist
---
File: ./auren/src/agents/specialists/base_specialist_postgresql.py
52-            db_pool: PostgreSQL connection pool
53-            user_id: User ID for user-specific memory isolation
54:            override_agent: Optional pre-configured CrewAI agent
55-        """
56-        self.identity = genesis.identity
--
188-    
189-    def process_interaction_sync(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
190:        """Synchronous wrapper for CrewAI compatibility."""
191-        try:
192-            loop = asyncio.get_event_loop()
--
198-    
199-    def execute_task(self, task_description: str, context: Optional[Dict[str, Any]] = None) -> str:
200:        """Execute task in CrewAI-compatible format."""
201-        if context is None:
202-            context = {}
---
File: ./auren/src/agents/specialists/base_specialist.py
96-            memory_path: Path to persistent memory storage
97-            memory_retention_limit: Maximum evolution records to retain
98:            override_agent: Optional pre-configured CrewAI agent (advanced use case)
99-                          Default None maintains self-birthing behavior
100-        """
--
337-    def process_interaction_sync(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
338-        """
339:        Synchronous wrapper for process_interaction for CrewAI compatibility.
340-        
341:        CrewAI's task execution is synchronous, so this wrapper allows
342:        specialists to be used in standard CrewAI workflows while maintaining
343-        our async architecture for future scalability.
344-        
--
366-    ) -> ConsensusPosition:
367-        """
368:        Synchronous wrapper for collaborate_on_consensus for CrewAI compatibility.
369-        
370-        Allows specialists to participate in consensus building within
371:        CrewAI's synchronous task execution model.
372-        
373-        Args:
--
388-    def execute_task(self, task_description: str, context: Optional[Dict[str, Any]] = None) -> str:
389-        """
390:        Execute a task in CrewAI-compatible format.
391-        
392-        This method provides a simple string-in, string-out interface
393:        that CrewAI tasks expect, while leveraging the full specialist
394-        capabilities internally.
395-        
--
399-            
400-        Returns:
401:            String response suitable for CrewAI task output
402-        """
403-        if context is None:
--
407-        result = self.process_interaction_sync(task_description, context)
408-        
409:        # Format response for CrewAI
410-        response_parts = []
411-        
--
428-        Export specialist configuration in YAML-compatible format.
429-        
430:        This allows basic interoperability with CrewAI YAML workflows
431-        while maintaining the dynamic nature of specialists.
432-        
---
File: ./auren/src/agents/ui_orchestrator.py
56-        self.packet_builder = create_packet_builder()
57-        
58:        # Initialize CrewAI agent
59-        self.agent = self._create_agent()
60-        
61-    def _create_agent(self) -> Agent:
62:        """Create the CrewAI agent for AUREN's personality."""
63-        return Agent(
64-            role="AUREN - Personal Optimization Companion",
--
229-
230-
231:# Factory function for CrewAI integration
232-def create_auren_ui_orchestrator(user_id: str, cognitive_profile: Any) -> AURENUIOrchestrator:
233-    """Create an AUREN UI orchestrator instance."""
---
File: ./config/agents/neuros_agent_profile.yaml
1-# NEUROS Complete Agent Profile - AUREN Framework
2:# This YAML is designed to plug directly into CrewAI with AUREN's custom extensions
3-
4-agent_profile:
--
7-  model_type: Elite cognitive and biometric optimization agent
8-  version: 1.0.0
9:  framework_compatibility: AUREN_CrewAI_v1
10-
11-  # Specializations
---
File: ./agents/my_agent.py
59-        ss[self.edit_key] = value
60-
61:    # --- CrewAI glue ---
62-    def get_crewai_agent(self) -> Agent:
63-        llm = create_llm(self.llm_provider_model, temperature=self.temperature)
---
File: ./validate_tools.py
1-#!/usr/bin/env python3
2-"""
3:CrewAI Studio Tool Validation Script
4-Checks for common issues that cause startup failures
5-"""
--
83-def main():
84-    """Main validation function"""
85:    print("🔧 CrewAI Studio Tool Validation")
86-    print("=" * 40)
87-    
---
File: ./.venv/bin/pdf2txt.py
1:#!/Users/Jason/Downloads/CrewAI-Studio-main/.venv/bin/python3.11
2-"""A command line tool for extracting text and images from PDF and
3-output it to plain text, html, xml or tags.
---
File: ./.venv/bin/dumppdf.py
1:#!/Users/Jason/Downloads/CrewAI-Studio-main/.venv/bin/python3.11
2-"""Extract pdf structure in XML format"""
3-
---
File: ./.venv/bin/jp.py
1:#!/Users/Jason/Downloads/CrewAI-Studio-main/.venv/bin/python3.11
2-
3-import sys
---
File: ./.venv/lib/python3.11/site-packages/crewai/experimental/evaluation/evaluation_listener.py
7-from crewai.task import Task
8-from crewai.utilities.events.base_event_listener import BaseEventListener
9:from crewai.utilities.events.crewai_event_bus import CrewAIEventsBus
10-from crewai.utilities.events.agent_events import (
11-    AgentExecutionStartedEvent,
--
50-            self._initialized = True
51-
52:    def setup_listeners(self, event_bus: CrewAIEventsBus):
53-        @event_bus.on(AgentExecutionStartedEvent)
54-        def on_agent_started(source, event: AgentExecutionStartedEvent):
---
File: ./.venv/lib/python3.11/site-packages/crewai/tasks/hallucination_guardrail.py
1:"""Hallucination Guardrail Placeholder for CrewAI.
2-
3-This is a no-op version of the HallucinationGuardrail for the open-source repository.
---
File: ./.venv/lib/python3.11/site-packages/crewai/tools/structured_tool.py
16-
17-    This tool intends to replace StructuredTool with a custom implementation
18:    that integrates better with CrewAI's ecosystem.
19-    """
20-
---
File: ./.venv/lib/python3.11/site-packages/crewai/security/fingerprint.py
3-
4-This module provides functionality for generating and validating unique identifiers
5:for CrewAI agents. These identifiers are used for tracking, auditing, and security.
6-"""
7-
--
94-            
95-        # Create a deterministic UUID using v5 (SHA-1)
96:        # Custom namespace for CrewAI to enhance security
97-
98:        # Using a unique namespace specific to CrewAI to reduce collision risks
99-        CREW_AI_NAMESPACE = uuid.UUID('f47ac10b-58cc-4372-a567-0e02b2c3d479')
100-        return str(uuid.uuid5(CREW_AI_NAMESPACE, seed))
---
File: ./.venv/lib/python3.11/site-packages/crewai/security/__init__.py
1-"""
2:CrewAI security module.
3-
4:This module provides security-related functionality for CrewAI, including:
5-- Fingerprinting for component identity and tracking
6-- Security configuration for controlling access and permissions
---
File: ./.venv/lib/python3.11/site-packages/crewai/security/security_config.py
2-Security Configuration Module
3-
4:This module provides configuration for CrewAI security features, including:
5-- Authentication settings
6-- Scoping rules
--
8-
9-The SecurityConfig class is the primary interface for managing security settings
10:in CrewAI applications.
11-"""
12-
--
20-class SecurityConfig(BaseModel):
21-    """
22:    Configuration for CrewAI security features.
23-
24:    This class manages security settings for CrewAI agents, including:
25-    - Authentication credentials *TODO*
26-    - Identity information (agent fingerprints)
---
File: ./.venv/lib/python3.11/site-packages/crewai/__init__.py
34-
35-    try:
36:        pixel_url = "https://api.scarf.sh/v2/packages/CrewAI/crewai/docs/00f2dad1-8334-4a39-934e-003b2e1146db"
37-
38-        req = urllib.request.Request(pixel_url)
39:        req.add_header('User-Agent', f'CrewAI-Python/{__version__}')
40-
41-        with urllib.request.urlopen(req, timeout=2):  # nosec B310
---
File: ./.venv/lib/python3.11/site-packages/crewai/agents/agent_adapters/langgraph/langgraph_adapter.py
33-
34-class LangGraphAgentAdapter(BaseAgentAdapter):
35:    """Adapter for LangGraph agents to work with CrewAI."""
36-
37-    model_config = {"arbitrary_types_allowed": True}
---
File: ./.venv/lib/python3.11/site-packages/crewai/agents/agent_adapters/langgraph/langgraph_tool_adapter.py
7-
8-class LangGraphToolAdapter(BaseToolAdapter):
9:    """Adapts CrewAI tools to LangGraph agent tool compatible format"""
10-
11-    def __init__(self, tools: Optional[List[BaseTool]] = None):
--
15-    def configure_tools(self, tools: List[BaseTool]) -> None:
16-        """
17:        Configure and convert CrewAI tools to LangGraph-compatible format.
18-        LangGraph expects tools in langchain_core.tools format.
19-        """
---
File: ./.venv/lib/python3.11/site-packages/crewai/agents/agent_adapters/base_tool_adapter.py
6-
7-class BaseToolAdapter(ABC):
8:    """Base class for all tool adapters in CrewAI.
9-
10-    This abstract class defines the common interface that all tool adapters
11:    must implement. It provides the structure for adapting CrewAI tools to
12-    different frameworks and platforms.
13-    """
---
File: ./.venv/lib/python3.11/site-packages/crewai/agents/agent_adapters/openai_agents/openai_agent_tool_adapter.py
26-        self, tools: Optional[List[BaseTool]]
27-    ) -> List[Tool]:
28:        """Convert CrewAI tools to OpenAI Assistant tool format"""
29-        if not tools:
30-            return []
---
File: ./.venv/lib/python3.11/site-packages/crewai/agents/agent_adapters/base_converter_adapter.py
3-
4-class BaseConverterAdapter(ABC):
5:    """Base class for all converter adapters in CrewAI.
6-
7-    This abstract class defines the common interface and functionality that all
---
File: ./.venv/lib/python3.11/site-packages/crewai/agents/agent_adapters/base_agent_adapter.py
9-
10-class BaseAgentAdapter(BaseAgent, ABC):
11:    """Base class for all agent adapters in CrewAI.
12-
13-    This abstract class defines the common interface and functionality that all
14-    agent adapters must implement. It extends BaseAgent to maintain compatibility
15:    with the CrewAI framework while adding adapter-specific requirements.
16-    """
17-
---
File: ./.venv/lib/python3.11/site-packages/crewai/agents/agent_builder/base_agent.py
33-
34-class BaseAgent(ABC, BaseModel):
35:    """Abstract Base Class for all third party agents compatible with CrewAI.
36-
37-    Attributes:
---
File: ./.venv/lib/python3.11/site-packages/crewai/cli/tools/main.py
26-class ToolCommand(BaseCommand, PlusAPIMixin):
27-    """
28:    A class to handle tool repository related operations for CrewAI projects.
29-    """
30-
---
File: ./.venv/lib/python3.11/site-packages/crewai/cli/command.py
24-            self._deploy_signup_error_span = telemetry.deploy_signup_error_span()
25-            console.print(
26:                "Please sign up/login to CrewAI+ before using the CLI.",
27-                style="bold red",
28-            )
---
File: ./.venv/lib/python3.11/site-packages/crewai/cli/version.py
3-
4-def get_crewai_version() -> str:
5:    """Get the version number of CrewAI running the CLI"""
6-    return importlib.metadata.version("crewai")
---
File: ./.venv/lib/python3.11/site-packages/crewai/cli/deploy/main.py
12-class DeployCommand(BaseCommand, PlusAPIMixin):
13-    """
14:    A class to handle deployment-related operations for CrewAI projects.
15-    """
16-
---
File: ./.venv/lib/python3.11/site-packages/crewai/cli/crew_chat.py
140-
141-    return (
142:        "You are a helpful AI assistant for the CrewAI platform. "
143-        "Your primary purpose is to assist users with the crew's specific tasks. "
144-        "You can answer general questions, but should guide users back to the crew's purpose afterward. "
---
File: ./.venv/lib/python3.11/site-packages/crewai/cli/cli.py
227-@crewai.command()
228-def login():
229:    """Sign Up/Login to CrewAI Enterprise."""
230-    Settings().clear()
231-    AuthenticationCommand().login()
---
File: ./.venv/lib/python3.11/site-packages/crewai/cli/plus_api.py
11-class PlusAPI:
12-    """
13:    This class exposes methods for working with the CrewAI+ API.
14-    """
15-
--
24-            "Authorization": f"Bearer {api_key}",
25-            "Content-Type": "application/json",
26:            "User-Agent": f"CrewAI-CLI/{get_crewai_version()}",
27-            "X-Crewai-Version": get_crewai_version(),
28-        }
---
File: ./.venv/lib/python3.11/site-packages/crewai/cli/templates/flow/crews/poem_crew/config/agents.yaml
1-poem_writer:
2-  role: >
3:    CrewAI Poem Writer
4-  goal: >
5:    Generate a funny, light heartedpoem about how CrewAI 
6-    is awesome with a sentence count of {sentence_count}
7-  backstory: >
---
File: ./.venv/lib/python3.11/site-packages/crewai/cli/templates/flow/crews/poem_crew/config/tasks.yaml
1-write_poem:
2-  description: >
3:    Write a poem about how CrewAI is awesome.
4-    Ensure the poem is engaging and adheres to the specified sentence count of {sentence_count}.
5-  expected_output: >
6:    A beautifully crafted poem about CrewAI, with exactly {sentence_count} sentences.
7-  agent: poem_writer
---
File: ./.venv/lib/python3.11/site-packages/crewai/cli/authentication/main.py
36-
37-    def login(self) -> None:
38:        """Sign up to CrewAI+"""
39-
40-        device_code_url = self.WORKOS_DEVICE_CODE_URL
--
43-        audience = None
44-
45:        console.print("Signing in to CrewAI Enterprise...\n", style="bold blue")
46-
47-        # TODO: WORKOS - Next line and conditional are temporary until migration to WorkOS is complete.
--
111-
112-                console.print(
113:                    "\n[bold green]Welcome to CrewAI Enterprise![/bold green]\n"
114-                )
115-                return
--
188-
189-        console.print(
190:            "Enter your CrewAI Enterprise account email: ", style="bold blue", end=""
191-        )
192-        email = input()
---
File: ./.venv/lib/python3.11/site-packages/crewai/utilities/paths.py
4-import appdirs
5-
6:"""Path management utilities for CrewAI storage and configuration."""
7-
8-def db_storage_path() -> str:
--
13-    """
14-    app_name = get_project_directory_name()
15:    app_author = "CrewAI"
16-
17-    data_dir = Path(appdirs.user_data_dir(app_name, app_author))
---
File: ./.venv/lib/python3.11/site-packages/crewai/utilities/agent_utils.py
12-from crewai.llm import LLM
13-from crewai.llms.base_llm import BaseLLM
14:from crewai.tools import BaseTool as CrewAITool
15-from crewai.tools.base_tool import BaseTool
16-from crewai.tools.structured_tool import CrewStructuredTool
--
31-
32-    for tool in tools:
33:        if isinstance(tool, CrewAITool):
34-            tools_list.append(tool.to_structured_tool())
35-        else:
---
File: ./.venv/lib/python3.11/site-packages/crewai/utilities/crew_json_encoder.py
1:"""JSON encoder for handling CrewAI specific types."""
2-
3-import json
--
11-
12-class CrewJSONEncoder(json.JSONEncoder):
13:    """Custom JSON encoder for CrewAI objects and special types."""
14-    def default(self, obj):
15-        if isinstance(obj, BaseModel):
---
File: ./.venv/lib/python3.11/site-packages/crewai/utilities/i18n.py
5-from pydantic import BaseModel, Field, PrivateAttr, model_validator
6-
7:"""Internationalization support for CrewAI prompts and messages."""
8-
9-class I18N(BaseModel):
---
File: ./.venv/lib/python3.11/site-packages/crewai/utilities/errors.py
1:"""Error message definitions for CrewAI database operations."""
2-
3-from typing import Optional
---
File: ./.venv/lib/python3.11/site-packages/crewai/utilities/events/crewai_event_bus.py
11-
12-
13:class CrewAIEventsBus:
14-    """
15-    A singleton event bus that uses blinker signals for event handling.
--
24-            with cls._lock:
25-                if cls._instance is None:  # prevent race condition
26:                    cls._instance = super(CrewAIEventsBus, cls).__new__(cls)
27-                    cls._instance._initialize()
28-        return cls._instance
--
113-
114-# Global instance
115:crewai_event_bus = CrewAIEventsBus()
---
File: ./.venv/lib/python3.11/site-packages/crewai/utilities/events/base_event_listener.py
2-from logging import Logger
3-
4:from crewai.utilities.events.crewai_event_bus import CrewAIEventsBus, crewai_event_bus
5-
6-
--
13-
14-    @abstractmethod
15:    def setup_listeners(self, crewai_event_bus: CrewAIEventsBus):
16-        pass
---
File: ./.venv/lib/python3.11/site-packages/crewai/utilities/events/__init__.py
37-    MethodExecutionFailedEvent,
38-)
39:from .crewai_event_bus import CrewAIEventsBus, crewai_event_bus
40-from .tool_usage_events import (
41-    ToolUsageFinishedEvent,
--
73-    "EventListener",
74-    "agentops_listener",
75:    "CrewAIEventsBus",
76-    "crewai_event_bus",
77-    "AgentExecutionStartedEvent",
---
File: ./.venv/lib/python3.11/site-packages/crewai/flow/persistence/__init__.py
1-"""
2:CrewAI Flow Persistence.
3-
4-This module provides interfaces and implementations for persisting flow states.
---
File: ./.venv/lib/python3.11/site-packages/crewai/flow/path_utils.py
1-"""
2:Path utilities for secure file operations in CrewAI flow module.
3-
4-This module provides utilities for secure path handling to prevent directory
---
File: ./scripts/test_whatsapp_flow.py
29-                    "timestamp": "1720500000",
30-                    "type": "text",
31:                    "text": {"body": "Hello, CrewAI!"}
32-                }]
33-            },
--
41-
42-# Process the webhook
43:result = tool._run(webhook_payload=webhook_payload, response_message="Hi! This is CrewAI responding.")
44-
45-print("=== WhatsApp Webhook Tool Result ===")
---
File: ./src/auren/app/pg_knowledge.py
21-
22-    def clear_knowledge(self):
23:        # This will clear knowledge stores in CrewAI
24:        # Get CrewAI home directory
25-        home_dir = Path.home()
26-        crewai_dir = home_dir / ".crewai"
--
48-        # Clear knowledge button
49-        st.button("Clear All Knowledge Stores", on_click=self.clear_knowledge, 
50:                  help="This will clear all knowledge stores in CrewAI, removing cached embeddings")
51-        
52-        # Display existing knowledge sources
---
File: ./src/auren/app/app/pg_knowledge.py
21-
22-    def clear_knowledge(self):
23:        # This will clear knowledge stores in CrewAI
24:        # Get CrewAI home directory
25-        home_dir = Path.home()
26-        crewai_dir = home_dir / ".crewai"
--
48-        # Clear knowledge button
49-        st.button("Clear All Knowledge Stores", on_click=self.clear_knowledge, 
50:                  help="This will clear all knowledge stores in CrewAI, removing cached embeddings")
51-        
52-        # Display existing knowledge sources
---
File: ./src/auren/app/app/my_tools.py
30-            self.file_path = file_path
31-
32:        def __call__(self, *args, **kwargs):  # Streamlit and CrewAI expect tools to be callable
33-            try:
34-                import PyPDF2
--
41-                return f"[ReadPdfTextTool] Error reading PDF – {e}"
42-
43:        # CrewAI tools may look for a run() method – alias it to __call__ for safety
44-        run = __call__
45-
--
506-            tool_id,
507-            'MCPServerAdapter',
508:            "Connect to an MCP server and expose its tools inside CrewAI.",
509-            parameters,
510-            server_url=server_url,
---
File: ./src/auren/app/app/utils.py
49-    <html>
50-        <head>
51:            <title>CrewAI-Studio result - {crew_name}</title>
52-            <style>
53-                body {{
--
102-            </button>
103-
104:            <h1>CrewAI-Studio result</h1>
105-            <div class="section">
106-                <h2>Crew Information</h2>
---
File: ./src/auren/app/app/app.py
158-            
159-def main():
160:    st.set_page_config(page_title="CrewAI Studio", page_icon="img/favicon.ico", layout="wide")
161-    load_dotenv()
162-    load_secrets_fron_env()
---
File: ./src/auren/app/my_tools.py
30-            self.file_path = file_path
31-
32:        def __call__(self, *args, **kwargs):  # Streamlit and CrewAI expect tools to be callable
33-            try:
34-                import PyPDF2
--
41-                return f"[ReadPdfTextTool] Error reading PDF – {e}"
42-
43:        # CrewAI tools may look for a run() method – alias it to __call__ for safety
44-        run = __call__
45-
--
506-            tool_id,
507-            'MCPServerAdapter',
508:            "Connect to an MCP server and expose its tools inside CrewAI.",
509-            parameters,
510-            server_url=server_url,
---
File: ./src/auren/app/utils.py
49-    <html>
50-        <head>
51:            <title>CrewAI-Studio result - {crew_name}</title>
52-            <style>
53-                body {{
--
102-            </button>
103-
104:            <h1>CrewAI-Studio result</h1>
105-            <div class="section">
106-                <h2>Crew Information</h2>
---
File: ./src/auren/app/app.py
134-def main():
135-    favicon_path = asset_loader.get_image('favicon.ico')
136:    st.set_page_config(page_title="CrewAI Studio", page_icon=favicon_path, layout="wide")
137-    load_dotenv()
138-    load_secrets_fron_env()
---
File: ./src/auren/agents/my_agent.py
61-        ss[self.edit_key] = value
62-
63:    # --- CrewAI glue ---
64-    def get_crewai_agent(self) -> Agent:
65-        llm = create_llm(self.llm_provider_model, temperature=self.temperature)
---
❌ NOT FOUND: No files with 'class.*Agent.*CrewAI'
❌ NOT FOUND: No files with 'crew\.Agent'
❌ NOT FOUND: No files with 'crew\.Task'
