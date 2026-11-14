"""
Olist E-Commerce Dashboard — Streamlit App
Authors: Monish L (1972260035), Prasannakumar S (1924260253),
         S Hari Surendran (1912260615)

Usage: streamlit run app/app.py
"""

import importlib
import sys
from pathlib import Path
import streamlit as st

# Ensure project root is available in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
# Resolve the app package before Streamlit's script directory can shadow it.
sys.path.insert(0, str(PROJECT_ROOT))

# Page configuration
st.set_page_config(
    page_title="Olist E-Commerce Dashboard",
    layout="wide",
    page_icon="📦",
)

# Registry of supported application pages
PAGE_MAPPING = {
    "📋 Dataset Manager": ["app.pages.dataset_manager"],
    "🗄️ Database Explorer": ["app.pages.db_explorer"],
    "🔀 Normalization": ["app.pages.normalization"],
    "📊 ER Diagram": ["app.pages.er_diagram", "app.pages.er"],
    "🔍 SQL Query Explorer": ["app.pages.sql_explorer", "app.pages.sql_query_explorer"],
    "📈 Reports": ["app.pages.reports", "app.pages.reports_page"],
    "📉 Dashboard": ["app.pages.dashboard"],
}


def render_sidebar() -> str:
    """Render sidebar navigation and project metadata footer."""
    st.sidebar.title("📦 Olist E-Commerce")
    st.sidebar.caption("DBMS Capstone Project")

    selected_page = st.sidebar.radio(
        "Navigation",
        options=list(PAGE_MAPPING.keys()),
        index=0,
    )

    st.sidebar.markdown("---")
    st.sidebar.markdown(
        """
        ### 👥 Project Team
        **DBMS Capstone Project**  
        *Brazilian E-Commerce Analytics*

        - **Monish L** (1972260035)
        - **Prasannakumar S** (1924260253)
        - **S Hari Surendran** (1912260615)

        ---
        <sub>Powered by Streamlit & MySQL</sub>
        """,
        unsafe_allow_html=True,
    )

    return selected_page


def load_and_render_page(page_name: str) -> None:
    """Dynamically import and render the selected page module with graceful error handling."""
    candidate_modules = PAGE_MAPPING.get(page_name, [])
    loaded_module = None
    import_errors = []

    for mod_path in candidate_modules:
        try:
            loaded_module = importlib.import_module(mod_path)
            break
        except ModuleNotFoundError as err:
            import_errors.append(f"`{mod_path}`: {err}")
        except Exception as err:
            import_errors.append(f"`{mod_path}` (error during load): {err}")
            break

    if loaded_module is None:
        st.error(f"❌ Page module for **{page_name}** could not be loaded.")
        st.info(
            "This module has not been implemented yet or is currently under development.\n\n"
            f"**Attempted module paths:**\n" + "\n".join(f"- {e}" for e in import_errors)
        )
        return

    if not hasattr(loaded_module, "render") or not callable(loaded_module.render):
        st.error(
            f"❌ The module `{loaded_module.__name__}` does not provide a callable `render()` function."
        )
        return

    try:
        loaded_module.render()
    except Exception as err:
        st.error(f"❌ An error occurred while rendering **{page_name}**:")
        st.exception(err)


def main() -> None:
    """Main application execution flow."""
    selected_page = render_sidebar()
    load_and_render_page(selected_page)


if __name__ == "__main__":
    main()
