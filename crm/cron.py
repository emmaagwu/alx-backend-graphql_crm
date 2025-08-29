import datetime
import requests

def log_crm_heartbeat():
    now = datetime.datetime.now().strftime("%d/%m/%Y-%H:%M:%S")

    message = f"{now} CRM is alive"

    # Log to file (append mode)
    with open("/tmp/crm_heartbeat_log.txt", "a") as f:
        f.write(message + "\n")

    # Optional: check GraphQL hello query
    try:
        response = requests.post(
            "http://localhost:8000/graphql",
            json={"query": "{ hello }"},
            timeout=5
        )
        if response.status_code == 200:
            data = response.json()
            hello_value = data.get("data", {}).get("hello", "No response")
            with open("/tmp/crm_heartbeat_log.txt", "a") as f:
                f.write(f"{now} GraphQL hello -> {hello_value}\n")
    except Exception as e:
        with open("/tmp/crm_heartbeat_log.txt", "a") as f:
            f.write(f"{now} GraphQL heartbeat failed: {e}\n")
