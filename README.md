# Guardian

Guardian is an intent-based access control framework POC that runs in five containers

1. Agentic Gateway: Lightweight Python script that intercepts requests
2. n8n: A "contract engine" where hydration and logic executes
3. Service layer: A simple mock service API that needs protecting
4. Control-pit: redis ledger that documents all interactions
5. Frontend: To display redis stream of events

## The Flow
1. Agent sends a request to the Gateway.
2. Gateway reads contract.yaml (A solidity inspired smart contract)
3. Gateway sends the Request + Contract to an n8n workflow via webhook
4. n8n does the heavy lifting
    - Fetches data from the DB/API if needed (Context hydration)
    - Runs a Code Node (Deterministic Contract Logic)
    - Returns Authorized: True/False + Reason
5. Gateway publishes interaction and its result.
6. Gateway either forwards the request to the service or returns a 403.


## Prerequisites
- docker
- docker-compose
- ollama

## Try it out
To Run the system: 
```
docker-compose up --build
ollama run llama3.1

python3 untrusted_agent/real_agent.py

```

To stop the system: `docker-compose down`