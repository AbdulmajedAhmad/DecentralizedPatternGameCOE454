import firebase_admin
from firebase_admin import credentials, db
import paho.mqtt.client as mqtt
import json
import time
import os

# --- CLOUD CONFIG ---
# "Environment Variables" for Render.com
UNIQUE_ID = os.environ.get('UNIQUE_ID')
DB_URL = os.environ.get('FIREBASE_DB_URL')

# Securely load the Firebase JSON from the environment variable
fb_json_str = os.environ.get('FIREBASE_JSON')

if fb_json_str:
    # Use Environment Variable for Cloud Deployment
    fb_config = json.loads(fb_json_str)
    cred = credentials.Certificate(fb_config)
else:
    # Fallback for local testing on your Arch machine
    cred = credentials.Certificate("service_key.json")

firebase_admin.initialize_app(cred, {'databaseURL': DB_URL})
db_ref = db.reference('game_state')

# --- MQTT CONFIG ---
TOPIC_BASE = f"kfupm/{UNIQUE_ID}/game"
TOPIC_INPUT = f"{TOPIC_BASE}/input"

state = {
    "sequence": [],
    "current_player": "p1", # Standardized to p1/p2
    "index": 0,
    "score": 0
}

# A function for project local deployment:
# def save_and_publish(client):
#     with open("game_state.json", "w") as f:
#         json.dump(state, f)
#     client.publish(f"{TOPIC_BASE}/dashboard", json.dumps(state), retain=True)

def save_to_cloud():
    db_ref.set(state)
    print("☁️ Cloud JSON Updated")

def on_message(client, userdata, msg):
    global state
    payload = msg.payload.decode()
    
    try:
        # Expecting "p1:B1" or "p2:B2"
        sender, button = payload.split(":")
        sender = sender.lower() # Ensure it matches p1/p2
        
        if sender != state["current_player"]:
            return

        # 1. Validation Phase
        if state["index"] < len(state["sequence"]):
            if button == state["sequence"][state["index"]]:
                state["index"] += 1
            else:
                # FAIL
                client.publish(f"{TOPIC_BASE}/p1", "WRONG")
                client.publish(f"{TOPIC_BASE}/p2", "WRONG")
                state = {"sequence": [], "current_player": "p1", "index": 0, "score": 0}
                #save_and_publish(client)
                save_to_cloud()
                return

        # 2. Add-on Phase
        elif state["index"] == len(state["sequence"]):
            state["sequence"].append(button)
            state["score"] += 1
            
            # Inform current player they were successful
            client.publish(f"{TOPIC_BASE}/{sender}", "CORRECT")
            
            # Switch turn
            state["current_player"] = "p2" if sender == "p1" else "p1"
            state["index"] = 0 
            #save_and_publish(client)
            save_to_cloud()

            # 3. Trigger Light Spikes for the NEXT player
            time.sleep(0.5) 
            target_topic = f"{TOPIC_BASE}/{state['current_player']}/sequence"
            client.publish(target_topic, json.dumps(state["sequence"]))

    except Exception as e:
        print(f"Error: {e}")
        
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"✅ Connected to Broker! Subscribing to: {TOPIC_INPUT}")
        client.subscribe(TOPIC_INPUT)
    else:
        print(f"❌ Failed to connect, return code {rc}")

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect("broker.hivemq.com", 1883, 180)
save_to_cloud() # Initial state sync
client.loop_forever()
