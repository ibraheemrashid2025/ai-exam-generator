# ui/app.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
import json

from core.crew_runner import run_pipeline, generate_study_material
from storage.db_handler import save_session, get_all_sessions, get_session_by_id, delete_session

# ── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Autonomous Assessment Creator",
    page_icon="📝",
    layout="wide"
)

# ── Sidebar — Past Sessions ──────────────────────────────────────────────────
with st.sidebar:
    st.title("📚 Past Sessions")
    sessions = get_all_sessions()

    if not sessions:
        st.info("No sessions yet.")
    else:
        for s in sessions:
            col1, col2 = st.columns([3, 1])
            with col1:
                if st.button(f"📄 {s['session_name']}", key=f"load_{s['id']}"):
                    st.session_state['loaded_session'] = get_session_by_id(s['id'])
                    st.session_state['result'] = st.session_state['loaded_session']
                    st.experimental_rerun()
            with col2:
                if st.button("🗑", key=f"del_{s['id']}"):
                    delete_session(s['id'])
                    st.experimental_rerun()

# ── Main UI ──────────────────────────────────────────────────────────────────
st.title("📝 Autonomous Educational Assessment Creator")
st.markdown("Paste your syllabus or lecture notes below and generate a complete exam paper automatically.")

# Input Section
notes_input = st.text_area(
    label="📋 Paste your curriculum notes or syllabus here:",
    height=250,
    placeholder="e.g. Chapter 1: Introduction to Operating Systems\n- Process Management..."
)

session_name = st.text_input(
    label="💾 Session Name (to save this exam):",
    placeholder="e.g. OS Midterm Exam"
)

generate_btn = st.button("🚀 Generate Exam Paper")

# ── Pipeline Trigger ─────────────────────────────────────────────────────────
if generate_btn:
    if not notes_input.strip():
        st.error("Please paste your notes first.")
    elif not session_name.strip():
        st.error("Please enter a session name.")
    else:
        with st.spinner("⏳ Agents are working... This may take 30-60 seconds."):
            try:
                result = run_pipeline(notes_input)
                save_session(session_name, result)
                st.session_state['result'] = result
                st.success("✅ Exam paper generated and saved!")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")

# ── Results Display ──────────────────────────────────────────────────────────
if 'result' in st.session_state:
    result = st.session_state['result']
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📚 Curriculum", "❓ Questions", "⚖️ Difficulty", "📋 Rubric", "📊 Analytics"
    ])

    # ── Tab 1: Curriculum ────────────────────────────────────────────────────
    with tab1:
        st.subheader(f"Subject: {result['curriculum'].get('subject', 'N/A')}")
        for idx, topic in enumerate(result['curriculum'].get('topics', [])):
            with st.expander(f"📌 {topic['topic']} — Importance: {topic['importance']}"):
                for obj in topic.get('objectives', []):
                    st.markdown(f"- {obj}")
                
                st.markdown("---")
                
                # Yeh raha Learn Button jo expander ke andar hoga
                if st.button(f"📖 Learn this Topic", key=f"learn_btn_{idx}"):
                    with st.spinner(f"Generating study notes for {topic['topic']}..."):
                        study_content = generate_study_material(topic['topic'], topic.get('objectives', []))
                        st.success("Study Material Generated!")
                        st.markdown(study_content)

    # ── Tab 2: Questions ─────────────────────────────────────────────────────
    with tab2:
        questions = result['questions'].get('questions', [])
        st.markdown(f"**Total Questions Generated: {len(questions)}**")
        for q in questions:
            with st.expander(f"{q['question_id']} — [{q['question_type']}] {q['question_text'][:60]}..."):
                st.markdown(f"**Topic:** {q['topic']}")
                st.markdown(f"**Question:** {q['question_text']}")
                if q.get('options'):
                    for opt in q['options']:
                        st.markdown(f"- {opt}")
                st.markdown(f"✅ **Answer:** {q['correct_answer']}")

    # ── Tab 3: Difficulty ────────────────────────────────────────────────────
    with tab3:
        dist = result['difficulty'].get('difficulty_distribution', {})
        col1, col2, col3 = st.columns(3)
        col1.metric("🟢 Easy", dist.get('Easy', 0))
        col2.metric("🟡 Medium", dist.get('Medium', 0))
        col3.metric("🔴 Hard", dist.get('Hard', 0))
        
        st.markdown("---")
        
        for q in result['difficulty'].get('calibrated_questions', []):
            badge = {"Easy": "🟢", "Medium": "🟡", "Hard": "🔴"}.get(q['difficulty'], "⚪")
            with st.expander(f"{badge} {q['question_id']} — {q['difficulty']} — {q['question_text'][:60]}..."):
                st.markdown(f"**Reason:** {q['difficulty_reason']}")

    # ── Tab 4: Rubric ────────────────────────────────────────────────────────
    with tab4:
        st.markdown(f"### 🎯 Total Marks: {result['rubric'].get('total_marks', 0)}")
        for item in result['rubric'].get('rubric', []):
            with st.expander(f"{item['question_id']} — {item['marks']} mark(s) — {item['question_text'][:60]}..."):
                st.markdown(f"**Correct Answer:** {item['correct_answer']}")
                st.markdown(f"**Marking Guide:** {item['marking_guide']}")

    # ── Tab 5: Analytics ─────────────────────────────────────────────────────
    with tab5:
        analytics = result['analytics']
        col1, col2 = st.columns(2)
        col1.metric("📝 Total Questions", analytics.get('total_questions', 0))
        col2.metric("🎯 Total Marks", analytics.get('total_marks', 0))
        
        st.markdown("---")
        st.subheader("📊 Topic Coverage")
        for tc in analytics.get('topic_coverage', []):
            st.markdown(f"**{tc['topic']}** — {tc['questions_count']} questions — "
                       f"{tc['marks_allocated']} marks — {tc['coverage_percentage']}%")
            st.progress(min(tc['coverage_percentage'] / 100, 1.0))
        
        if analytics.get('gaps'):
            st.markdown("---")
            st.subheader("⚠️ Coverage Gaps")
            for gap in analytics['gaps']:
                st.warning(gap)
        
        st.markdown("---")
        st.subheader("📝 Summary")
        st.info(analytics.get('summary', 'No summary available.'))
        
        st.markdown("---")
        st.download_button(
            label="⬇️ Download Full Result (JSON)",
            data=json.dumps(result, indent=2),
            file_name=f"{session_name if session_name else 'exam'}_result.json",
            mime="application/json"
        )