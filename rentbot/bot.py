import os
import requests
import pandas as pd
import gradio as gr
from datetime import datetime
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langgraph.prebuilt import create_react_agent
from langchain.tools import tool
from langchain_core.messages import HumanMessage, AIMessage

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
RENTCAST_API_KEY = os.getenv("RENTCAST_API_KEY")

# ── Tools ──────────────────────────────────────────────────────────────────────

STATE_ABBREVS = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR", "california": "CA",
    "colorado": "CO", "connecticut": "CT", "delaware": "DE", "florida": "FL", "georgia": "GA",
    "hawaii": "HI", "idaho": "ID", "illinois": "IL", "indiana": "IN", "iowa": "IA",
    "kansas": "KS", "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN", "mississippi": "MS",
    "missouri": "MO", "montana": "MT", "nebraska": "NE", "nevada": "NV", "new hampshire": "NH",
    "new jersey": "NJ", "new mexico": "NM", "new york": "NY", "north carolina": "NC",
    "north dakota": "ND", "ohio": "OH", "oklahoma": "OK", "oregon": "OR", "pennsylvania": "PA",
    "rhode island": "RI", "south carolina": "SC", "south dakota": "SD", "tennessee": "TN",
    "texas": "TX", "utah": "UT", "vermont": "VT", "virginia": "VA", "washington": "WA",
    "west virginia": "WV", "wisconsin": "WI", "wyoming": "WY",
}

@tool
def search_rentals(city: str, state: str, max_rent: int) -> str:
    """Search for rental listings in a given city and state under a max monthly rent price."""
    try:
        state_code = STATE_ABBREVS.get(state.lower(), state.upper())
        df = pd.read_csv("rentals.csv", sep=";", encoding="latin-1", on_bad_lines="skip", low_memory=False)
        df["price"] = pd.to_numeric(df["price"], errors="coerce")
        filtered = df[
            (df["cityname"].str.strip().str.lower() == city.strip().lower()) &
            (df["state"].str.strip().str.upper() == state_code.strip()) &
            (df["price"] <= max_rent)
        ].dropna(subset=["price"])
        if filtered.empty:
            return f"No rentals found under ${max_rent}/mo in {city}, {state}."
        results = []
        for _, row in filtered.head(10).iterrows():
            sqft = f" | {int(row['square_feet'])} sqft" if pd.notna(row.get("square_feet")) else ""
            pets = f" | Pets: {row['pets_allowed']}" if pd.notna(row.get("pets_allowed")) else ""
            results.append(f"• {row['address']} — ${int(row['price'])}/mo | {row['bedrooms']} bed / {row['bathrooms']} bath{sqft}{pets}")
        return f"Rentals in {city}, {state} under ${max_rent}/mo:\n" + "\n".join(results)
    except FileNotFoundError:
        return "Rentals data file not found. Make sure rentals.csv is in the same folder as bot.py."
    except Exception as e:
        return f"Error searching rentals: {e}"


@tool
def get_neighborhood_info(city: str, state: str) -> str:
    """Get location and neighborhood information for a city using OpenStreetMap."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {"city": city, "state": state, "country": "USA", "format": "json", "limit": 1}
    headers = {"User-Agent": "RentBot/1.0"}
    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if not data:
            return f"No location data found for {city}, {state}."
        place = data[0]
        return (
            f"Location info for {city}, {state}:\n"
            f"Full name: {place.get('display_name', 'N/A')}\n"
            f"Type: {place.get('type', 'N/A')}\n"
            f"Coordinates: {place.get('lat', 'N/A')}, {place.get('lon', 'N/A')}"
        )
    except Exception as e:
        return f"Error fetching neighborhood info: {e}"


@tool
def calculate_affordability(monthly_income: float) -> str:
    """Calculate how much rent a person can afford based on their monthly income using the 30% rule."""
    comfortable = monthly_income * 0.25
    recommended = monthly_income * 0.30
    stretched = monthly_income * 0.35
    return (
        f"Affordability breakdown for ${monthly_income:,.0f}/mo income:\n"
        f"• Comfortable  (25%): up to ${comfortable:,.0f}/mo\n"
        f"• Recommended  (30%): up to ${recommended:,.0f}/mo\n"
        f"• Stretched    (35%): up to ${stretched:,.0f}/mo\n\n"
        f"Most financial advisors recommend keeping rent at or below 30% of your gross income."
    )


@tool
def get_renter_tips(topic: str) -> str:
    """Get helpful renter tips and advice. Topics include: lease, deposit, utilities, moving, rights."""
    try:
        with open("renter_tips.md", "r", encoding="utf-8") as f:
            content = f.read()
        sections = content.split("\n## ")
        for section in sections:
            if topic.lower() in section.lower():
                return section[:2000]
        return content[:2000]
    except FileNotFoundError:
        return "Renter tips file not found. Make sure renter_tips.md is in the same folder as bot.py."


# ── LLM + Agent setup ──────────────────────────────────────────────────────────

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=GROQ_API_KEY,
    temperature=0.3,
)

tools = [search_rentals, get_neighborhood_info, calculate_affordability, get_renter_tips]

SYSTEM_PROMPT = (
    "You are RentBot, a friendly AI assistant that helps people find apartments and houses for rent. "
    "You have four tools: search for real listings, get neighborhood info, calculate affordability, and share renter tips. "
    "Always be concise, helpful, and encouraging. "
    "If the user asks to search for rentals but hasn't provided a city or state, ask for those details first. "
    "When displaying listings, format them clearly with bullet points. "
    "If the search tool returns no results, tell the user clearly that no listings were found for that city and suggest they try a nearby major city."
)

agent = create_react_agent(
    model=llm,
    tools=tools,
    prompt=SYSTEM_PROMPT,
)


# ── Conversation logging ───────────────────────────────────────────────────────

def log_conversation(role: str, message: str):
    with open("conversation_log.txt", "a", encoding="utf-8") as f:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {role}: {message}\n")


# ── Gradio chat interface ──────────────────────────────────────────────────────

def chat(user_message: str, history: list) -> str:
    log_conversation("User", user_message)

    # Build full message list from Gradio history + new message
    messages = []
    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))
    messages.append(HumanMessage(content=user_message))

    try:
        result = agent.invoke({"messages": messages}, config={"recursion_limit": 25})
        answer = result["messages"][-1].content
    except Exception as e:
        answer = f"Sorry, I ran into an error: {e}"

    log_conversation("RentBot", answer)
    return answer


demo = gr.ChatInterface(
    fn=chat,
    title="RentBot — AI Apartment Finder",
    description="Ask me to find rentals, check neighborhoods, calculate what you can afford, or get renter advice!",
    examples=[
        "Find apartments in Dallas, Texas under $1500/month",
        "Find rentals in Denver, Colorado under $2000/month",
        "I make $4,000 a month. What can I afford?",
        "What should I know before signing a lease?",
        "Tell me about the neighborhood in Las Vegas, Nevada",
    ],
)

if __name__ == "__main__":
    demo.launch()
