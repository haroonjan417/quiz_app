import json
import docx
import pypdf
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
    "Generate custom quizzes instantly from topics or uploaded documents using"
    " Groq AI!"
)

# Sidebar Navigation
nav_option = st.sidebar.radio(
    "Navigation",
    ["Generate AI Quiz", "Take Available Quiz", "Create Manual Question"],
)

# Reset submission state if switching tabs
if "last_nav" not in st.session_state or st.session_state.last_nav != nav_option:
  st.session_state.quiz_submitted = False
  st.session_state.last_nav = nav_option


# Helper function to extract text from files
def extract_text_from_file(uploaded_file):
  file_extension = uploaded_file.name.split(".")[-1].lower()
  text = ""
  if file_extension == "txt":
    text = uploaded_file.getvalue().decode("utf-8")
  elif file_extension == "pdf":
    reader = pypdf.PdfReader(uploaded_file)
    for page in reader.pages:
      page_text = page.extract_text()
      if page_text:
        text += page_text + "\n"
  elif file_extension in ["docx", "doc"]:
    doc = docx.Document(uploaded_file)
    for para in doc.paragraphs:
      text += para.text + "\n"
  return text


# ----------------------------------------------------
# 1. GENERATE AI QUIZ
# ----------------------------------------------------
if nav_option == "Generate AI Quiz":
  st.header("🤖 Generate Quiz with Groq AI")

  generation_mode = st.radio(
      "Choose Generation Source", ["By Topic / Subject", "From Uploaded Document"]
  )

  num_mcqs = st.slider(
      "Select Number of MCQs", min_value=10, max_value=100, value=10, step=5
  )

  source_content = ""
  quiz_title = ""

  if generation_mode == "By Topic / Subject":
    topic_input = st.text_input(
        "Enter Subject or Topic",
        placeholder=(
            "e.g., Python Programming, World History, Electrical Power Systems"
        ),
    )
    source_content = topic_input
    quiz_title = f"AI Topic: {topic_input}"
  else:
    uploaded_file = st.file_uploader(
        "Upload a document (.pdf, .docx, .txt)", type=["pdf", "docx", "txt"]
    )
    if uploaded_file is not None:
      with st.spinner("Extracting text from document..."):
        source_content = extract_text_from_file(uploaded_file)
        quiz_title = f"AI Doc: {uploaded_file.name}"

  if st.button("Generate Quiz via AI"):
    if "GROQ_API_KEY" not in st.secrets:
      st.error(
          "Groq API Key not found! Please add it to your Streamlit Cloud"
          " Secrets."
      )
    elif not source_content.strip():
      st.error("Please provide a valid topic or upload a valid document.")
    else:
      with st.spinner(
          f"Generating {num_mcqs} MCQs using Groq (openai/gpt-oss-20b)..."
          " Please wait, large quizzes take a moment."
      ):
        try:
          client = Groq(api_key=st.secrets["GROQ_API_KEY"])

          if generation_mode == "By Topic / Subject":
            prompt = f"""Generate exactly {num_mcqs} multiple choice questions about '{source_content}'.
Return ONLY a valid JSON array. Each element in the array must be an object with these exact keys:
- "question": string
- "options": list of 4 string options
- "answer": the exact string from options that is correct

Do not include any markdown code blocks, intro text, or extra commentary. Just output the raw JSON array starting with [ and ending with ]."""
          else:
            prompt = f"""Based on the following document content, generate exactly {num_mcqs} multiple choice questions.
Document content:
---
{source_content[:15000]}
---
Return ONLY a valid JSON array. Each element in the array must be an object with these exact keys:
- "question": string
- "options": list of 4 string options
- "answer": the exact string from options that is correct

Do not include any markdown code blocks, intro text, or extra commentary. Just output the raw JSON array starting with [ and ending with ]."""

          chat_completion = client.chat.completions.create(
              model="openai/gpt-oss-20b",
              messages=[
                  {
                      "role": "system",
                      "content": (
                          "You are a precise JSON-only quiz generator API. Output"
                          " valid JSON arrays only."
                      ),
                  },
                  {"role": "user", "content": prompt},
              ],
              temperature=0.5,
              max_tokens=8192,  # Increased token limit to allow up to 100 questions without truncation
          )

          response_text = chat_completion.choices[0].message.content.strip()

          # Clean markdown tags if present
          if "```" in response_text:
            parts = response_text.split("```")
            for part in parts:
              part_clean = part.strip()
              if part_clean.startswith("json"):
                part_clean = part_clean[4:].strip()
              if part_clean.startswith("[") and part_clean.endswith("]"):
                response_text = part_clean
                break

          # Final safety clean for leading/trailing text
          start_idx = response_text.find("[")
          end_idx = response_text.rfind("]")
          if start_idx != -1 and end_idx != -1:
            response_text = response_text[start_idx : end_idx + 1]

          questions_list = json.loads(response_text)

          if isinstance(questions_list, list) and len(questions_list) > 0:
            final_key = f"{quiz_title} ({len(questions_list)} Qs)"
            st.session_state.custom_quizzes[final_key] = questions_list
            st.success(
                f"✅ Successfully generated {len(questions_list)} MCQs! Switch"
                " to 'Take Available Quiz' in the sidebar to start."
            )
          else:
            st.error("Failed to parse valid questions from AI response.")
        except json.JSONDecodeError as jde:
          st.error(
              f"JSON Parsing Error: The model output was cut off or improperly"
              f" formatted. Try reducing the number of MCQs slightly or try"
              f" again. Details: {jde}"
          )
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

    for i, q in enumerate(questions):
      st.subheader(f"Q{i+1}: {q['question']}")

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
        user_answers[i] = st.radio(
            f"Select option for Q{i+1}:",
            q["options"],
            key=f"q_{selected_category}_{i}",
        )
        st.write("---")

    if not st.session_state.quiz_submitted:
      if st.button("Submit Quiz"):
        st.session_state.quiz_submitted = True
        st.rerun()
    else:
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
