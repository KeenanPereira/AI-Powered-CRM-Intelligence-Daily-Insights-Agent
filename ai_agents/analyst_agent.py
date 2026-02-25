import json
import logging
from typing import Dict, Any, Optional
from langchain_ollama import ChatOllama

# Set up logging for production architecture
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def _construct_data_scientist_prompt(payload: Dict[str, Any]) -> str:
    """
    Constructs an advanced, zero-shot prompt with strict analytical rubrics
    to force the LLM into a Data Scientist persona and prevent generic hallucinated advice.
    """
    json_string = json.dumps(payload, indent=2)
    
    prompt = f"""
You are an elite Revenue Operations Analyst reporting to the CEO. You translate raw CRM data into sharp, highly actionable business intelligence. 

YOUR TONE:
Direct, insightful, and slightly ruthless about inefficiencies. No fluff.

YOUR MANDATE:
Analyze the data snapshot below. Pay CRITICAL attention to the `anomalies_detected_by_math` section—these are pre-calculated bottlenecks that you MUST report on.

STRICT RULES:
1. ZERO HALLUCINATION: Only use provided names, sources, numbers, and currency (₹).
2. NO GENERIC FLUFF: Do not invent generic problems. If `anomalies_detected_by_math` highlights an overloaded rep or a toxic channel, you MUST make that the centerpiece of your recommended actions.
3. FOCUS ON DAILY CHANGES: For the WhatsApp report, only talk about what happened *yesterday* and what needs to be fixed *today*.

OUTPUT FORMAT:
Always output exactly two sections clearly delimited by <DASHBOARD_REPORT> and <WHATSAPP_REPORT> tags. Do not output any text outside of these tags.

<DASHBOARD_REPORT>
### 1. The Daily Pulse
- Briefly summarize yesterday's lead volume, pipeline value, and pacing. Provide deep insights.
### 2. Deep Dive Diagnostics
- Detailed breakdown in bullet points. Explicitly call out any 'OVERLOADED' reps or 'TOXIC' channels provided in the anomalies payload.
### 3. Immediate Execution
- Give 1-2 sharp, realistic actions based entirely on fixing the identified bottlenecks.
</DASHBOARD_REPORT>

<WHATSAPP_REPORT>
Provide a hard-hitting executive summary carefully formatted for WhatsApp. Do NOT use markdown headers like `###` as they do not render well on WhatsApp. Instead, use WhatsApp bolding (`*Text*`) for section headers.
Structure the summary EXACTLY as follows:

*1. The Daily Pulse*
- Yesterday's lead volume was [X], a [+/-X%] change from the 7-day average.
- New pipeline generated today is ₹[X], bringing total open pipeline to ₹[X].
- Total Closed Won stands at [X] deals (₹[X]), and Closed Lost stands at [X] deals (₹[X]).

*2. Deep Dive Diagnostics*
- [Bullet summarizing critical rep overload with exact active leads and pipeline value, e.g. *OVERLOADED* rep:]
- [Bullet summarizing toxic channel with exact junk percentage]

*3. Immediate Execution*
- [Action 1 based on the data]
- [Action 2 based on the data]
- [Action 3 based on the data]

CRITICAL RULES: Use `*` for bold text in WhatsApp. NO emojis. NO informal language. Write strictly for a CEO. Keep total output under 1400 characters. Incorporate exact numbers from the payload.
</WHATSAPP_REPORT>

DATA:
{json_string}
"""
    return prompt

def get_executive_summary(payload: Dict[str, Any], model_name: str = "llama3.2", temperature: float = 0.3) -> Optional[str]:
    """
    Invokes the local LLM using a strict prompt engineering framework.
    Returns the string text of the report or None if execution fails.
    """
    if not payload:
        logging.error("Empty payload provided to AI Agent.")
        return None
        
    prompt = _construct_data_scientist_prompt(payload)
    
    # Temperature 0.0 enforces consistency and mathematical grounding over creativity
    try:
        logging.info(f"Invoking {model_name} (Temp: {temperature})...")
        llm = ChatOllama(model=model_name, temperature=temperature)
        response = llm.invoke(prompt)
        return response.content
        
    except Exception as e:
        logging.critical(f"LLM Invocation Failed: {e}")
        return None

