import socket
import time

def wait_for_kafka(host="kafka", port=9092, timeout=60):
    start = time.time()
    while True:
        try:
            with socket.create_connection((host, port), timeout=2):
                print("[MMS] ✅ Kafka is available.")
                return
        except OSError:
            if time.time() - start > timeout:
                raise TimeoutError(f"[MMS] ❌ Timeout: Kafka not available after {timeout} seconds.")
            print("[MMS] ⏳ Waiting for Kafka...")
            time.sleep(2)
