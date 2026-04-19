from flask import Flask, render_template, request
import PyPDF2
import os
from google import genai

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


# Gemini API Configuration
client = genai.Client(api_key="AIzaSyC-EjGetRSnJfsvgNGTeNpfJJjqhqNuGL4")


# Role-based skill checking
job_roles = {
    "Data Analyst": [
        "Python",
        "SQL",
        "Pandas",
        "Excel",
        "Power BI",
        "Tableau"
    ],

    "Python Developer": [
        "Python",
        "Flask",
        "SQL",
        "Git",
        "APIs",
        "OOP"
    ],

    "Software Developer": [
        "Python",
        "Java",
        "DBMS",
        "SQL",
        "OOP",
        "GitHub"
    ]
}


def extract_text_from_pdf(pdf_path):
    text = ""

    with open(pdf_path, "rb") as file:
        reader = PyPDF2.PdfReader(file)

        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted

    return text


def get_ai_suggestion(text, selected_role):
    prompt = f"""
    Analyze this resume for the role of {selected_role}.

    Resume Content:
    {text}

    Give professional ATS improvement suggestions,
    missing important skills,
    and ways to improve job opportunities.

    Keep the response short, clear, and recruiter-friendly.
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )

        return response.text

    except Exception:
        return "AI suggestions are temporarily unavailable due to API quota limits. Please try again later."


def analyze_resume(text, selected_role):
    required_skills = job_roles[selected_role]

    found_skills = []
    missing_skills = []

    for skill in required_skills:
        if skill.lower() in text.lower():
            found_skills.append(skill)
        else:
            missing_skills.append(skill)

    score = int((len(found_skills) / len(required_skills)) * 100)

    if score >= 80:
        suggestion = f"Strong resume for {selected_role} role."

    elif score >= 50:
        suggestion = (
            f"Good resume, but adding "
            f"{', '.join(missing_skills)} "
            f"will improve your chances for {selected_role} roles."
        )

    else:
        suggestion = (
            f"Resume needs major improvement. "
            f"Add skills like {', '.join(missing_skills)} "
            f"for better opportunities in {selected_role} roles."
        )

    return score, found_skills, missing_skills, suggestion


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        pdf = request.files["resume"]
        selected_role = request.form["job_role"]

        if pdf:
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], pdf.filename)
            pdf.save(file_path)

            extracted_text = extract_text_from_pdf(file_path)

            # Rule-based analysis
            score, found_skills, missing_skills, suggestion = analyze_resume(
                extracted_text,
                selected_role
            )

            # Gemini AI suggestion
            ai_suggestion = get_ai_suggestion(
                extracted_text,
                selected_role
            )

            return render_template(
                "result.html",
                score=score,
                found_skills=found_skills,
                missing_skills=missing_skills,
                suggestion=suggestion,
                ai_suggestion=ai_suggestion,
                selected_role=selected_role
            )

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)