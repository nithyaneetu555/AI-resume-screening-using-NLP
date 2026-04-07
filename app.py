import streamlit as st
import requests

# Page config
st.set_page_config(page_title="AI Resume Screener", layout="wide")

# Title
st.markdown("<h1 style='text-align: center;'>🤖 AI Resume Screening System</h1>", unsafe_allow_html=True)
st.markdown("---")

# Layout (2 columns)
col1, col2 = st.columns(2)

with col1:
    jd = st.text_area("📄 Enter Job Description", height=200)

with col2:
    uploaded_files = st.file_uploader(
        "📂 Upload Resumes",
        type=["pdf", "txt"],
        accept_multiple_files=True
    )

st.markdown("---")

analyze = st.button("🚀 Analyze Resumes")

if analyze:

    if not jd:
        st.warning("Please enter job description")

    elif not uploaded_files:
        st.warning("Upload resumes first")

    else:
        files = []

        for file in uploaded_files:
            files.append(
                ("files", (file.name, file.getvalue(), file.type))
            )

        with st.spinner("Analyzing resumes... ⏳"):
            response = requests.post(
                "http://127.0.0.1:8000/upload-resume",
                files=files,
                data={"job_description": jd}
            )

        result = response.json()

        st.success("Analysis Complete ✅")

        st.markdown("## 📊 Results")

        top_candidate = result["ranked_resumes"][0]
        st.markdown("## 🥇 Top Candidate")
        # ⭐ Highlight
        st.info("⭐ Best Match Found")
        # # 🎯 Color score
        if top_candidate["score"] > 75:
            st.success(f"Score: {top_candidate['score']}")
        elif top_candidate["score"] > 50:
            st.warning(f"Score: {top_candidate['score']}")
        else:
            st.error(f"Score: {top_candidate['score']}")

# 📊 Animated progress (ONLY HERE)
        progress = st.progress(0)
        for i in range(int(top_candidate["score"])):
            progress.progress(i + 1)

# 🧠 Skills badges
        st.markdown("**Skills:**")
        for skill in top_candidate["matched_skills"]:
            st.markdown(f"- 🔹 {skill}")

# 📄 Expandable preview
        with st.expander("📄 View Resume Preview"):
            st.write(top_candidate["resume_preview"])

        for res in result["ranked_resumes"]:
            st.subheader(f"🏆 Rank #{res['rank']}")


# 🎯 Color-coded score
        
            if res["score"] > 75:
                st.success(f"Score: {res['score']}")
            elif res["score"] > 50:
                st.warning(f"Score: {res['score']}")
            else:
                st.error(f"Score: {res['score']}")


# 📊 Normal progress (NO animation here)
            st.progress(res["score"] / 100)


# 🧠 Skill badges
            st.write("Skills:")
            for skill in res["matched_skills"]:
                st.markdown(f"- 🔹 {skill}")

            #one resume preview
            with st.expander("📄 View Resume Preview"):
                st.write(res["resume_preview"])
                st.divider()