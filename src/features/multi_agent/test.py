import asyncio
import json
import logging

from features.multi_agent.agent_factory import run_research_pipeline

def main():
    # Set logging to INFO or DEBUG to see more details
    logging.basicConfig(level=logging.INFO)
    
    # Example company name
    company_name = "Tesla"

    # Run the pipeline (asynchronously)
    state = asyncio.run(run_research_pipeline(company_name))

    # Print the final structured output from the pipeline
    print("\n=== Final Structured Output ===")
    if state.final_output:
        # Pretty-print JSON
        print(json.dumps(state.final_output, indent=2))
    else:
        print("No final output was produced.")

if __name__ == "__main__":
    main()