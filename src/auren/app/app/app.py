# Fix Python path to find modules at project root
import os
from auren.repositories import Database, AgentRepository
from auren.repositories import TaskRepository
from auren.repositories import CrewRepository


# Robust path fixing - ensures we can find all modules
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Validate critical paths exist
def validate_environment():
    """Validate that critical files and directories exist"""
    critical_paths = [
        'agents/my_agent.py',
        'utils.py',
        'img/langgraph_logo.png'
    ]
    
    missing_paths = []
    for path in critical_paths:
        full_path = os.path.join(project_root, path)
        if not os.path.exists(full_path):
            missing_paths.append(path)
    
    if missing_paths:
        import streamlit as st
        st.error(f"⚠️ Missing critical files: {', '.join(missing_paths)}")
        st.info("Please ensure you're running from the correct directory and all files are present.")
    
    return len(missing_paths) == 0

# Run validation
validate_environment()

import streamlit as st
from streamlit import session_state as ss
import db_utils
from pg_agents import PageAgents
from pg_tasks import PageTasks
from pg_crews import PageCrews
from pg_tools import PageTools
from pg_crew_run import PageCrewRun
from pg_export_crew import PageExportCrew
from pg_results import PageResults
from pg_knowledge import PageKnowledge
from dotenv import load_dotenv
from llms import load_secrets_fron_env
import os
from tornado.web import RequestHandler
from streamlit.web.server import Server


# -----------------------------------------------------------------------------
# Meta / WhatsApp Business API – webhook verification endpoint
# -----------------------------------------------------------------------------
# We expose a lightweight Tornado handler at /webhook that performs the standard
# verification handshake expected by Meta:
#   1. Receive GET with query params: hub.mode, hub.verify_token, hub.challenge
#   2. Ensure hub.mode == "subscribe" and hub.verify_token matches
#      the WHATSAPP_VERIFY_TOKEN env var.
#   3. Respond with the hub.challenge value (plain-text) on success, or HTTP 403
#      on failure.
#
# This handler is registered with Streamlit's underlying Tornado application so
# it is served by the same process (and thus the same port that ngrok forwards
# to).  Registration happens once at runtime within `main()` to avoid duplicate
# route errors when users re-run the app from the Streamlit sidebar.


class _WebhookVerificationHandler(RequestHandler):
    """Tornado handler for GET /webhook verification handshake."""

    def get(self):
        hub_mode = self.get_argument("hub.mode", default=None)
        hub_verify_token = self.get_argument("hub.verify_token", default=None)
        hub_challenge = self.get_argument("hub.challenge", default=None)

        expected_token = os.getenv("WHATSAPP_VERIFY_TOKEN")

        # Validate request
        if hub_mode == "subscribe" and hub_verify_token and hub_challenge and hub_verify_token == expected_token:
            self.set_status(200)
            # Respond with the challenge in plain text as required by Meta
            self.write(hub_challenge)
        else:
            # Invalid token or parameters – return 403
            self.set_status(403)
            self.write("Forbidden")


def _register_webhook_route():
    """Attach the /webhook route to Streamlit's Tornado app (idempotent)."""
    # `Server.get_current()` is available in newer Streamlit versions.  Use a
    # safe getattr call so static analysis doesn’t complain when the symbol is
    # missing.
    get_current = getattr(Server, "get_current", None)  # type: ignore[attr-defined]
    if callable(get_current):
        server = get_current()
    else:
        # Fallback for older versions where `Server.get_current` lives in the
        # sub-module path or simply isn’t exposed.  This keeps runtime errors
        # away while satisfying the linter.
        try:
            from streamlit.web.server.server import Server as _LegacyServer  # type: ignore
            server = getattr(_LegacyServer, "get_current", lambda: None)()
        except Exception:
            server = None

    # If we can't access the running server, do nothing – Streamlit may not have
    # started yet (e.g., during `streamlit run` CLI auto-reload). The route will
    # be added on the first successful run.
    if not server or not hasattr(server, "_app"):
        return

    # Avoid duplicate registrations when the script is re-executed (e.g. on
    # every sidebar interaction or code change).
    if any(r.regex.pattern == r"/webhook" for r in getattr(server._app, "default_router", server._app).rules):  # type: ignore[attr-type,arg-type]
        return

    server._app.add_handlers(r".*$", [(r"/webhook", _WebhookVerificationHandler)])  # type: ignore[arg-type]


def pages():
    return {
        'Crews': PageCrews(),
        'Tools': PageTools(),
        'Agents': PageAgents(),
        'Tasks': PageTasks(),
        'Knowledge': PageKnowledge(),  # Add this line
        'Kickoff!': PageCrewRun(),
        'Results': PageResults(),
        'Import/export': PageExportCrew()
    }

def load_data():
    ss.agents = db_utils.load_agents()
    ss.tasks = db_utils.load_tasks()
    ss.crews = db_utils.load_crews()
    ss.tools = db_utils.load_tools()
    ss.enabled_tools = db_utils.load_tools_state()
    ss.knowledge_sources = db_utils.load_knowledge_sources()


def draw_sidebar():
    with st.sidebar:
        st.image("../img/langgraph_logo.png")

        if 'page' not in ss:
            ss.page = 'Crews'
        
        selected_page = st.radio('Page', list(pages().keys()), index=list(pages().keys()).index(ss.page),label_visibility="collapsed")
        if selected_page != ss.page:
            ss.page = selected_page
            st.rerun()
            
def main():
    st.set_page_config(page_title="AUREN Studio", page_icon="img/favicon.ico", layout="wide")
    load_dotenv()
    load_secrets_fron_env()
    # Register webhook verification route once the server has started.
    _register_webhook_route()
    if (str(os.getenv('AGENTOPS_ENABLED')).lower() in ['true', '1']) and not ss.get('agentops_failed', False):
        try:
            import agentops
            agentops.init(api_key=os.getenv('AGENTOPS_API_KEY'),auto_start_session=False)    
        except ModuleNotFoundError as e:
            ss.agentops_failed = True
            print(f"Error initializing AgentOps: {str(e)}")            
        
    db_utils.initialize_db()
    # Load configuration from YAML into the database before pulling it into session state
    try:
        from config.config_loader import load_config_to_db
        load_config_to_db()
    except Exception as e:
        print(f"YAML config load skipped/failed: {e}")
    load_data()
    draw_sidebar()
    PageCrewRun.maintain_session_state() #this will persist the session state for the crew run page so crew run can be run in a separate thread
    pages()[ss.page].draw()
    
if __name__ == '__main__':
    main()
