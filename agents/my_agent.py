# Fix import path issues by providing self-contained utilities
import os
import sys
import yaml
from typing import List, Dict, Any, Optional, Protocol
from datetime import datetime
import functools
import random
import string

# Self-contained utilities to avoid import path issues in testing
def _local_rnd_id(length: int = 8) -> str:
    """Generate random ID locally to avoid import path dependencies in testing"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def _local_fix_columns_width():
    """Mock function to avoid import dependencies - replaced by actual Streamlit in production"""
    pass

# Try to import from production locations, fall back to local implementations
try:
    # First, try the shim module approach
    from utils import rnd_id, fix_columns_width
except ImportError:
    try:
        # Ensure app directory in path for imports of utils, db_utils, llms
        APP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'app'))
        if APP_DIR not in sys.path:
            sys.path.insert(0, APP_DIR)
        from utils import rnd_id, fix_columns_width
    except ImportError:
        # Fall back to local implementations for testing
        rnd_id = _local_rnd_id
        fix_columns_width = _local_fix_columns_width

from shared_utils import deep_merge, generate_kafka_topics

# Tool Protocol for better type safety
class ToolProtocol(Protocol):
    """Protocol for tool validation and type safety"""
    name: str
    tool_id: str
    
    def create_tool(self) -> Any: ...
    def is_valid(self, show_warning: bool = False) -> bool: ...
    def get_parameter_names(self) -> List[str]: ...

# Module-level cached LLM providers (performance optimization)
@functools.lru_cache(maxsize=1)
def _get_cached_llm_providers() -> List[str]:
    """Cached LLM provider list to avoid redundant API calls"""
    try:
        from llms import llm_providers_and_models
        return llm_providers_and_models()
    except Exception:
        return ["openai:gpt-4"]
# Fix: Import correct Agent class for LangGraph 0.6.2+
try:
    from langgraph.prebuilt.chat_agent_executor import AgentExecutor as Agent
    from langgraph.prebuilt import create_react_agent
except ImportError as e1:
    try:
        from langgraph.prebuilt import create_react_agent
        Agent = create_react_agent  # Use as Agent type for compatibility
    except ImportError as e2:
        raise ImportError(
            "❌ LangGraph Agent class not found. "
            "Install langgraph>=0.6.2 or check import paths."
        ) from e2

# Protected Streamlit import to prevent crashes in CI/testing
try:
    import streamlit as st
    from streamlit import session_state as ss
    STREAMLIT_AVAILABLE = True
except ImportError:
    # Mock streamlit for testing environments
    class MockStreamlit:
        def warning(self, msg): print(f"WARNING: {msg}")
        def info(self, msg): print(f"INFO: {msg}")
        def error(self, msg): print(f"ERROR: {msg}")
        def success(self, msg): print(f"SUCCESS: {msg}")
        def rerun(self): pass
    st = MockStreamlit()
    ss = {}
    STREAMLIT_AVAILABLE = False


# Safe YAML configuration loader (security best practice)
@functools.lru_cache(maxsize=32)  # Cache agent configs for performance
def load_agent_config(config_path: str) -> Dict[str, Any]:
    """
    Load agent configuration with safe YAML parsing.
    Uses yaml.safe_load to prevent object deserialization exploits.
    Guards against None return from empty files (CVE protection).
    Cached for performance optimization.
    """
    try:
        with open(config_path, 'r') as f:
            result = yaml.safe_load(f)
            # Guard against None from empty YAML files (CVE protection)
            config = result or {}
            
            # Validate basic config structure if present
            if config and not isinstance(config, dict):
                if STREAMLIT_AVAILABLE:
                    st.warning(f"Invalid YAML structure in {config_path}: Expected dict, got {type(config)}")
                return {}
            
            return config
    except FileNotFoundError:
        return {}
    except yaml.YAMLError as e:
        if STREAMLIT_AVAILABLE:
            st.warning(f"YAML parsing error in {config_path}: {e}")
        else:
            print(f"WARNING: YAML parsing error in {config_path}: {e}")
        return {}
    except Exception as e:
        if STREAMLIT_AVAILABLE:
            st.error(f"Unexpected error loading {config_path}: {e}")
        else:
            print(f"ERROR: Unexpected error loading {config_path}: {e}")
        return {}

# Lazy import helpers to avoid circular dependencies
def _save_agent_to_db(agent_obj) -> None:
    """Lazy DB import to break circular dependency loops"""
    from app import db_utils as _db_utils
    _db_utils.save_agent(agent_obj)

def _delete_agent_from_db(agent_id) -> None:
    """Lazy DB import to break circular dependency loops"""
    from app import db_utils as _db_utils
    _db_utils.delete_agent(agent_id)

def _create_llm(llm_provider_model, temperature=0.1) -> Any:
    """Lazy LLM import to prevent circular dependencies"""
    from llms import create_llm
    return create_llm(llm_provider_model, temperature=temperature)

def _get_llm_providers_and_models() -> List[str]:
    """Lazy LLM providers import - now uses module-level cache"""
    return _get_cached_llm_providers()


class MyAgent:
    """
    Professional specialist blueprint for the 9-agent AUREN OS.
    
    Features:
    - LangGraph-compatible agent wrapper
    - Streamlit UI controls with proper form batching
    - Kafka topic integration for event-driven architecture
    - YAML configuration loading with deep-merge support
    - Lazy imports to prevent circular dependencies
    - Production-ready type safety and validation
    """
    
    def __init__(self, id=None, role=None, backstory=None, goal=None, temperature=None, 
                 allow_delegation=False, verbose=False, cache=None, llm_provider_model=None, 
                 max_iter=None, created_at=None, tools=None, knowledge_source_ids=None, 
                 memory_files=None, schedule_triggers=None, agent_config_path=None, 
                 domain="biometric", **kwargs):
        
        self.id = id or "A_" + rnd_id()
        self.role = role or "Senior Researcher"
        self.backstory = backstory or "Driven by curiosity, you're at the forefront of innovation, eager to explore and share knowledge that could change the world."
        self.goal = goal or "Uncover groundbreaking technologies in AI"
        self.temperature = temperature or 0.1
        self.allow_delegation = allow_delegation if allow_delegation is not None else False
        self.verbose = verbose if verbose is not None else True
        self.cache = cache if cache is not None else True
        self.max_iter = max_iter or 25
        self.created_at = created_at or datetime.now().isoformat()
        self.tools = tools or []
        self.knowledge_source_ids = knowledge_source_ids or []
        
        # LLM configuration with lazy loading
        self.llm_provider_model = llm_provider_model or self._get_default_llm_model()
        
        # Session state management (prevents global collisions)
        self.edit_key = f'edit_{self.id}'
        if self.edit_key not in ss:
            ss[self.edit_key] = False
        
        # Kafka topic integration (Confluent-style naming)
        self.domain = domain
        topics = generate_kafka_topics(self.role, domain)
        self.ingest_topic = topics['ingest']
        self.output_topic = topics['output']
        self.status_topic = topics['status']
        
        # YAML configuration loading with validation
        self.agent_config_path = agent_config_path
        self.config = {}
        if agent_config_path:
            if os.path.exists(agent_config_path):
                self.config = load_agent_config(agent_config_path)
                # Validate loaded config structure
                if self.config and not isinstance(self.config, dict):
                    if STREAMLIT_AVAILABLE:
                        st.warning(f"Invalid config structure in {agent_config_path}")
                    self.config = {}
                else:
                    self._apply_config_overrides()
            else:
                if STREAMLIT_AVAILABLE:
                    st.info(f"Config file not found: {agent_config_path} (using defaults)")
                else:
                    print(f"INFO: Config file not found: {agent_config_path} (using defaults)")
        
        # Advanced parameters for future features
        self.memory_files = memory_files or []
        self.schedule_triggers = schedule_triggers or []
        
        # Store unexpected keyword arguments for future compatibility
        self._extra_fields = kwargs
        
        # Agent status tracking
        self.status = kwargs.get('status', 'active')
        self.enabled = kwargs.get('enabled', True)
        self.locked = kwargs.get('locked', False)  # Prevents deletion if true

    def _get_default_llm_model(self) -> str:
        """Get default LLM model with module-level caching"""
        providers = _get_cached_llm_providers()
        return providers[0] if providers else "openai:gpt-4"
    
    def _apply_config_overrides(self) -> None:
        """Apply YAML configuration overrides using deep merge with validation"""
        if not self.config or not isinstance(self.config, dict):
            return
            
        # Validate config structure before applying overrides
        try:
            # Apply personality overrides
            personality = self.config.get('personality', {})
            if personality and isinstance(personality, dict):
                if 'identity' in personality:
                    identity = personality['identity']
                    if isinstance(identity, dict):
                        self.role = identity.get('role', self.role)
                        self.backstory = identity.get('background', self.backstory)
            
            # Apply voice characteristics
            voice = self.config.get('voice_characteristics', {})
            if voice and isinstance(voice, dict):
                if 'base_tone' in voice:
                    # Map voice characteristics to temperature
                    tone_map = {'curious': 0.3, 'structured': 0.1, 'empathetic': 0.4, 'analytical': 0.1}
                    base_tone = voice.get('base_tone')
                    if isinstance(base_tone, str) and base_tone in tone_map:
                        self.temperature = tone_map[base_tone]
                        
        except Exception as e:
            if STREAMLIT_AVAILABLE:
                st.warning(f"Error applying config overrides: {e}")
            else:
                print(f"WARNING: Error applying config overrides: {e}")

    # Properties with session state integration
    @property
    def edit(self) -> bool:
        """Get edit state from session"""
        return ss.get(self.edit_key, False) if STREAMLIT_AVAILABLE else False

    @edit.setter
    def edit(self, value: bool) -> None:
        """Set edit state in session"""
        if STREAMLIT_AVAILABLE:
            ss[self.edit_key] = value

    # LangGraph integration with proper type safety  
    def get_langgraph_agent(self) -> Optional[Agent]:
        """
        Create LangGraph agent with proper imports and type safety.
        Uses lazy imports to prevent circular dependencies.
        """
        try:
            llm = _create_llm(self.llm_provider_model, temperature=self.temperature)
        except Exception as e:
            st.error(f"Failed to create LLM: {e}")
            return None
            
        tools = []
        try:
            tools = [tool.create_tool() for tool in self.tools if hasattr(tool, 'create_tool')]
        except Exception as e:
            st.warning(f"Tool creation warning: {e}")

        knowledge_sources = []
        if 'knowledge_sources' in ss and self.knowledge_source_ids:
            for ks_id in self.knowledge_source_ids:
                ks = next((k for k in ss.knowledge_sources if k.id == ks_id), None)
                if ks:
                    try:
                        knowledge_sources.append(ks)
                    except Exception as e:
                        st.warning(f"Error loading knowledge source {ks.id}: {str(e)}")

        if knowledge_sources:
            st.info(f"✅ Loaded {len(knowledge_sources)} knowledge sources for {self.role}")

        try:
            # Use the modern LangGraph create_react_agent API
            return create_react_agent(
                model=llm,
                tools=tools,
                state_modifier=f"You are {self.role}. {self.backstory} Your goal: {self.goal}"
            )
        except Exception as e:
            st.error(f"Failed to create LangGraph agent: {e}")
            return None

    # Kafka integration methods
    def publish_status_update(self, status_data: Dict[str, Any]) -> None:
        """Publish agent status to Kafka topic (future implementation)"""
        # TODO: Wire to actual Kafka producer
        raise NotImplementedError(
            f"Kafka status publishing not implemented. "
            f"Topic: {self.status_topic}, Data: {status_data}"
        )
    
    def emit_kpi(self, metric: str, value: float, unit: str, confidence: float = 1.0) -> None:
        """
        Emit KPI following universal schema: [metric, value, unit, confidence, timestamp]
        Compatible with Flink CEP pattern matching.
        """
        kpi_data = {
            "metric": metric,
            "value": value,
            "unit": unit,
            "confidence": confidence,
            "timestamp": datetime.now().isoformat(),
            "agent": self.role,
            "topic": self.output_topic
        }
        # TODO: Wire to actual Kafka producer for Flink CEP
        if self.verbose:
            st.info(f"📊 KPI Emitted: {metric} = {value} {unit}")
        
        raise NotImplementedError(
            f"Kafka KPI emission not implemented. "
            f"Topic: {self.output_topic}, KPI: {kpi_data}"
        )

    # Persistence helpers
    def delete(self) -> bool:
        """Delete agent with protection for locked agents"""
        if self.locked:
            st.warning("🔒 Cannot delete locked agent. Clone or unlock first.")
            return False
            
        if STREAMLIT_AVAILABLE and hasattr(ss, 'agents'):
            ss.agents = [agent for agent in ss.agents if agent.id != self.id]
        _delete_agent_from_db(self.id)
        return True

    def clone(self, new_role_suffix: str = "Copy") -> 'MyAgent':
        """Create a copy of this agent for safe experimentation"""
        new_agent = MyAgent(
            role=f"{self.role} ({new_role_suffix})",
            backstory=self.backstory,
            goal=self.goal,
            temperature=self.temperature,
            allow_delegation=self.allow_delegation,
            verbose=self.verbose,
            cache=self.cache,
            llm_provider_model=self.llm_provider_model,
            max_iter=self.max_iter,
            tools=self.tools.copy(),
            knowledge_source_ids=self.knowledge_source_ids.copy(),
            domain=self.domain
        )
        return new_agent

    # Validation helpers
    def get_tool_display_name(self, tool) -> str:
        """Generate display-friendly tool names"""
        try:
            first_param_name = tool.get_parameter_names()[0] if tool.get_parameter_names() else None
            first_param_value = tool.parameters.get(first_param_name, '') if first_param_name else ''
            return f"{tool.name} ({first_param_value if first_param_value else tool.tool_id})"
        except Exception:
            return f"{getattr(tool, 'name', 'Unknown Tool')}"

    def is_valid(self, show_warning: bool = False) -> bool:
        """Validate agent configuration"""
        valid = True
        
        # Validate tools
        for tool in self.tools:
            if hasattr(tool, 'is_valid') and not tool.is_valid(show_warning=show_warning):
                if show_warning:
                    st.warning(f"⚠️ Tool {getattr(tool, 'name', 'Unknown')} is not valid")
                valid = False
        
        # Validate LLM provider
        try:
            available_models = _get_cached_llm_providers()
            if self.llm_provider_model not in available_models:
                if show_warning:
                    st.warning(f"⚠️ LLM model {self.llm_provider_model} not available")
                valid = False
        except Exception:
            if show_warning:
                st.warning("⚠️ Could not validate LLM provider")
            valid = False
            
        return valid

    def validate_llm_provider_model(self) -> None:
        """Auto-correct invalid LLM provider models with module-level caching"""
        try:
            available_models = _get_cached_llm_providers()
            if self.llm_provider_model not in available_models:
                self.llm_provider_model = available_models[0] if available_models else "openai:gpt-4"
        except Exception:
            self.llm_provider_model = "openai:gpt-4"

    # Enhanced Streamlit UI with UX improvements
    def draw(self, key: Optional[str] = None) -> None:
        """
        Enhanced Streamlit UI with professional UX improvements:
        - Tooltips for complex controls
        - Locked agent protection
        - Better validation feedback
        - Professional styling
        """
        self.validate_llm_provider_model()
        
        # Professional expander title with status indicators
        status_icon = "🔒" if self.locked else ("✅" if self.is_valid() else "❗")
        model_short = self.llm_provider_model.split(':')[1] if ':' in self.llm_provider_model else self.llm_provider_model
        expander_title = f"{status_icon} {self.role[:50]} - {model_short}"
        
        form_key = f'form_{self.id}_{key}' if key else f'form_{self.id}'

        if self.edit and not self.locked:
            with st.expander(f"🔧 Editing: {self.role}", expanded=True):
                with st.form(key=form_key):
                    # Basic configuration
                    self.role = st.text_input("Role", value=self.role, 
                                            help="Define the agent's primary role and expertise area")
                    
                    self.backstory = st.text_area("Backstory", value=self.backstory, height=100,
                                                help="Agent's background and experience that informs its approach")
                    
                    self.goal = st.text_area("Goal", value=self.goal, height=80,
                                           help="Primary objective this agent is designed to achieve")
                    
                    # Advanced configuration in columns
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        self.allow_delegation = st.checkbox("Allow delegation", value=self.allow_delegation,
                                                          help="Enable this agent to delegate tasks to other agents")
                        self.verbose = st.checkbox("Verbose", value=self.verbose,
                                                 help="Enable detailed logging and debugging output")
                        self.cache = st.checkbox("Cache", value=self.cache,
                                               help="Cache responses to improve performance")
                    
                    with col2:
                        self.temperature = st.slider("Temperature", value=self.temperature, 
                                                    min_value=0.0, max_value=1.0, step=0.05,
                                                    help="Controls randomness: Lower = more focused, Higher = more creative")
                        
                        self.max_iter = st.number_input("Max Iterations", value=self.max_iter, 
                                                       min_value=1, max_value=100,
                                                       help="Maximum number of reasoning steps before timeout")
                    
                    # LLM Provider selection
                    try:
                        available_models = _get_cached_llm_providers()
                        current_index = available_models.index(self.llm_provider_model) if self.llm_provider_model in available_models else 0
                        self.llm_provider_model = st.selectbox("LLM Provider and Model", 
                                                             options=available_models, 
                                                             index=current_index,
                                                             help="Select the language model provider and specific model")
                    except Exception:
                        st.warning("⚠️ Could not load LLM providers")
                    
                    # Tools selection
                    if hasattr(ss, 'tools') and ss.tools:
                        enabled_tools = [tool for tool in ss.tools]
                        tools_key = f"{self.id}_tools_{key}" if key else f"{self.id}_tools"
                        selected_tools = st.multiselect(
                            "Select Tools",
                            [self.get_tool_display_name(tool) for tool in enabled_tools],
                            default=[self.get_tool_display_name(tool) for tool in self.tools],
                            key=tools_key,
                            help="Choose which tools this agent can use"
                        )
                    
                    # Knowledge sources selection
                    if hasattr(ss, 'knowledge_sources') and ss.knowledge_sources:
                        knowledge_source_options = [ks.id for ks in ss.knowledge_sources]
                        knowledge_source_labels = {ks.id: ks.name for ks in ss.knowledge_sources}

                        valid_knowledge_sources = [ks_id for ks_id in self.knowledge_source_ids 
                                                 if ks_id in knowledge_source_options]
                        if len(valid_knowledge_sources) != len(self.knowledge_source_ids):
                            self.knowledge_source_ids = valid_knowledge_sources
                            _save_agent_to_db(self)

                        ks_key = f"knowledge_sources_{self.id}_{key}" if key else f"knowledge_sources_{self.id}"
                        selected_knowledge_sources = st.multiselect(
                            "Knowledge Sources",
                            options=knowledge_source_options,
                            default=valid_knowledge_sources,
                            format_func=lambda x: knowledge_source_labels.get(x, "Unknown"),
                            key=ks_key,
                            help="Select knowledge bases this agent can access"
                        )
                        self.knowledge_source_ids = selected_knowledge_sources

                    # Kafka topic configuration (read-only display)
                    with st.expander("🔗 Kafka Integration", expanded=False):
                        st.code(f"Ingest Topic: {self.ingest_topic}")
                        st.code(f"Output Topic: {self.output_topic}")
                        st.code(f"Status Topic: {self.status_topic}")

                    submitted = st.form_submit_button("💾 Save Changes", type="primary")
                    if submitted:
                        if hasattr(ss, 'tools') and ss.tools:
                            enabled_tools = [tool for tool in ss.tools]
                            self.tools = [tool for tool in enabled_tools 
                                        if self.get_tool_display_name(tool) in selected_tools]
                        self.set_editable(False)
                        st.success("✅ Agent updated successfully!")

        else:
            # Read-only view with professional styling
            fix_columns_width()
            with st.expander(expander_title, expanded=False):
                # Agent overview
                st.markdown(f"**🎭 Role:** {self.role}")
                st.markdown(f"**📖 Backstory:** {self.backstory}")
                st.markdown(f"**🎯 Goal:** {self.goal}")
                
                # Configuration details in columns
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"**🤝 Allow delegation:** {self.allow_delegation}")
                    st.markdown(f"**💬 Verbose:** {self.verbose}")
                    st.markdown(f"**💾 Cache:** {self.cache}")
                
                with col2:
                    st.markdown(f"**🌡️ Temperature:** {self.temperature}")
                    st.markdown(f"**🔄 Max Iterations:** {self.max_iter}")
                    st.markdown(f"**🤖 LLM:** {self.llm_provider_model}")
                
                # Tools and knowledge sources
                if self.tools:
                    st.markdown("**🛠️ Tools:**")
                    for tool in self.tools:
                        st.markdown(f"  • {self.get_tool_display_name(tool)}")
                
                if self.knowledge_source_ids and hasattr(ss, 'knowledge_sources'):
                    knowledge_sources = [ks for ks in ss.knowledge_sources if ks.id in self.knowledge_source_ids]
                    if knowledge_sources:
                        st.markdown("**📚 Knowledge Sources:**")
                        for ks in knowledge_sources:
                            st.markdown(f"  • {ks.name}")
                
                # Kafka topics (collapsed by default)
                with st.expander("🔗 Event Streams", expanded=False):
                    st.code(f"📥 Input:  {self.ingest_topic}")
                    st.code(f"📤 Output: {self.output_topic}")
                    st.code(f"📊 Status: {self.status_topic}")
                
                # Validation status
                self.is_valid(show_warning=True)
                
                # Action buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    if not self.locked:
                        btn_key = f"edit_btn_{rnd_id()}"
                        st.button("✏️ Edit", on_click=self.set_editable, args=(True,), 
                                key=btn_key, help="Edit this agent's configuration")
                    else:
                        st.button("🔒 Locked", disabled=True, help="This agent is locked for safety")
                
                with col2:
                    clone_key = f"clone_btn_{rnd_id()}"
                    if st.button("📋 Clone", key=clone_key, help="Create a copy of this agent"):
                        cloned = self.clone()
                        if hasattr(ss, 'agents'):
                            ss.agents.append(cloned)
                        st.success(f"✅ Cloned as '{cloned.role}'")
                        st.rerun()
                
                with col3:
                    if not self.locked:
                        del_key = f"del_btn_{rnd_id()}"
                        st.button("🗑️ Delete", on_click=self.delete, key=del_key, 
                                help="Delete this agent (cannot be undone)")

    def set_editable(self, edit: bool) -> None:
        """Set agent edit state and save to database"""
        self.edit = edit
        _save_agent_to_db(self)
        if not edit and STREAMLIT_AVAILABLE:
            st.rerun()

    def to_dict(self) -> Dict[str, Any]:
        """Export agent configuration as dictionary"""
        return {
            'id': self.id,
            'role': self.role,
            'backstory': self.backstory,
            'goal': self.goal,
            'temperature': self.temperature,
            'allow_delegation': self.allow_delegation,
            'verbose': self.verbose,
            'cache': self.cache,
            'llm_provider_model': self.llm_provider_model,
            'max_iter': self.max_iter,
            'created_at': self.created_at,
            'tools': [tool.to_dict() if hasattr(tool, 'to_dict') else str(tool) for tool in self.tools],
            'knowledge_source_ids': self.knowledge_source_ids,
            'ingest_topic': self.ingest_topic,
            'output_topic': self.output_topic,
            'status_topic': self.status_topic,
            'domain': self.domain,
            'status': self.status,
            'enabled': self.enabled,
            'locked': self.locked
        } 