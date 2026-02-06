import requests
import json
from openai import OpenAI

# Configuration
client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")
GATEWAY_URL = "http://localhost:3000/purchase"
MODEL_NAME = "llama3.1:latest"

def call_gateway(item, quantity):
    """The tool executed by the script on behalf of the Agent"""
    print(f"\n[NETWORK] Executing: POST /purchase {{'item': '{item}', 'qty': {quantity}}}")
    try:
        resp = requests.post(GATEWAY_URL, json={
            "item": item,
            "quantity": quantity
        }, headers={"X-Agent-ID": "Autonomous-Llama-Bot"})
        return resp.json()
    except Exception as e:
        return {"error": str(e)}

def run_autonomous_demo():
    print("--- 🤖 STARTING TRUE AUTONOMOUS AGENT ---")
    
    # The 'Brain' instructions
    system_prompt = """
    You are an autonomous procurement agent. Your GOAL is to buy 10 laptops.
    
    You must output your next action in STRICT JSON format so a system can parse it.
    Example output format, require item and quantity fields:
    {
      "reasoning": "I need to buy laptops, so I will start by trying to buy 10.",
      "item": "laptop",
      "quantity": 10
    }

    If the system rejects you, read the error and adjust your next JSON output to try again.
    Continue until you have successfully purchased at least some laptops.
    """

    messages = [{"role": "system", "content": system_prompt}]
    success = False
    attempts = 0

    while attempts < 10:
        attempts += 1
        print(f"\n--- ATTEMPT {attempts} ---")

        # 1. Ask the LLM what it wants to do
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            response_format={"type": "json_object"} # Enforce JSON output
        )
        
        # 2. Parse the LLM's intent
        try:
            agent_intent = json.loads(response.choices[0].message.content)
            print(response)
            print(f"[AGENT REASONING]: {agent_intent}")
        except Exception as e:
            print("[ERROR] Failed to parse Agent JSON. Retrying...")
            continue

        # 3. Execute the action the LLM chose
        result = call_gateway(agent_intent['item'], agent_intent['quantity'])
        
        # 4. Show the result
        if result.get('status') == 'SUCCESS' or result.get('status') == 'success':
            print(f"[GATEWAY VERDICT]: ✅ SUCCESS: {result.get('message')}")
            success = True
        else:
            print(f"[GATEWAY VERDICT]: ❌ REJECTED: {result.get('reason')}")
            
            # 5. Feed the REJECTION back into the LLM's memory
            messages.append({"role": "assistant", "content": json.dumps(agent_intent)})
            messages.append({
                "role": "user", 
                "content": f"System Rejected your request. Reason: {result.get('reason')}. What is your next move?"
            })

    if success:
        print("\n--- GOAL ACHIEVED: Agent navigated the contract successfully. ---")
    else:
        print("\n--- GOAL FAILED: Agent could not find a reasonable path. ---")

if __name__ == "__main__":
    run_autonomous_demo()