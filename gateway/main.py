import os, yaml, requests
from flask import Flask, request, jsonify

app = Flask(__name__)

# Handle purchase requests from the Agent
@app.route('/purchase', methods=['POST'])
def handle_request():
    intent = request.json
    agent_id = request.headers.get("X-Agent-ID", "autonomous-bot-01")

    # 1. CONTRACT RESOLUTION
    with open("/app/contracts/store_policy.yaml", "r") as f:
        contract = yaml.safe_load(f)

    # 2. CONTEXT ASSEMBLY (Fetch current state from service to understand reality)
    api_resp = requests.get(f"{os.getenv('BACKEND_URL')}/items/{intent['item']}")
    item_context = api_resp.json()

    # 3. EVALUATION (The Pure Function)
    bundle = {
        "intent": intent,
        "contract": contract,
        "context": item_context, # Reality
        "agent_id": agent_id
    }
    
    engine_resp = requests.post(os.getenv("N8N_WEBHOOK_URL"), json=bundle)
    decision = engine_resp.json()

    # 4. EVENT EMISSION (Record the "Reasoning" to the Control Pit)
    # We record the Triad: Intent + Context + Decision
    requests.post("http://control-pit:5000/events", json={
        "agent_id": agent_id,
        "intent": intent,
        "context_at_execution": item_context,
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