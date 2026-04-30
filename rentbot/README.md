# RentBot — AI Apartment Finder

## Overview

RentBot is a conversational AI assistant that helps renters search for apartments, understand what they can afford, research neighborhoods, and navigate the rental process with confidence. It's built with LangChain, a Groq-hosted LLM, and a Gradio chat interface — deployable as a live web app in minutes.

## The Problem

Finding an apartment is stressful enough without having to juggle five browser tabs, a spreadsheet of listings, a Reddit thread about neighborhoods, and a calculator open on the side. Most rental search tools are transactional — they show you a list and leave the rest to you. First-time renters especially have no easy way to ask "can I actually afford this?" or "what should I watch out for in a lease?" RentBot combines search, financial guidance, and renter education into a single conversation so users can make better decisions faster.

## How It Works

RentBot uses a LangChain ReAct agent (via `langgraph`) backed by a Groq-hosted Llama 3.3 70B model. Based on what the user asks, the agent routes to one of four tools:

```
User message
     │
     ▼
 LangChain ReAct Agent (Llama 3.3 70B via Groq)
     │
     ├── search_rentals         → Filters rentals.csv by city, state, and max price
     │                            Returns up to 10 matching listings
     │
     ├── get_neighborhood_info  → Calls OpenStreetMap Nominatim API
     │                            Returns location type, full name, and coordinates
     │
     ├── calculate_affordability → Applies 25/30/35% income rules
     │                             Returns a tiered rent budget breakdown
     │
     └── get_renter_tips        → Reads renter_tips.md (RAG on local document)
                                  Returns advice on lease, deposit, utilities, moving, or rights
```

The agent decides which tool(s) to use based on the user's message — no hardcoded routing rules.

## Key Findings / What I Learned

Working with a real 99k-row dataset immediately exposed practical problems that a toy demo never would — encoding issues, inconsistent delimiters, and mixed column types all had to be handled before a single query could run. That debugging process was more educational than any clean tutorial dataset.

The trickiest part was getting the agent to behave predictably when a tool returned no results. Without explicit instructions, the LLM would generate a polite but misleading response implying it had found something. A single line in the system prompt — telling the bot to clearly state when nothing was found and suggest alternatives — fixed this entirely. Prompt engineering is underrated.

## Sample Conversations

> Replace these placeholders with real exchanges from your `conversation_log.txt` after running the bot.

**Tool triggered: `search_rentals`**
```
User:    Find apartments in Dallas, Texas under $1,200 a month
RentBot: Here are rentals in Dallas, TX under $1,200/mo:
         • 4821 Cedar Springs Rd — $1,100/mo | 1 bed / 1 bath | 620 sqft | Pets: None
         • ...
```

**Tool triggered: `calculate_affordability`**
```
User:    I make $3,500 a month. What can I afford?
RentBot: Affordability breakdown for $3,500/mo income:
         • Comfortable (25%): up to $875/mo
         • Recommended (30%): up to $1,050/mo
         • Stretched   (35%): up to $1,225/mo
```

**Tool triggered: `get_neighborhood_info`**
```
User:    Tell me about the Denver, Colorado area
RentBot: Location info for Denver, Colorado:
         Full name: Denver, Denver County, Colorado, United States
         Type: city | Coordinates: 39.7392, -104.9903
```

**Tool triggered: `get_renter_tips`**
```
User:    What should I know about security deposits?
RentBot: Before moving in, take dated photos and video of every room and email
         them to your landlord to create a paper trail. Most states require
         landlords to return deposits within 14–30 days of move-out ...
```

## How to Run

**Requirements:** Python 3.9+

1. Clone the repo and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file in the project root:
   ```
   GROQ_API_KEY=your_key_here
   ```
   Get a free key at [console.groq.com](https://console.groq.com).

3. Launch the app:
   ```bash
   python bot.py
   ```
   Gradio will print a local URL (e.g. `http://127.0.0.1:7860`). Open it in your browser.

**For Hugging Face Spaces deployment:** Set `GROQ_API_KEY` as a Space secret under *Settings → Variables and secrets*. The `rentals.csv` file is tracked via Git LFS — clone with `git lfs pull` to get it locally.

## Who Would Care

Anyone apartment hunting for the first time — college students, recent graduates, or people relocating to a new city — would find RentBot useful. It replaces the need to separately search listings, Google affordability rules, and read Reddit threads about neighborhoods. Property managers or tenant advocacy organizations could also adapt it as a renter education tool, embedding it on their site to answer common questions before a leasing agent gets involved.
