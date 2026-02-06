import os, yaml, requests, json, time
from flask import Flask, request, jsonify

app = Flask(__name__)

# Config
N8N_URL = os.getenv("N8N_WEBHOOK_URL")
BACKEND_URL = os.getenv("BACKEND_URL")
CONTROL_PIT_URL = os.getenv("CONTROL_PIT_URL")

# Handle purchase requests from the Agent
@app.route('/purchase', methods=['POST'])
def handle_request():
    intent = request.json
    agent_id = request.headers.get("X-Agent-ID", "autonomous-bot-01")

    # 1. CONTRACT RESOLUTION
    with open("/app/contracts/store_policy_v2.yaml", "r") as f:
        contract = yaml.safe_load(f)

    # 2. CONTEXT ASSEMBLY (Fetch current state from service to understand reality and history)
    reality = requests.get(f"{BACKEND_URL}/items/{intent['item']}").json()
    history = requests.get(f"{CONTROL_PIT_URL}/history/{agent_id}").json()

    # 3. EVALUATION (The Pure Function)
    bundle = {
        "intent": intent,
        "contract": {
            "metadata": contract.get('metadata'),
            "constraints": contract.get('constraints'),
            "policies": contract.get('policies')
        },
        "context": {
            "reality": reality,
            "history": history,
            "now": time.time()
        },
        "agent_id": agent_id
    }
    
    engine_resp = requests.post(N8N_URL, json=bundle)
    decision = engine_resp.json()

    # 4. EVENT EMISSION (Record the "Reasoning" to the Control Pit)
    # We record the Triad: Intent + Context + Decision
    requests.post(f"{CONTROL_PIT_URL}/events", json={
        "agent_id": agent_id,
        "intent": intent,
        "context_at_execution": bundle["context"],
        "decision": decision
    })

    # 5. ENFORCEMENT
    if decision.get('authorized'):
        # Forward to target service...
        return jsonify({"status": "SUCCESS", "message": "Action permitted"}), 200
    else:
        return jsonify(decision), 403

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)