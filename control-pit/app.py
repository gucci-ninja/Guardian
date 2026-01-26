import redis
import json
import os
from flask import Flask, request, jsonify

app = Flask(__name__)
r = redis.Redis(host='redis', port=6379, db=0, decode_responses=True)

# Record an event to the reasoning ledger
@app.route('/events', methods=['POST'])
def record_event():
    event_data = request.json
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)