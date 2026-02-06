import redis
import json
import os
import time
from flask import Flask, request, jsonify

app = Flask(__name__)
r = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

# Record an event to the reasoning ledger
@app.route('/events', methods=['POST'])
def record_event():
    event_data = request.json
    event_data['timestamp'] = time.time()  # Add server timestamp for filtering and ordering
    # Push event to a Redis List (The Ledger)
    r.lpush("reasoning_ledger", json.dumps(event_data))
    
    print(f"Ledger Updated: {event_data.get('decision', {}).get('authorized')}")
    return jsonify({"status": "appended_to_ledger"}), 201

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
        # You could even calculate rolling averages here
        "avg_qty_1h": sum(e['intent']['quantity'] for e in agent_events) / len(agent_events) if agent_events else 0
    }
    
    return jsonify(history)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)