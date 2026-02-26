import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

def _build_system_prompt(bhk, locality, city, area, furnishing, predicted_rent, persona):
    persona_context = ""
    if persona == "owner":
        persona_context = """
## USER PERSONA: PROPERTY OWNER
The user is a property owner seeking to maximise rental yield.
- Provide ROI-focused insights, suggest optimal listing price, maintenance ROI.
- Calculate gross yield: (annual rent / capital value) × 100.
- Suggest which upgrades (modular kitchen, AC, etc.) increase rent premium.
- Advise on tenant screening and lease duration for maximum stability.
"""
    else:
        persona_context = """
## USER PERSONA: TENANT / RENTER
The user is seeking to rent a property and avoid overpaying.
- Identify if the asking price is above/below the ML benchmark.
- Provide concrete negotiation scripts and non-monetary asks (parking, lock-in flexibility).
- Flag red flags in listings (price spikes, hidden costs like maintenance).
- Suggest comparable localities that offer better value.
"""

    return f"""## ROLE: THE CATALYST STRATEGIST (V3.0)
You are a Tier-1 Real Estate Investment Strategist specializing in Indian Urban Markets (Mumbai, Pune, Delhi NCR).
You operate with the precision of a data scientist and the instincts of a 20-year veteran broker.
Tone: Sophisticated, Direct, Data-driven.

## PROPERTY PROFILE (IMMUTABLE)
- **Configuration:** {bhk} BHK | {area} sqft | {furnishing}
- **Location:** {locality}, {city}
- **ML Fair Rent:** ₹{int(predicted_rent):,}/month (±5% confidence band)
  This is your anchor. Always defend it with micro-market data.

{persona_context}

## RESPONSE STYLE
- Use ₹ for all currency. Bold key numbers and locations.
- No filler phrases. Be direct and tactical.
- End every response with a **💡 Strategist's Pro-Tip**.
- If asked for a full report/analysis, structure it:
  1. Market Dynamics
  2. Competitor Micro-Markets (name 2 nearby localities)
  3. Yield/ROI or Negotiation Levers (based on persona)
  4. 30-Day Outlook
"""

def stream_real_estate_advice(bhk, locality, city, area, furnishing, predicted_rent,
                                user_question, chat_history="", persona="tenant"):

    system_prompt = _build_system_prompt(bhk, locality, city, area, furnishing, predicted_rent, persona)

    messages = [{"role": "system", "content": system_prompt}]

    # Inject chat history as conversation turns
    if chat_history:
        for line in chat_history.strip().split("\n"):
            if line.startswith("user:"):
                messages.append({"role": "user", "content": line[5:].strip()})
            elif line.startswith("ai:"):
                messages.append({"role": "assistant", "content": line[3:].strip()})

    messages.append({"role": "user", "content": user_question})

    stream = client.chat.completions.create(
        model="gemini-2.5-flash",
        messages=messages,
        temperature=0.7,
        stream=True,
        # web_search_options=True
    )

    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta and delta.content:
            yield delta.content


# Non-streaming fallback (kept for compare endpoint)
def get_real_estate_advice(bhk, locality, city, area, furnishing,
                            predicted_rent, user_question, chat_history="", persona="tenant"):
    system_prompt = _build_system_prompt(bhk, locality, city, area, furnishing, predicted_rent, persona)
    response = client.chat.completions.create(
        model="gemini-2.5-flash",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_question}
        ],
        temperature=0.7,
    )
    return response.choices[0].message.content
