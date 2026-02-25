import os
from jobs.run_daily_sync import build_ai_payload
from ai_agents.analyst_agent import get_executive_summary

def main():
    with open("test_output2.txt", "w", encoding="utf-8") as f:
        f.write("Building Payload...\n")
        payload = build_ai_payload()
        import json
        f.write(json.dumps(payload, indent=2))
        
        f.write("\nGenerating AI Report...\n")
        # Generate the report
        report_text = get_executive_summary(payload)
        f.write("\n---------------- REPORT ----------------\n")
        if report_text:
            f.write(report_text)
        else:
            f.write("None\n")
        f.write("\n----------------------------------------\n")

if __name__ == "__main__":
    main()
