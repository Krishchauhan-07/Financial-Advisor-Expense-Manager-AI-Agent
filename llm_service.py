from openai import OpenAI

def generate_financial_advice(prompt: str, api_key: str) -> str:
    """
    Sends the user's prompt (with optional document context) to the LLM
    to act as a Financial Advisor/Mentor.
    """
    client = OpenAI(api_key=api_key)

    system_prompt = """
    You are Nexus, a highly knowledgeable, professional, and insightful AI Financial Advisor.
    You communicate like a financial guru and mentor. You simplify complex financial concepts,
    provide actionable advice based on provided data, and maintain a sophisticated yet accessible tone.
    Always prioritize risk management and remind users that you are an AI and they should verify critical decisions.
    Format your response nicely with markdown.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )
        return response.choices[0].message.content
    except Exception as e:
        raise Exception(f"LLM Error: {str(e)}")
