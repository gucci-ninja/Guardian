import redis
import json
import os
import time
import logging
from flask import Flask, request, jsonify
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)
r = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

# Prometheus Metrics
POLICY_VIOLATIONS = Counter(
    'guardian_policy_violations_total',
    'Total policy violations',
    ['contract_id', 'policy_id', 'agent_id']
)
DECISION_TIME = Histogram(
    'guardian_decision_latency_seconds',
    'Time taken to reach a decision',
    ['contract_id']
)

# Record an event to the reasoning ledger
@app.route('/events', methods=['POST'])
def record_event():
    event_data = request.get_json(force=True)
    event_data['timestamp'] = time.time()
    decision = event_data.get('decision', {})

    # 1. EMIT METRICS
    if not decision.get('authorized'):
        violations = decision.get('violations') or [{'id': 'policy_violation', 'message': decision.get('reason', 'unknown')}]
        for violation in violations:
            POLICY_VIOLATIONS.labels(
                contract_id=event_data.get('contract_id', 'unknown'),
                policy_id=violation['id'],
                agent_id=event_data.get('agent_id', 'unknown')
            ).inc()

    if event_data.get('decision_latency_s') is not None:
        DECISION_TIME.labels(
            contract_id=event_data.get('contract_id', 'unknown')
        ).observe(event_data['decision_latency_s'])

    # 2. EMIT STRUCTURED LOG — Decision Manifest (for Loki/RAG)
    logging.info(json.dumps({
        "msg": "Decision Evaluated",
        "agent_id": event_data.get('agent_id'),
        "contract_id": event_data.get('contract_id'),
        "intent": event_data.get('intent'),
        "resolved_constraints": decision.get('resolved_constraints'),
        "authorized": decision.get('authorized'),
        "violations": decision.get('violations'),
        "context_snapshot": event_data.get('context_at_execution')
    }))

    r.lpush("reasoning_ledger", json.dumps(event_data))

    print(f"Ledger Updated: {event_data.get('decision', {}).get('authorized')}")
    return jsonify({"status": "appended_to_ledger"}), 201

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

# Retrieve the most recent events from the reasoning ledger
@app.route('/ledger', methods=['GET'])
def get_ledger():
    # Retrieve last 10 events
    events = r.lrange("reasoning_ledger", 0, 9)
    return jsonify([json.loads(e) for e in events])

# Retrieve mock history event data for a given agent_id
@app.route('/history/<agent_id>', methods=['GET'])
def get_history(agent_id):
    # Fetch all events from the ledger
    all_events = r.lrange("reasoning_ledger", 0, -1)
    
    now = time.time()
    one_hour_ago = now - 3600
    
    # Filter events for THIS agent within the last hour
    agent_events = []
    for e in all_events:
        event = json.loads(e)
        # Check if event belongs to agent and happened in the last hour
        if event.get('agent_id') == agent_id and event.get('timestamp', 0) > one_hour_ago:
            agent_events.append(event)

    # Calculate facts for the Contract
    history = {
        "request_count_1h": len(agent_events),
        "session_start": agent_events[-1]['timestamp'] if agent_events else now,
        "last_action": agent_events[0]['intent']['item'] if agent_events else None,
        "avg_qty_1h": sum(e['intent']['quantity'] for e in agent_events) / len(agent_events) if agent_events else 0
    }
    
    return jsonify(history)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)