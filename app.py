import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="Interactive Quiz App", page_icon="📝", layout="centered"
)

# Initialize Session State for storing custom quizzes & scores
if "custom_quizzes" not in st.session_state:
    st.session_state.custom_quizzes = {
        "General Science": [
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
        ],
        "Mathematics": [
            {
                "question": "What is 9 multiplied by 8?",
                "options": ["72", "81", "64", "56"],
                "answer": "72",
            },
            {
                "question": "What is the square root of 144?",
                "options": ["10", "11", "12", "14"],
                "answer": "12",
            },
        ],
    }

# App Header
st.title("📝 Interactive Quiz Application")
st.write(
    "Test your knowledge or build your own custom quizzes easily using Streamlit!"
)

# Sidebar Navigation
nav_option = st.sidebar.radio(
    "Navigation", ["Take a Quiz", "Create a Custom Quiz"]
)

# ----------------------------------------------------
# TAB 1: TAKE A QUIZ
# ----------------------------------------------------
if nav_option == "Take a Quiz":
    st.header("🎯 Select a Quiz")

    # Combine default & custom quizzes
    all_categories = list(st.session_state.custom_quizzes.keys())
    selected_category = st.selectbox(
        "Choose a subject category:", all_categories
    )

    questions = st.session_state.custom_quizzes[selected_category]

    if not questions:
        st.warning("No questions found in this category yet. Add some!")
    else:
        # Quiz Form
        with st.form(key="quiz_form"):
            user_answers = {}
            for i, q in enumerate(questions):
                st.subheader(f"Q{i+1}: {q['question']}")
                user_answers[i] = st.radio(
                    f"Select option for Q{i+1}:", q["options"], key=f"q_{i}"
                )
                st.write("---")

            submitted = st.form_submit_button("Submit Quiz")

            if submitted:
                score = 0
                total = len(questions)
                for i, q in enumerate(questions):
                    if user_answers[i] == q["answer"]:
                        score += 1

                st.success(f"🎉 You finished the quiz! Your Score: {score}/{total}")

                if score == total:
                    st.balloons()
                    st.write("🌟 Excellent! Perfect score!")
                elif score >= total / 2:
                    st.write("👍 Good job! Keep practicing.")
                else:
                    st.write("💡 Keep studying, you can do better next time!")

# ----------------------------------------------------
# TAB 2: CREATE A CUSTOM QUIZ
# ----------------------------------------------------
elif nav_option == "Create a Custom Quiz":
    st.header("🛠️ Add New Questions to a Quiz")

    # Option to select existing or create a new category
    category_mode = st.radio(
        "Category Choice", ["Add to Existing Category", "Create New Category"]
    )

    if category_mode == "Add to Existing Category":
        category_name = st.selectbox(
            "Select Category", list(st.session_state.custom_quizzes.keys())
        )
    else:
        category_name = st.text_input("Enter New Category Name")

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
                st.error("Please enter a valid category name.")
            elif not new_question or not opt1 or not opt2 or not opt3 or not opt4:
                st.error("Please fill in all question and option fields.")
            else:
                if category_name not in st.session_state.custom_quizzes:
                    st.session_state.custom_quizzes[category_name] = []

                st.session_state.custom_quizzes[category_name].append({
                    "question": new_question,
                    "options": [opt1, opt2, opt3, opt4],
                    "answer": correct_opt,
                })
                st.success(
                    f"✅ Question successfully added to '{category_name}'!"
                )
