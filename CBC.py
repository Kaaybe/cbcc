import time
from datetime import datetime
import json
import streamlit as st
import requests # Added this import to the top of the file

# --- 1. SET PAGE CONFIGURATION ---
st.set_page_config(
    page_title="CBC AI Tutor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CUSTOM CSS ---
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
    }
    .stChatMessage {
        background-color: #1e2127;
        border-radius: 10px;
        padding: 10px;
        margin: 5px 0;
    }
    .header-banner {
        text-align: center;
        padding: 30px;
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        border-radius: 15px;
        margin-bottom: 20px;
    }
    .stat-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# --- 3. INITIALIZE SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

if "materials_generated" not in st.session_state:
    st.session_state.materials_generated = 0

if "current_grade" not in st.session_state:
    st.session_state.current_grade = "Grade 4"

if "current_subject" not in st.session_state:
    st.session_state.current_subject = "Mathematics"

if "user_role" not in st.session_state:
    st.session_state.user_role = "teacher"

# --- 4. CBC CURRICULUM DATA ---
CBC_SUBJECTS = {
    "Lower Primary (Grade 1-3)": [
        "Mathematics", "English", "Kiswahili", "Environmental Activities",
        "Hygiene and Nutrition", "Religious Education", "Movement and Creative Activities"
    ],
    "Upper Primary (Grade 4-6)": [
        "Mathematics", "English", "Kiswahili", "Science and Technology",
        "Social Studies", "Religious Education", "Creative Arts", "Physical Education"
    ],
    "Junior Secondary (Grade 7-9)": [
        "Mathematics", "English", "Kiswahili", "Integrated Science",
        "Social Studies", "Religious Education", "Creative Arts and Sports",
        "Pre-Technical Studies", "Business Studies", "Agriculture"
    ]
}

# CBC Curriculum Knowledge Base
CBC_CURRICULUM_CONTEXT = """
KENYAN CBC (COMPETENCY-BASED CURRICULUM) CONTEXT:

CORE COMPETENCIES:
1. Communication and Collaboration
2. Critical Thinking and Problem Solving
3. Imagination and Creativity
4. Citizenship
5. Digital Literacy
6. Learning to Learn
7. Self-Efficacy

VALUES:
- Love, Responsibility, Respect, Unity, Peace, Patriotism, Integrity

ASSESSMENT LEVELS:
- Exceeds Expectations (80-100%)
- Meets Expectations (60-79%)
- Approaches Expectations (40-59%)
- Below Expectations (<40%)

KENYAN EDUCATIONAL CONTEXT:
- Use Kenyan examples (Kenyan currency, local environments, Kenyan history)
- Include cultural relevance (Kenyan communities, traditions)
- Reference local resources and materials
- Use Kenyan English spellings and terminology
- Consider urban and rural school contexts
"""

SUBJECT_KNOWLEDGE = {
    "Mathematics": {
        "Grade 1-3": ["Numbers 0-1000", "Addition", "Subtraction", "Shapes", "Measurement", "Money (KES)", "Time", "Data handling"],
        "Grade 4-6": ["Fractions", "Decimals", "Multiplication", "Division", "Geometry", "Perimeter", "Area", "Graphs", "Algebra basics", "Ratio"],
        "Grade 7-9": ["Algebra", "Linear equations", "Quadratic equations", "Geometry", "Trigonometry", "Statistics", "Probability", "Financial math"]
    },
    "Science and Technology": {
        "Grade 4-6": ["Living things", "Plants", "Animals", "Human body", "Health", "Matter", "Forces", "Energy", "Technology", "Environment"],
        "Grade 7-9": ["Biology", "Chemistry", "Physics", "Scientific method", "Cells", "Chemical reactions", "Motion", "Electricity", "Magnetism"]
    },
    "English": {
        "All Grades": ["Reading comprehension", "Writing skills", "Grammar", "Vocabulary", "Speaking", "Listening", "Literature", "Composition"]
    },
    "Kiswahili": {
        "All Grades": ["Kusoma", "Kuandika", "Sarufi", "Mazungumzo", "Fasihi", "Insha"]
    },
    "Social Studies": {
        "Grade 4-9": ["Kenyan history", "Geography of Kenya", "Government", "Counties", "Culture", "Trade", "Transportation", "Maps", "Resources"]
    }
}

# --- 5. AI HELPER FUNCTION ---
# Changed to a synchronous function and moved 'requests' import to the top
def call_claude_api(messages, system_prompt):
    """
    Calls Claude API to generate intelligent responses.
    """
    try:
        # Prepare the API call
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01"
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 4000,
                "system": system_prompt,
                "messages": messages
            },
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            return data['content'][0]['text']
        else:
            return f"Error: Unable to generate response (Status: {response.status_code})"

    except Exception as e:
        return f"Error connecting to AI: {str(e)}"

def get_system_prompt(grade, subject, role):
    """
    Creates a specialized system prompt based on context.
    """

    # Get subject-specific knowledge
    subject_info = ""
    for subj_key, topics in SUBJECT_KNOWLEDGE.items():
        if subj_key in subject:
            grade_num = int(grade.split()[1])
            if grade_num <= 3:
                key = "Grade 1-3"
            elif grade_num <= 6:
                key = "Grade 4-6"
            else:
                key = "Grade 7-9"

            if key in topics:
                subject_info = f"\n\nKEY TOPICS FOR {subject} ({grade}):\n" + ", ".join(topics[key])
            elif "All Grades" in topics:
                subject_info = f"\n\nKEY TOPICS FOR {subject}:\n" + ", ".join(topics["All Grades"])

    role_context = ""
    if role == "teacher":
        role_context = """
You are assisting a TEACHER. Focus on:
- Creating comprehensive teaching materials
- Providing lesson planning support
- Generating assessments with marking schemes
- Offering pedagogical strategies
- Including differentiation techniques
- Providing classroom management tips
"""
    else:
        role_context = """
You are assisting a STUDENT. Focus on:
- Clear, simple explanations
- Step-by-step problem solving
- Encouraging and supportive tone
- Making concepts relatable
- Providing practice opportunities
- Building confidence
"""

    return f"""You are an expert Kenyan CBC (Competency-Based Curriculum) educational assistant.

{CBC_CURRICULUM_CONTEXT}

CURRENT CONTEXT:
- Grade Level: {grade}
- Subject: {subject}
- User Role: {role.upper()}

{subject_info}

{role_context}

RESPONSE GUIDELINES:
1. Use Kenyan context and examples (KES currency, Kenyan cities, local environment)
2. Align with CBC competencies and values
3. Provide culturally relevant content
4. Use appropriate difficulty level for the grade
5. Include practical, hands-on elements when possible
6. Be encouraging and supportive
7. Format responses clearly with headings and structure
8. For mathematics, show step-by-step working
9. For assessments, include marking schemes
10. Use Kenyan English spelling (e.g., "organisation" not "organization")

When creating materials:
- Worksheets: Include instructions, questions, and answer spaces
- Lesson plans: Follow 40-minute structure (intro, development, conclusion)
- Quizzes: Provide questions and answers
- Explanations: Break down concepts simply
- Assignments: Make them practical and relevant

Always be helpful, accurate, and aligned with CBC standards."""

# --- 6. SIDEBAR ---
with st.sidebar:
    st.title("🎓 CBC AI Tutor")

    # User role
    st.session_state.user_role = st.radio(
        "I am a:",
        ["teacher", "student"],
        format_func=lambda x: "👨‍🏫 Teacher" if x == "teacher" else "👨‍🎓 Student"
    )

    st.markdown("---")

    # Grade level
    st.session_state.current_grade = st.selectbox(
        "Grade Level",
        ["Grade 1", "Grade 2", "Grade 3", "Grade 4", "Grade 5", "Grade 6",
         "Grade 7", "Grade 8", "Grade 9"],
        index=3
    )

    # Determine curriculum level
    grade_num = int(st.session_state.current_grade.split()[1])
    if grade_num <= 3:
        curriculum_level = "Lower Primary (Grade 1-3)"
    elif grade_num <= 6:
        curriculum_level = "Upper Primary (Grade 4-6)"
    else:
        curriculum_level = "Junior Secondary (Grade 7-9)"

    # Subject
    st.session_state.current_subject = st.selectbox(
        "Subject",
        CBC_SUBJECTS[curriculum_level]
    )

    # Statistics
    st.markdown("---")
    st.markdown("### 📊 Session Stats")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"""
            <div class="stat-box">
                <h2>💬 {len(st.session_state.messages)//2}</h2>
                <p>Conversations</p>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div class="stat-box">
                <h2>📚 {st.session_state.materials_generated}</h2>
                <p>Materials</p>
            </div>
        """, unsafe_allow_html=True)

    # Quick actions
    st.markdown("---")
    st.markdown("### ⚡ Quick Actions")

    if st.button("🗑️ Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.materials_generated = 0
        st.rerun()

    # Example prompts
    st.markdown("---")
    st.markdown("### 💡 What I Can Do")

    capabilities = [
        "📝 Create worksheets",
        "📋 Generate lesson plans",
        "✅ Make quizzes & tests",
        "💡 Explain concepts",
        "🎯 Design activities",
        "📊 Help with homework",
        "🎴 Create flashcards",
        "📖 Provide study notes"
    ]

    for cap in capabilities:
        st.markdown(f"- {cap}")

    st.markdown("---")
    st.markdown("### 🔍 Example Requests")

    examples = {
        "teacher": [
            "Create a worksheet on fractions for Grade 4",
            "Write a lesson plan about photosynthesis",
            "Generate a quiz on Kenyan history",
            "Make flashcards for Kiswahili verbs"
        ],
        "student": [
            "Help me understand fractions",
            "Explain photosynthesis simply",
            "Give me practice problems for multiplication",
            "How do I solve this math problem?"
        ]
    }

    current_examples = examples[st.session_state.user_role]
    for ex in current_examples:
        if st.button(ex, use_container_width=True, key=ex):
            st.session_state.messages.append({"role": "user", "content": ex})
            st.rerun()

# --- 7. MAIN CHAT INTERFACE ---
st.markdown("""
    <div class="header-banner">
        <h1>🎓 CBC AI Tutor</h1>
        <p>Your Intelligent Kenyan Curriculum Assistant</p>
    </div>
""", unsafe_allow_html=True)

# Display settings
col1, col2, col3 = st.columns(3)
with col1:
    st.info(f"📚 **Grade:** {st.session_state.current_grade}")
with col2:
    st.info(f"📖 **Subject:** {st.session_state.current_subject}")
with col3:
    role_emoji = "👨‍🏫" if st.session_state.user_role == "teacher" else "👨‍🎓"
    st.info(f"{role_emoji} **Role:** {st.session_state.user_role.title()}")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input(f"Ask me anything about {st.session_state.current_subject}..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Generate AI response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("Thinking... 🤔")

        # Prepare conversation history for API
        api_messages = []
        for msg in st.session_state.messages[-10:]:  # Last 10 messages for context
            api_messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        # Get system prompt
        system_prompt = get_system_prompt(
            st.session_state.current_grade,
            st.session_state.current_subject,
            st.session_state.user_role
        )

        # Simulate API call (you'll need to implement actual API integration)
        try:
            # In production, uncomment the API call below
            # response = call_claude_api(api_messages, system_prompt) # No 'await' needed now
            
            # PLACEHOLDER RESPONSE (remove this in production)
            response = f"""I understand you're asking about: "{prompt}"\n\nFor {st.session_state.current_grade} {st.session_state.current_subject}, let me help you.\n\n**Note:** This is a demo version. To activate full AI capabilities:\n\n1. Add your Anthropic API key\n2. Uncomment the API call in the code\n3. Ensure you have a `requirements.txt` file with `streamlit`, `requests`, and `anthropic` (if using the Anthropic SDK).\n\n**What I can do when fully activated:**\n- Generate custom worksheets with questions\n- Create detailed lesson plans\n- Explain concepts step-by-step\n- Provide practice problems with solutions\n- Make assessments with marking schemes\n- Help with homework\n- Create study materials\n\n**For now, try the example prompts in the sidebar!**\n\nWould you like me to create a specific type of material? I can generate:\n- 📝 Worksheets\n- 📋 Lesson Plans\n- ✅ Quizzes/Tests\n- 🎴 Flashcards\n- 💡 Explanations\n"""

            # Display response with typing effect
            full_response = ""
            words = response.split()
            for i in range(0, len(words), 5):
                chunk = " ".join(words[i:i+5]) + " "
                full_response += chunk
                time.sleep(0.05)
                message_placeholder.markdown(full_response + "▌")

            message_placeholder.markdown(full_response)

            # Add to chat history
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            st.session_state.materials_generated += 1

        except Exception as e:
            error_msg = f"Sorry, I encountered an error: {str(e)}\n\nPlease try again or rephrase your question."
            message_placeholder.markdown(error_msg)
            st.session_state.messages.append({"role": "assistant", "content": error_msg})

# Welcome message if no messages
if len(st.session_state.messages) == 0:
    with st.chat_message("assistant"):
        if st.session_state.user_role == "teacher":
            welcome = f"""👋 **Welcome, Teacher!**\n\nI'm your CBC AI Tutor, ready to help you create amazing learning materials for {st.session_state.current_grade} {st.session_state.current_subject}.\n\n**I can help you:**\n- 📝 Create custom worksheets\n- 📋 Generate comprehensive lesson plans\n- ✅ Make quizzes and assessments\n- 🎯 Design engaging activities\n- 🎴 Create flashcards\n- 💡 Explain teaching strategies\n\n**Just ask me!** For example:\n- "Create a worksheet on fractions"\n- "Write a lesson plan about photosynthesis"\n- "Generate a quiz on Kenyan history"\n\nWhat would you like me to create today?"""
        else:
            welcome = f"""👋 **Hello, Student!**\n\nI'm here to help you learn {st.session_state.current_subject} for {st.session_state.current_grade}!\n\n**I can help you:**\n- 💡 Understand difficult concepts\n- 📝 Practice with worksheets\n- ✅ Prepare for tests\n- 📖 Study and revise\n- 🎯 Do your homework\n\n**Just ask me!** For example:\n- "Help me understand fractions"\n- "Explain photosynthesis simply"\n- "Give me practice problems"\n\nWhat topic are you studying today?"""

        st.markdown(welcome)

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>🇰🇪 <strong>CBC AI Tutor</strong> - Powered by Claude AI</p>
    <p>Aligned with Kenyan Competency-Based Curriculum</p>
</div>
""", unsafe_allow_html=True)
