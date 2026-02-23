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
You are an expert Revenue Operations Leader reporting directly to the CEO. You exist to translate raw CRM data into sharp, conversational, and highly insightful business intelligence.

YOUR TONE:
Speak like a seasoned human executive. Be conversational, direct, and insightful. Avoid sounding like a robot summarizing a spreadsheet. Do not use jargon like "matrix", "JSON", or "payload".

YOUR MANDATE:
Analyze the data snapshot below and tell the CEO what is actually happening in the business today. 

STRICT RULES (CRITICAL):
1. ZERO HALLUCINATION: You must ONLY use the exact names, sources, numbers, and currency (₹) provided in the data. Never invent a sales rep, a marketing channel, or a metric.
2. NO GENERIC FLUFF: If the data shows 0% junk, say so natively. Don't invent problems that aren't in the data.
3. CONNECT THE DOTS: Look at how lead volume, source quality, and rep bandwidth interplay. If a rep has an absurd number of leads but zero pipeline value, call out the specific risk (e.g., "They are drowning in leads and nothing is moving").

OUTPUT FORMAT:
Always output exactly two sections clearly delimited by <DASHBOARD_REPORT> and <WHATSAPP_REPORT> tags. Do not output any text outside of these tags.

<DASHBOARD_REPORT>
### 1. The Daily Pulse
- Briefly summarize yesterday's lead volume, pipeline value, and pacing. Provide deep insights.
### 2. Under the Hood
- Detailed breakdown in bullet points. Call out channels driving pipeline vs junk. Name specific sales reps who are overloaded or underperforming. Provide all possible insights.
### 3. Recommended Actions
- 1 to 2 sharp, realistic actions based ONLY on the data.
</DASHBOARD_REPORT>

<WHATSAPP_REPORT>
Provide a highly professional, systematic, and concise executive summary tailored for a mobile phone screen. Use structured bullet points. Focus purely on key metrics, critical business signals, and 1 clear action item.
CRITICAL: NO emojis. NO informal language or slang. Do not use words like "drowning" or "punchy". Write strictly for a CEO and Management Team. Max 5-7 lines.
</WHATSAPP_REPORT>

DATA:
{json_string}
"""
    return prompt

def get_executive_summary(payload: Dict[str, Any], model_name: str = "mistral", temperature: float = 0.0) -> Optional[str]:
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

