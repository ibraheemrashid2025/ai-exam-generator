# core/crew_runner.py
# Yeh file poori agent pipeline run karti hai
import json
import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv() 

# ── Helper Function: Clean JSON ──────────────────────────────────────────────
# Yeh LLM ke response se extra text aur markdown remove karega
def parse_json_response(text: str) -> dict:
    text = text.strip()
    start = text.find('{')
    end = text.rfind('}') + 1
    if start != -1 and end != 0:
        clean_text = text[start:end]
        return json.loads(clean_text)
    return json.loads(text)

# ── LLM Setup ───────────────────────────────────────────────────────────────
def get_llm():
    return ChatGroq(
        api_key=os.getenv("GROQ_API_KEY"),
        model="llama-3.3-70b-versatile",
        temperature=0.3,
    )

# ── Agent 1: Curriculum Agent ────────────────────────────────────────────────
def run_curriculum_agent(notes_text: str) -> dict:
    llm = get_llm()
    messages = [
        SystemMessage(content="""You are a Curriculum Analysis Expert.
Your job is to read academic notes or syllabus text and extract:
1. The overall subject name
2. All key topics
3. Learning objectives for each topic
4. Importance level (High/Medium/Low) for each topic
You MUST respond with valid JSON only. No explanation, no markdown, no extra text.
Use this exact format:
{
  "subject": "subject name",
  "topics": [
    {
      "topic": "topic name",
      "objectives": ["objective 1", "objective 2"],
      "importance": "High"
    }
  ]
}"""),
        HumanMessage(content=f"Extract topics and objectives from these notes:\n\n{notes_text}")
    ]
    response = llm.invoke(messages)
    return parse_json_response(response.content)

# ── Agent 2: Question Agent ──────────────────────────────────────────────────
def run_question_agent(curriculum_output: dict) -> dict:
    llm = get_llm()
    messages = [
        SystemMessage(content="""You are an Expert Exam Question Writer.
Given topics and learning objectives, generate exam questions.
Create a mix of:
- MCQs (4 options each, label them A/B/C/D)
- True/False questions
- Short answer questions
Rules:
- Generate 3-4 questions per topic
- Cover all topics
- MCQs must have exactly 4 options
You MUST respond with valid JSON only. No explanation, no markdown, no extra text.
Use this exact format:
{
  "questions": [
    {
      "question_id": "Q1",
      "question_type": "MCQ",
      "topic": "topic name",
      "question_text": "question here",
      "options": ["A. option1", "B. option2", "C. option3", "D. option4"],
      "correct_answer": "A. option1"
    },
    {
      "question_id": "Q2",
      "question_type": "TrueFalse",
      "topic": "topic name",
      "question_text": "statement here",
      "options": null,
      "correct_answer": "True"
    },
    {
      "question_id": "Q3",
      "question_type": "ShortQuestion",
      "topic": "topic name",
      "question_text": "question here",
      "options": null,
      "correct_answer": "expected answer"
    }
  ]
}"""),
        HumanMessage(content=f"Generate exam questions for this curriculum:\n\n{json.dumps(curriculum_output, indent=2)}")
    ]
    response = llm.invoke(messages)
    return parse_json_response(response.content)

# ── Agent 3: Difficulty Agent ────────────────────────────────────────────────
def run_difficulty_agent(question_output: dict) -> dict:
    llm = get_llm()
    messages = [
        SystemMessage(content="""You are an Exam Difficulty Calibration Expert.
Review each question and assign a difficulty level: Easy, Medium, or Hard.
Ensure a balanced distribution: roughly 30% Easy, 50% Medium, 20% Hard.
You MUST respond with valid JSON only. No explanation, no markdown, no extra text.
Use this exact format:
{
  "calibrated_questions": [
    {
      "question_id": "Q1",
      "question_text": "question here",
      "question_type": "MCQ",
      "topic": "topic name",
      "options": ["A. option1", "B. option2", "C. option3", "D. option4"],
      "correct_answer": "A. option1",
      "difficulty": "Easy",
      "difficulty_reason": "reason here"
    }
  ],
  "difficulty_distribution": {
    "Easy": 5,
    "Medium": 10,
    "Hard": 5
  }
}"""),
        HumanMessage(content=f"Calibrate difficulty for these questions:\n\n{json.dumps(question_output, indent=2)}")
    ]
    response = llm.invoke(messages)
    return parse_json_response(response.content)

# ── Agent 4: Rubric Agent ────────────────────────────────────────────────────
def run_rubric_agent(difficulty_output: dict) -> dict:
    llm = get_llm()
    messages = [
        SystemMessage(content="""You are an Academic Assessment Rubric Designer.
Create a detailed marking rubric for each question.
Marks allocation:
- Easy MCQ/TrueFalse: 1 mark
- Medium MCQ/TrueFalse: 1 mark
- Hard MCQ/TrueFalse: 2 marks
- Easy ShortQuestion: 2 marks
- Medium ShortQuestion: 3 marks
- Hard ShortQuestion: 5 marks
You MUST respond with valid JSON only. No explanation, no markdown, no extra text.
Use this exact format:
{
  "total_marks": 50,
  "rubric": [
    {
      "question_id": "Q1",
      "question_text": "question here",
      "correct_answer": "answer here",
      "marks": 1,
      "marking_guide": "Award 1 mark if student selects correct option."
    }
  ]
}"""),
        HumanMessage(content=f"Create marking rubric for these questions:\n\n{json.dumps(difficulty_output, indent=2)}")
    ]
    response = llm.invoke(messages)
    return parse_json_response(response.content)

# ── Agent 5: Analytics Agent ─────────────────────────────────────────────────
def run_analytics_agent(curriculum_output: dict, difficulty_output: dict, rubric_output: dict) -> dict:
    llm = get_llm()
    combined = {
        "curriculum": curriculum_output,
        "questions": difficulty_output,
        "rubric": rubric_output
    }
    messages = [
        SystemMessage(content="""You are an Educational Analytics Expert.
Analyze the exam paper and generate a coverage report:
1. How many questions per topic
2. Marks per topic
3. Coverage percentage per topic
4. Any topics that are under-represented (gaps)
5. Overall summary
You MUST respond with valid JSON only. No explanation, no markdown, no extra text.
Use this exact format:
{
  "total_questions": 20,
  "total_marks": 50,
  "topic_coverage": [
    {
      "topic": "topic name",
      "questions_count": 3,
      "marks_allocated": 5,
      "coverage_percentage": 15.0
    }
  ],
  "gaps": ["Topic X has only 1 question", "Topic Y not covered"],
  "summary": "Overall summary of the exam paper"
}"""),
        HumanMessage(content=f"Generate analytics report for this exam:\n\n{json.dumps(combined, indent=2)}")
    ]
    response = llm.invoke(messages)
    return parse_json_response(response.content)

# ── Master Pipeline ──────────────────────────────────────────────────────────
def run_pipeline(notes_text: str) -> dict:
    print("🔄 Agent 1: Curriculum Analysis...")
    curriculum = run_curriculum_agent(notes_text)
    
    print("🔄 Agent 2: Question Generation...")
    questions = run_question_agent(curriculum)
    
    print("🔄 Agent 3: Difficulty Calibration...")
    difficulty = run_difficulty_agent(questions)
    
    print("🔄 Agent 4: Rubric Creation...")
    rubric = run_rubric_agent(difficulty)
    
    print("🔄 Agent 5: Analytics Generation...")
    analytics = run_analytics_agent(curriculum, difficulty, rubric)
    
    print("✅ Pipeline Complete!")
    return {
        "curriculum": curriculum,
        "questions": questions,
        "difficulty": difficulty,
        "rubric": rubric,
        "analytics": analytics
    }

# ── AI Tutor Function ────────────────────────────────────────────────────────
# Yeh function specific topic ko detail mein explain karega
def generate_study_material(topic_name: str, objectives: list) -> str:
    llm = get_llm()
    objectives_str = "\n".join([f"- {obj}" for obj in objectives])
    messages = [
        SystemMessage(content="""You are an expert Educational AI Tutor. 
Your job is to teach the user about a specific topic based on its learning objectives. 
Provide a comprehensive, easy-to-understand explanation, use bullet points, and give real-world examples. 
Keep the tone encouraging and academic."""),
        HumanMessage(content=f"Please teach me about '{topic_name}'.\nHere are the learning objectives I need to cover:\n{objectives_str}")
    ]
    response = llm.invoke(messages)
    return response.content