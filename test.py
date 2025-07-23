import google.generativeai as genai

# --- Gemini API Setup ---
genai.configure(api_key="AIzaSyBg2j-nmkJ7Fm63UeGRPSKJlYVjUzcdchs")
def convert_to_qa(text: str) -> str:
    """
    Converts raw website text into a list of Q&A pairs using Gemini API.
    
    Parameters:
        text (str): The raw extracted text content from a website.
    
    Returns:
        str: Formatted Q&A pairs or an error message.
    """
    prompt = f"""
You are a domain-agnostic AI assistant specialized in transforming raw text into structured knowledge.

Your task is to read the following input and generate a clean, diverse set of Question-Answer (Q&A) pairs.

Instructions:
- Generate as many meaningful Q&A pairs as possible based on the content.
- Cover all important points, facts, sections, or ideas in the text.
- Rephrase questions naturally, like a real user might ask them.
- Avoid vague or repetitive questions.
- Ensure accurate and complete answers.
- Format the output as a JSON array like this:

[
  {{
    "question": "What is the main goal of the project?",
    "answer": "The main goal is to provide a voice-enabled AI chatbot based on user data."
  }},
  ...
]

Now use the following text to generate the Q&A pairs:
also the number of q/a must be minimum 50 
and it includes all the important points, facts, sections, or ideas in the text includiing the numbers too 

\"\"\"{text}\"\"\"
    """

    try:
        model = genai.GenerativeModel("models/gemini-2.0-flash")  # or "models/gemini-2.0-flash" if faster
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print("Gemini API Error:", e)
        return "❌ Gemini API Error: Please try again later or check your API credentials."


# --- Load Text File ---
def load_text_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        print("Error reading file:", e)
        return ""

# --- Main ---
if __name__ == "__main__":
    file_path = "sample.txt"
    print(f"[*] Loading website text from: {file_path}")
    
    website_text = load_text_file(file_path)

    if not website_text.strip():
        print("[-] No content to process.")
        exit()

    print("[*] Sending text to Gemini for Q&A generation...")
    qa_result = convert_to_qa(website_text)

    print("\n===== GENERATED Q&A =====\n")
    print(qa_result[:3000])  # Print first 3000 chars

    # --- Save to File ---
    output_file = "qa_output.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(qa_result)

    print(f"\n[✓] Q&A saved to {output_file}")
