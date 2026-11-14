"""
Page 4: ER Diagram
Authors: Monish L (1972260035), Prasannakumar S (1924260253),
         S Hari Surendran (1912260615)
"""

import streamlit as st

try:
    from app.er import (
        GRAPHVIZ_AVAILABLE,
        er_to_pdf,
        er_to_png,
        generate_er_diagram,
        generate_er_fallback,
    )
except ImportError:
    from er import (
        GRAPHVIZ_AVAILABLE,
        er_to_pdf,
        er_to_png,
        generate_er_diagram,
        generate_er_fallback,
    )


@st.cache_data
def get_cached_er_diagram():
    """
    Generate and cache the Graphviz ER diagram object.
    Prevents re-introspecting the database or re-building graph nodes on each rerun.
    """
    return generate_er_diagram()


@st.cache_data
def get_cached_er_png(_dot) -> bytes:
    """
    Render and cache the ER diagram PNG bytes.
    The leading underscore on _dot prevents Streamlit from attempting to hash the Digraph.
    """
    return er_to_png(_dot)


@st.cache_data
def get_cached_er_pdf(_dot) -> bytes:
    """
    Render and cache the ER diagram PDF bytes.
    """
    return er_to_pdf(_dot)


def render() -> None:
    """
    Render the Entity-Relationship Diagram page.
    Generates dynamic visual ER diagrams using Graphviz or displays a
    formatted text schema fallback when binaries are unavailable.
    """
    st.title("Entity-Relationship Diagram")
    st.markdown(
        "Interactive Entity-Relationship visualization for the 3NF Olist E-Commerce schema. "
        "Shows all 9 entity tables, primary keys (`[PK]`), column data types, and 1-to-many (`1 : N`) "
        "foreign key relationships."
    )

    if GRAPHVIZ_AVAILABLE:
        try:
            dot = get_cached_er_diagram()
        except Exception as exc:
            dot = None
            st.warning(f"Unable to generate ER diagram: {exc}")

        if dot is not None:
            try:
                png_bytes = get_cached_er_png(dot)
                pdf_bytes = get_cached_er_pdf(dot)

                st.image(
                    png_bytes,
                    caption="Olist Database Entity-Relationship Diagram (Crow's Foot 1:N Notation)",
                    use_container_width=True,
                )

                st.markdown("### Export Options")
                col1, col2 = st.columns(2)
                with col1:
                    st.download_button(
                        label="📥 Download PNG",
                        data=png_bytes,
                        file_name="olist_er_diagram.png",
                        mime="image/png",
                        use_container_width=True,
                    )
                with col2:
                    st.download_button(
                        label="📄 Download PDF",
                        data=pdf_bytes,
                        file_name="olist_er_diagram.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
            except Exception as render_err:
                st.warning(f"Error rendering Graphviz image: {render_err}")
                st.code(generate_er_fallback(), language="text")
        else:
            st.warning("Database schema could not be generated into an ER diagram. Displaying schema fallback text below.")
            st.code(generate_er_fallback(), language="text")
    else:
        st.info("ℹ️ Graphviz binary (`dot`) is not installed or not found on the system PATH. Displaying text-based schema specification.")
        st.code(generate_er_fallback(), language="text")

        st.markdown(
            """
            > [!TIP]
            > **How to install Graphviz for graphical diagram rendering:**
            > - **Windows (winget):** `winget install Graphviz.Graphviz`
            > - **Windows (Chocolatey):** `choco install graphviz`
            > - **macOS (Homebrew):** `brew install graphviz`
            > - **Linux (Ubuntu/Debian):** `sudo apt-get install -y graphviz`
            >
            > After installation, ensure the `bin/` directory containing `dot.exe` (e.g. `C:\\Program Files\\Graphviz\\bin`) 
            > is added to your environment `PATH` variable and restart the Streamlit server.
            """
        )
