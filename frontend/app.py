import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="Guardian Control Pit", layout="wide")

st.title("🛡️ Guardian: Reasoning Ledger")
st.subheader("Real-time Agentic Access Control Feed")

# Sidebar for auto-refresh settings
refresh_rate = st.sidebar.slider("Refresh rate (seconds)", 1, 10, 2)

# Placeholder for the data
placeholder = st.empty()

def fetch_ledger():
    try:
        # Use localhost:5005 if running locally, othewrwise use the service name in Docker
        resp = requests.get("http://control-pit:5000/ledger")
        return resp.json()
    except:
        return []

while True:
    data = fetch_ledger()
    
    with placeholder.container():
        if not data:
            st.info("No events in ledger yet...")
        else:
            # Create a nice table
            for event in data:
                with st.expander(
                    f"{'✅' if event['decision']['authorized'] else '❌'} "
                    f"Agent: {event['agent_id']} | "
                    f"Action: {event['intent']['item']} x{event['intent']['quantity']}"
                ):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.write("**Intent**")
                        st.json(event['intent'])
                    
                    with col2:
                        st.write("**Context (Reality)**")
                        st.json(event['context_at_execution'])
                        
                    with col3:
                        st.write("**Decision**")
                        if event['decision']['authorized']:
                            st.success("Authorized")
                        else:
                            st.error(f"Rejected: {event['decision']['reason']}")
    
    time.sleep(refresh_rate)
    st.rerun()