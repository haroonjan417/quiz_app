import json
import streamlit as st
from groq import Groq

# Page Configuration
st.set_page_config(
    page_title="AI-Powered Quiz App", page_icon="📝", layout="centered"
)

# Initialize Session State
if "custom_quizzes" not in st.session_state:
  st.session_state.custom_quizzes = {
      "General Science (Sample)": [
          {
              "question": "What is the chemical symbol for water?",
              "options": ["H2O", "CO2", "O2", "NaCl"],
              "answer": "H2O",
          },
          {
              "question": "Which planet is known as the Red Planet?",
              "options": ["Venus", "Mars", "Jupiter", "Saturn"],
              "answer": "Mars",
          },
      ]
  }

if "quiz_submitted" not in st.session_state:
  st.session_state.quiz_submitted = False

# App Header
st.title("📝 AI-Powered Interactive Quiz Generator")
st.write(
    "Generate custom quizzes instantly using Groq AI or take available quizzes!"
)

# Sidebar Navigation
nav_option = st.sidebar.radio(
    "Navigation",
    ["Generate AI Quiz", "Take Available Quiz", "Create Manual Question"],
)

# Reset submission state if switching navigation tabs
if "last_nav" not in st.session_state or st.session_state.last_nav != nav_option:
  st.session_state.quiz_submitted = False
  st.session_state.last_nav = nav_option

# ----------------------------------------------------
# 1. GENERATE AI QUIZ
# ----------------------------------------------------
if nav_option == "Generate AI Quiz":
  st.header("🤖 Generate Quiz with Groq AI")

  topic_input = st.text_input(
      "Enter Subject or Topic",
      placeholder="e.g., Python Programming, World History, Electrical Power Systems",
  )
  num_mcqs = st.slider(
      "Select Number of MCQs", min_value=10, max_value=100, value=10, step=5
  )

  if st.button("Generate Quiz via AI"):
    if "GROQ_API_KEY" not in st.secrets:
      st.error(
          "Groq API Key not found! Please add it to your Streamlit Cloud"
          " Secrets."
      )
    elif not topic_input.strip():
      st.error("Please enter a valid topic or subject.")
    else:
      with st.spinner(
          f"Generating {num_mcqs} MCQs on '{topic_input}' using Groq AI..."
      ):
        try:
          client = Groq(api_key=st.secrets["GROQ_API_KEY"])
          prompt = f"""Generate exactly {num_mcqs} multiple choice questions about '{topic_input}'.
Return ONLY a valid JSON array. Each element in the array must be an object with these exact keys:
- "question": string
- "options": list of 4 string options
- "answer": the exact string from options that is correct

Do not include any markdown code blocks or extra text. Just output the raw JSON array starting with [ and ending with ]."""

          chat_completion = client.chat.completions.create(
              model="llama-3.3-70b-versatile",
              messages=[
                  {
                      "role": "system",
                      "content": (
                          "You are a precise JSON-only quiz generator API."
                      ),
                  },
                  {"role": "user", "content": prompt},
              ],
              temperature=0.7,
          )

          response_text = chat_completion.choices[0].message.content.strip()

          if response_text.startswith("```"):
            response_text = response_text.split("```")[1]
            if response_text.startswith("json"):
              response_text = response_text[4:]
            response_text = response_text.strip()

          questions_list = json.loads(response_text)

          if isinstance(questions_list, list) and len(questions_list) > 0:
            quiz_key = f"AI: {topic_input} ({len(questions_list)} Qs)"
            st.session_state.custom_quizzes[quiz_key] = questions_list
            st.success(
                f"✅ Successfully generated {len(questions_list)} MCQs for"
                f" '{topic_input}'! Switch to 'Take Available Quiz' in the"
                " sidebar to start."
            )
          else:
            st.error("Failed to parse valid questions from AI response.")
        except Exception as e:
          st.error(f"Error generating quiz: {e}")

# ----------------------------------------------------
# 2. TAKE AVAILABLE QUIZ
# ----------------------------------------------------
elif nav_option == "Take Available Quiz":
  st.header("🎯 Take a Quiz")

  all_categories = list(st.session_state.custom_quizzes.keys())
  selected_category = st.selectbox("Choose a quiz category:", all_categories)

  questions = st.session_state.custom_quizzes[selected_category]

  if not questions:
    st.warning("No questions found in this category.")
  else:
    st.info(f"**Total Questions:** {len(questions)}")

    user_answers = {}
    score = 0

    # Render questions
    for i, q in enumerate(questions):
      st.subheader(f"Q{i+1}: {q['question']}")

      # If already submitted, show results with ticks and crosses
      if st.session_state.quiz_submitted:
        selected_option = st.session_state.get(f"q_{selected_category}_{i}")
        correct_option = q["answer"]

        for opt in q["options"]:
          if opt == correct_option and opt == selected_option:
            st.markdown(f"✅ **{opt} (Correct)**")
          elif opt == correct_option:
            st.markdown(f"✅ **{opt} (Correct Answer)**")
          elif opt == selected_option:
            st.markdown(f"❌ **{opt} (Your Answer)**")
          else:
            st.markdown(f"- {opt}")

        if selected_option == correct_option:
          score += 1
        st.write("---")

      else:
        # Interactive radio selection before submission
        user_answers[i] = st.radio(
            f"Select option for Q{i+1}:",
            q["options"],
            key=f"q_{selected_category}_{i}",
        )
        st.write("---")

    # Submit or Retake buttons
    if not st.session_state.quiz_submitted:
      if st.button("Submit Quiz"):
        st.session_state.quiz_submitted = True
        st.rerun()
    else:
      # Calculate score display
      total = len(questions)
      percentage = (score / total) * 100
      st.subheader("📊 Quiz Results")
      st.success(f"🎉 Your Score: {score} / {total} ({percentage:.1f}%)")

      if score == total:
        st.balloons()
        st.write("🌟 Flawless! Perfect score!")
      elif score >= total * 0.7:
        st.write("👍 Great job! Solid understanding.")
      else:
        st.write("💡 Keep studying and try generating another quiz!")

      if st.button("🔄 Retake Quiz"):
        st.session_state.quiz_submitted = False
        st.rerun()

# ----------------------------------------------------
# 3. CREATE MANUAL QUESTION
# ----------------------------------------------------
elif nav_option == "Create Manual Question":
  st.header("🛠️ Add Manual Question")
  category_name = st.text_input("Category Name", value="My Custom Quiz")

  with st.form(key="add_question_form"):
    new_question = st.text_input("Question Statement")
    opt1 = st.text_input("Option A")
    opt2 = st.text_input("Option B")
    opt3 = st.text_input("Option C")
    opt4 = st.text_input("Option D")
    correct_opt = st.selectbox(
        "Select the Correct Option", [opt1, opt2, opt3, opt4]
    )

    add_btn = st.form_submit_button("Add Question")

    if add_btn:
      if not category_name.strip():
        st.error("Please enter a category name.")
      elif not new_question or not opt1 or not opt2 or not opt3 or not opt4:
        st.error("Please fill in all fields.")
      else:
        if category_name not in st.session_state.custom_quizzes:
          st.session_state.custom_quizzes[category_name] = []

        st.session_state.custom_quizzes[category_name].append({
            "question": new_question,
            "options": [opt1, opt2, opt3, opt4],
            "answer": correct_opt,
        })
        st.success(f"✅ Question added to '{category_name}'!")
