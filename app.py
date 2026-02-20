"""
Streamlit chat interface for System Design Interview Assistant.

Production-quality ChatGPT-like UX wrapping Phase 6 RAG pipeline with:
- Session state conversation history (last 5 turns)
- Source citations as expandable clickable links
- Loading states during AI processing
- Error handling for off-topic/service failures
- Follow-up question context preservation
- Mobile-responsive design (3 breakpoints: phone, tablet, desktop)
- Demo question buttons for quick testing

Run: streamlit run app.py
"""

from dotenv import load_dotenv
load_dotenv()  # Load environment variables before importing generator

import streamlit as st
import pandas as pd
from pathlib import Path
from src.generation.generator import generate_answer_with_citations


# Demo questions: 5 showcase examples + 1 edge case
DEMO_QUESTIONS = [
    {
        "emoji": "🔄",
        "label": "CAP Theorem",
        "question": "What is the CAP theorem and how does it apply to distributed systems?"
    },
    {
        "emoji": "🔗",
        "label": "URL Shortener",
        "question": "How would you design a URL shortener like bit.ly?"
    },
    {
        "emoji": "⚖️",
        "label": "Consistent Hashing",
        "question": "Explain consistent hashing and when to use it in distributed systems."
    },
    {
        "emoji": "🗄️",
        "label": "SQL vs NoSQL",
        "question": "What are the trade-offs between SQL and NoSQL databases?"
    },
    {
        "emoji": "📱",
        "label": "Twitter Feed",
        "question": "How would you design Twitter's feed system for millions of users?"
    },
    {
        "emoji": "❓",
        "label": "Edge Case",
        "question": "What's the weather like today in San Francisco?"
    }
]


def inject_custom_css():
    """Inject responsive CSS with media queries for mobile, tablet, desktop."""
    css = """
    <style>
    /* Mobile optimization (< 600px) */
    @media (max-width: 600px) {
        .stChatMessage {
            padding: 0.75rem !important;
        }
        .stChatMessage p {
            font-size: 0.9rem !important;
        }
        .stButton > button {
            min-height: 44px !important;  /* Touch-friendly */
            font-size: 0.85rem !important;
        }
        .stMarkdown {
            font-size: 0.9rem !important;
        }
    }

    /* Tablet optimization (600-768px) */
    @media (min-width: 600px) and (max-width: 768px) {
        .stChatMessage {
            padding: 1rem !important;
        }
        .stChatMessage p {
            font-size: 0.95rem !important;
        }
        .stButton > button {
            font-size: 0.9rem !important;
        }
    }

    /* Desktop optimization (> 1200px) */
    @media (min-width: 1200px) {
        .main .block-container {
            max-width: 900px !important;
        }
    }

    /* Demo question buttons styling */
    .demo-buttons {
        margin-bottom: 1.5rem;
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state on first run."""
    if "messages" not in st.session_state:
        # Structure: [{"role": "user"|"assistant", "content": str, "sources": list[dict]}]
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hi! I'm your system design interview assistant. Ask me about distributed systems, databases, caching, APIs, and more!",
                "sources": []
            }
        ]


def display_demo_questions():
    """Display demo question buttons in 3-column layout (auto-stacks on mobile)."""
    st.caption("💡 Try these examples:")

    # Create 3 columns for demo buttons (auto-stacks vertically on mobile)
    col1, col2, col3 = st.columns([1, 1, 1])

    # Distribute 6 buttons across 3 columns
    for i, demo in enumerate(DEMO_QUESTIONS):
        # Select column (0, 1, 2 cycle)
        col = [col1, col2, col3][i % 3]

        with col:
            # Create button with emoji + label, full question as tooltip
            if st.button(
                f"{demo['emoji']} {demo['label']}",
                key=f"demo_{i}",
                help=demo['question'],
                use_container_width=True
            ):
                # Directly call handle_user_input with full question
                handle_user_input(demo['question'])


def display_chat_history():
    """Display conversation history from session state."""
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            # Display message content
            st.markdown(message["content"])

            # For assistant messages with sources, add expandable section
            if message["role"] == "assistant" and message.get("sources"):
                sources = message["sources"]
                with st.expander(f"📚 View Sources ({len(sources)})"):
                    for i, src in enumerate(sources, start=1):
                        # Format: **[1]** [title](url)
                        title = src.get("title", "Unknown Source")
                        url = src.get("source_url", "#")
                        st.markdown(f"**[{i}]** [{title}]({url})")

                        # Show section if available
                        section = src.get("section")
                        if section:
                            st.caption(f"Section: {section}")


def handle_user_input(prompt: str):
    """
    Handle user question submission.

    Displays user message, calls RAG pipeline, handles status codes,
    displays assistant response with sources, and maintains sliding window.
    """
    # Display user message immediately
    with st.chat_message("user"):
        st.markdown(prompt)

    # Append user message to history
    st.session_state.messages.append({
        "role": "user",
        "content": prompt,
        "sources": []
    })

    # Generate assistant response with loading indicator
    with st.chat_message("assistant"):
        with st.spinner("🤔 AI thinking..."):
            # Call RAG pipeline
            result = generate_answer_with_citations(
                query=prompt,
                top_k=5,
                min_similarity=0.3
            )

        answer = result["answer"]
        sources = result["sources"]
        status = result["status"]

        # Handle different status codes
        if status == "success":
            # Display answer
            st.markdown(answer)

            # Display sources in expander
            if sources:
                with st.expander(f"📚 View Sources ({len(sources)})"):
                    for i, src in enumerate(sources, start=1):
                        title = src.get("title", "Unknown Source")
                        url = src.get("source_url", "#")
                        st.markdown(f"**[{i}]** [{title}]({url})")

                        section = src.get("section")
                        if section:
                            st.caption(f"Section: {section}")

            # Append to history
            st.session_state.messages.append({
                "role": "assistant",
                "content": answer,
                "sources": sources
            })

        elif status == "no_context":
            # Display error message
            st.error("I don't have relevant information in my knowledge base to answer this question.")
            st.info("💡 Try asking about distributed systems, databases, caching, APIs, system design patterns, or scalability topics.")

            # Append error to history
            st.session_state.messages.append({
                "role": "assistant",
                "content": "I don't have relevant information in my knowledge base to answer this question.",
                "sources": []
            })

        elif status == "llm_error":
            # Display error message
            st.error(f"Error generating answer: {answer}")
            st.info("💡 Try rephrasing your question or ask a different system design question.")

            # Append error to history
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"Error: {answer}",
                "sources": []
            })

    # Implement sliding window: keep greeting + last 10 messages (5 turns)
    # Total = 1 greeting + 10 messages = 11 messages
    if len(st.session_state.messages) > 11:
        st.session_state.messages = [st.session_state.messages[0]] + st.session_state.messages[-10:]


def load_metrics():
    """Load evaluation metrics from CSV file."""
    metrics_path = Path("data/evaluation/ragas_metrics.csv")
    if metrics_path.exists():
        df = pd.read_csv(metrics_path)
        # Calculate mean values for each metric
        metrics = {
            "faithfulness": df["faithfulness"].mean(),
            "answer_relevancy": df["answer_relevancy"].mean(),
            "context_precision": df["context_precision"].mean()
        }
        return metrics
    return None


def load_latency_metrics():
    """Load latency metrics from evaluation results."""
    latency_path = Path("data/evaluation/latency_results.csv")
    if latency_path.exists():
        df = pd.read_csv(latency_path)
        # Skip the SUMMARY_STATISTICS row and use numeric data
        df_numeric = df[df["question"] != "SUMMARY_STATISTICS"].copy()
        if len(df_numeric) > 0 and "retrieval_ms" in df_numeric.columns:
            # Calculate p95 values from actual data
            retrieval_p95 = pd.to_numeric(df_numeric["retrieval_ms"], errors='coerce').quantile(0.95)
            end_to_end_p95 = pd.to_numeric(df_numeric["end_to_end_ms"], errors='coerce').quantile(0.95)
            return {
                "retrieval_p95": retrieval_p95,
                "end_to_end_p95": end_to_end_p95
            }
    return None


def render_sidebar():
    """Render sidebar with About, Metrics Dashboard, Tips, and Clear History."""
    with st.sidebar:
        st.header("ℹ️ About")
        st.info(
            "This assistant uses a **RAG (Retrieval-Augmented Generation)** pipeline to answer "
            "system design questions. It retrieves relevant information from curated sources "
            "(system-design-primer, ByteByteGo, engineering blogs) and generates answers with "
            "citations you can verify."
        )

        # Metrics Dashboard
        st.header("📊 Performance Metrics")

        # Load and display Ragas metrics
        metrics = load_metrics()
        if metrics:
            st.subheader("Quality Metrics (Ragas)")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric(
                    label="Faithfulness",
                    value=f"{metrics['faithfulness']:.3f}",
                    help="Measures factual accuracy of generated answers"
                )

            with col2:
                st.metric(
                    label="Answer Relevancy",
                    value=f"{metrics['answer_relevancy']:.3f}",
                    help="Measures how well the answer addresses the question"
                )

            with col3:
                st.metric(
                    label="Context Precision",
                    value=f"{metrics['context_precision']:.3f}",
                    help="Measures quality of retrieved context"
                )

        # Load and display latency metrics
        latency = load_latency_metrics()
        if latency:
            st.subheader("Latency Metrics")
            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    label="Retrieval (p95)",
                    value=f"{latency['retrieval_p95']:.1f}ms",
                    help="95th percentile retrieval time"
                )

            with col2:
                st.metric(
                    label="End-to-End (p95)",
                    value=f"{latency['end_to_end_p95']:.1f}ms",
                    help="95th percentile total response time"
                )

        st.header("💡 Tips")
        st.markdown("""
**Example questions:**

- What is the CAP theorem and how does it apply to distributed systems?
- How would you design a URL shortener like bit.ly?
- Explain consistent hashing and when to use it
- How would you design Twitter's feed system?
- What are the trade-offs between SQL and NoSQL databases?
- Explain the difference between horizontal and vertical scaling
        """)

        st.header("🗑️ Clear Chat")
        if st.button("Clear Chat History", use_container_width=True):
            # Reset to just greeting message
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": "Hi! I'm your system design interview assistant. Ask me about distributed systems, databases, caching, APIs, and more!",
                    "sources": []
                }
            ]
            st.rerun()


def main():
    """Main Streamlit app."""
    # Page config
    st.set_page_config(
        page_title="System Design Interview Assistant",
        page_icon="💬",
        layout="centered",
        initial_sidebar_state="collapsed"  # Better mobile UX
    )

    # Inject responsive CSS
    inject_custom_css()

    # Title and caption
    st.title("💬 System Design Interview Assistant")
    st.caption("Ask any system design question and get answers with sources")

    # Initialize session state
    initialize_session_state()

    # Render sidebar
    render_sidebar()

    # Display demo questions (above chat history for visibility)
    display_demo_questions()

    # Display chat history
    display_chat_history()

    # User input at bottom
    if prompt := st.chat_input("Ask a system design question..."):
        handle_user_input(prompt)


if __name__ == "__main__":
    main()
