import streamlit as st
import pandas as pd
import subprocess
import tempfile
import sys
import json
import zipfile
import io
from pathlib import Path

ROOT = Path(__file__).resolve().parent

st.set_page_config(
    page_title="Integrity Engine",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .block-container {
        max-width: 1400px;
        padding-top: 2.5rem;
    }
    div[data-testid="stMetric"] {
        border: 1px solid #80808030;
        padding: 20px;
        border-radius: 14px;
    }
    div.stButton > button {
        border-radius: 8px;
        min-height: 45px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("🛡️ Integrity Engine")
    st.caption("Multimodal AI Detection")

    st.divider()
    st.subheader("Configuration")

    threshold = st.slider(
        "Similarity threshold",
        min_value=0.50,
        max_value=0.95,
        value=0.70,
        step=0.05
    )

    mode = st.radio(
        "Analysis mode",
        ["Upload files", "Use sample dataset"]
    )

    st.divider()
    st.subheader("AI Models")
    st.success("MiniLM-L6-v2")
    st.success("Whisper Tiny")
    st.caption("CPU-based inference")

    st.divider()
    st.caption(
        "Semantic similarity • NLP • Speech recognition"
    )

# Header
st.title("Submission Integrity Dashboard")

st.caption(
    "Detect exact duplication, semantic plagiarism "
    "and cross-modal content similarities."
)

st.divider()

# Upload section
st.subheader("Analyze submissions")

uploads = []

if mode == "Upload files":
    uploads = st.file_uploader(
        "Upload your documents or videos",
        type=["pdf", "docx", "mp4"],
        accept_multiple_files=True
    )

    st.info(
        "Upload at least two files for peer similarity "
        "comparison. A single file can still be checked "
        "against external references."
    )
else:
    st.info("The built-in synthetic dataset will be analyzed.")

analyze = st.button(
    "Analyze Submissions",
    type="primary",
    use_container_width=True
)

# Execute existing backend
if analyze:
    if mode == "Upload files" and not uploads:
        st.warning("Please upload at least one file.")
    else:
        st.session_state.pop("integrity_results", None)

        with st.spinner("Extracting content and analyzing similarities..."):
            try:
                with tempfile.TemporaryDirectory() as temp:
                    temp_path = Path(temp)

                    input_dir = temp_path / "inputs"
                    output_dir = temp_path / "reports"

                    input_dir.mkdir()
                    output_dir.mkdir()

                    if mode == "Use sample dataset":
                        input_dir = ROOT / "sample_submissions"
                    else:
                        used_names = set()

                        for file in uploads:
                            name = Path(file.name).name

                            if name in used_names:
                                raise ValueError(
                                    "Duplicate filename: " + name
                                )

                            used_names.add(name)
                            (input_dir / name).write_bytes(
                                file.getbuffer()
                            )

                    command = [
                        sys.executable,
                        str(ROOT / "run_integrity_check.py"),
                        "--input_dir",
                        str(input_dir),
                        "--output_dir",
                        str(output_dir),
                        "--threshold",
                        str(threshold)
                    ]

                    result = subprocess.run(
                        command,
                        cwd=str(ROOT),
                        capture_output=True,
                        text=True
                    )

                    if result.returncode != 0:
                        st.error("Analysis failed.")
                        st.code(result.stderr or result.stdout)

                    elif not (output_dir / "summary.json").exists():
                        st.error("The pipeline did not generate a summary.")

                    else:
                        summary = json.loads(
                            (output_dir / "summary.json").read_text()
                        )

                        reports = {}

                        for row in summary:
                            name = row["document_id"]
                            path = output_dir / (name + ".json")

                            if path.exists():
                                reports[name] = json.loads(
                                    path.read_text()
                                )

                        archive = io.BytesIO()

                        with zipfile.ZipFile(
                            archive, "w", zipfile.ZIP_DEFLATED
                        ) as z:
                            for path in output_dir.rglob("*"):
                                if path.is_file():
                                    z.write(
                                        path,
                                        path.relative_to(output_dir)
                                    )

                        st.session_state["integrity_results"] = {
                            "summary": summary,
                            "reports": reports,
                            "archive": archive.getvalue(),
                            "threshold": threshold,
                            "logs": result.stderr
                        }

                        st.success("Analysis completed successfully.")

            except Exception as error:
                st.error(str(error))

# Results dashboard
if "integrity_results" in st.session_state:

    data = st.session_state["integrity_results"]
    summary = data["summary"]
    reports = data["reports"]

    valid = [
        item for item in summary
        if item["status"] == "ok"
    ]

    high_risk = [
        item for item in valid
        if item["total_integrity_risk"] == "HIGH"
    ]

    st.divider()
    st.subheader("Analysis overview")

    st.caption(
        f"Analysis threshold: {data['threshold']:.2f}"
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total submissions", len(summary))
    c2.metric("Processed", len(valid))
    c3.metric("High risk", len(high_risk))
    c4.metric("Skipped", len(summary) - len(valid))

    rows = []

    for item in summary:
        scores = item["scores"]

        rows.append({
            "Document": item["document_id"],
            "Peer similarity": scores.get(
                "peer_similarity_percentage"
            ),
            "External similarity": scores.get(
                "external_similarity_percentage"
            ),
            "AI indicator": scores.get(
                "ai_generated_probability"
            ),
            "Risk": item["total_integrity_risk"],
            "Status": item["status"]
        })

    df = pd.DataFrame(rows)

    st.subheader("Submission results")

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Peer similarity": st.column_config.ProgressColumn(
                "Peer similarity (%)",
                min_value=0,
                max_value=100,
                format="%.1f%%"
            ),
            "External similarity": st.column_config.ProgressColumn(
                "External similarity (%)",
                min_value=0,
                max_value=100,
                format="%.1f%%"
            ),
            "AI indicator": st.column_config.ProgressColumn(
                "AI indicator (%)",
                min_value=0,
                max_value=100,
                format="%.1f%%"
            )
        }
    )

    st.caption(
        "The AI indicator is an uncalibrated mock heuristic, "
        "not proof of AI authorship."
    )

    # Similarity chart
    st.subheader("Similarity analytics")

    chart_data = df.set_index("Document")[
        ["Peer similarity", "External similarity"]
    ]

    st.bar_chart(chart_data)

    # Detailed reports
    st.divider()
    st.subheader("Detailed integrity report")

    if reports:

        selected = st.selectbox(
            "Select a submission",
            list(reports.keys())
        )

        report = reports[selected]
        scores = report["scores"]

        def percentage(value):
            return "N/A" if value is None else f"{value:.2f}%"

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Peer similarity",
            percentage(scores.get("peer_similarity_percentage"))
        )

        c2.metric(
            "External similarity",
            percentage(scores.get("external_similarity_percentage"))
        )

        c3.metric(
            "AI indicator",
            percentage(scores.get("ai_generated_probability"))
        )

        risk = report["total_integrity_risk"]

        if risk == "HIGH":
            st.error("High integrity risk — human review required.")
        elif risk == "LOW":
            st.success("Low detected integrity risk.")
        else:
            st.warning(f"Integrity risk: {risk}")

        matches = (
            report.get("peer_matches", [])
            + report.get("multimodal_matches", [])
            + report.get("external_matches", [])
        )

        st.subheader("Matching evidence")

        if not matches:
            st.info("No matching passages were flagged.")

        for match in matches:

            score = match.get("similarity_score", 0)

            with st.expander(
                f"{match.get('matched_file', 'Reference')} "
                f"— {score * 100:.2f}% similarity",
                expanded=True
            ):

                left, right = st.columns(2)

                with left:
                    st.markdown("**Submitted content**")
                    st.write(match.get("query_passage", ""))

                with right:
                    st.markdown("**Matching source**")
                    st.write(match.get("matched_passage", ""))

                st.markdown("**Source location**")
                st.json(match.get("location", {}))

        st.write(report.get("explanations", ""))

        st.download_button(
            "Download JSON Report",
            data=json.dumps(report, indent=2),
            file_name=selected + ".json",
            mime="application/json"
        )

    st.download_button(
        "Download All Reports",
        data=data["archive"],
        file_name="integrity_reports.zip",
        mime="application/zip"
    )

    with st.expander("Execution logs"):
        st.code(data["logs"])

else:
    st.divider()
    st.subheader("Ready to analyze")
    st.caption(
        "Upload your submissions or select the sample dataset "
        "from the sidebar to get started."
    )

    c1, c2, c3 = st.columns(3)

    with c1:
        st.metric("PDF support", "Enabled")

    with c2:
        st.metric("DOCX support", "Enabled")

    with c3:
        st.metric("MP4 support", "Enabled")

st.divider()
st.caption(
    "Integrity Engine | AI/ML-powered submission analysis | "
    "Human verification required"
)
