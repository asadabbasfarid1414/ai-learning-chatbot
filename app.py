
import streamlit as st
import json
from google import genai

st.set_page_config(
    page_title="AI Learning Chatbot",
    page_icon="🤖",
    layout="centered"
)

st.title("🤖 AI Learning Chatbot")
st.caption("AI Tutor | Quiz Generator | Automatic Result Checker")

# Securely load API key from Streamlit Secrets
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    client = genai.Client(api_key=api_key)
except Exception:
    st.error("Gemini API key missing. Add GEMINI_API_KEY in Streamlit Secrets.")
    st.stop()

MODEL = "gemini-flash-lite-latest"


def ask_ai(question):
    prompt = f"""
You are a helpful AI tutor.
Understand the user's language and reply in the same language.
- English question: answer in English.
- Roman Urdu question: answer in Roman Urdu.
- Urdu script question: answer in Urdu script.
Explain in simple words and give examples when useful.

User question: {question}
"""
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt
    )
    return response.text


def create_quiz(topic, number, difficulty, language):
    prompt = f"""
Create a Machine Learning and AI learning quiz.

Topic: {topic}
Number of questions: {number}
Difficulty: {difficulty}
Language: {language}

Return ONLY valid JSON in this exact structure:
{{
  "title": "Quiz title",
  "questions": [
    {{
      "question": "Question text",
      "options": {{
        "A": "Option A",
        "B": "Option B",
        "C": "Option C",
        "D": "Option D"
      }},
      "answer": "A",
      "explanation": "Short explanation"
    }}
  ]
}}

Rules:
- Include exactly {number} questions.
- Each question must have four options A, B, C, D.
- Exactly one correct answer per question.
- The answer field must contain only A, B, C, or D.
- Keep all quiz text in the requested language.
- Do not include Markdown fences or text outside JSON.
"""
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config={"response_mime_type": "application/json"}
    )
    return json.loads(response.text)


# Tabs
chat_tab, quiz_tab = st.tabs(["💬 Ask AI", "📝 Generate Quiz"])

with chat_tab:
    st.subheader("Ask your AI Tutor")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_question = st.chat_input("Apna question likhein...")

    if user_question:
        st.session_state.messages.append({
            "role": "user",
            "content": user_question
        })

        with st.chat_message("user"):
            st.markdown(user_question)

        with st.chat_message("assistant"):
            with st.spinner("AI jawab tayyar kar raha hai..."):
                try:
                    answer = ask_ai(user_question)
                    st.markdown(answer)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer
                    })
                except Exception as e:
                    st.error(f"AI error: {e}")

    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()


with quiz_tab:
    st.subheader("Create Your Quiz")

    with st.form("quiz_form"):
        topic = st.text_input(
            "Quiz Topic",
            placeholder="e.g. Machine Learning"
        )

        number = st.number_input(
            "Number of Questions",
            min_value=1,
            max_value=20,
            value=5
        )

        difficulty = st.selectbox(
            "Difficulty",
            ["Easy", "Medium", "Hard"]
        )

        language = st.selectbox(
            "Language",
            ["English", "Roman Urdu", "Urdu"]
        )

        generate = st.form_submit_button("Generate Quiz")

    if generate:
        if not topic.strip():
            st.warning("Please enter a quiz topic.")
        else:
            try:
                with st.spinner("Quiz generate ho raha hai..."):
                    st.session_state.quiz = create_quiz(
                        topic, int(number), difficulty, language
                    )
                    st.session_state.quiz_submitted = False
                    st.session_state.quiz_answers = {}
            except Exception as e:
                st.error(f"Quiz generation error: {e}")

    if "quiz" in st.session_state:
        quiz = st.session_state.quiz
        st.divider()
        st.subheader(quiz.get("title", "Your Quiz"))

        if not st.session_state.get("quiz_submitted", False):
            with st.form("answer_form"):
                for i, question in enumerate(quiz["questions"]):
                    st.markdown(f"**Q{i+1}. {question['question']}**")

                    options = question["options"]
                    choice = st.radio(
                        "Select your answer:",
                        options=list(options.keys()),
                        format_func=lambda key: f"{key}) {options[key]}",
                        key=f"answer_{i}",
                        index=None
                    )
                    st.session_state.quiz_answers[i] = choice
                    st.divider()

                submitted = st.form_submit_button("Submit Answers")

            if submitted:
                st.session_state.quiz_submitted = True
                st.rerun()

        else:
            score = 0
            questions = quiz["questions"]

            st.subheader("📊 Your Quiz Result")

            for i, question in enumerate(questions):
                correct = question["answer"].upper()
                student = st.session_state.quiz_answers.get(i)
                st.markdown(f"**Q{i+1}. {question['question']}**")

                if student == correct:
                    score += 1
                    st.success(f"Correct! Your answer: {student}")
                else:
                    st.error(
                        f"Incorrect. Your answer: {student or 'Not answered'}"
                    )
                    st.info(f"Correct answer: {correct}")

                st.write(f"Explanation: {question['explanation']}")
                st.divider()

            total = len(questions)
            percentage = (score / total) * 100

            st.metric("Obtained Marks", f"{score} / {total}")
            st.metric("Percentage", f"{percentage:.1f}%")

            if st.button("Generate Another Quiz"):
                del st.session_state.quiz
                st.session_state.quiz_submitted = False
                st.session_state.quiz_answers = {}
                st.rerun()
