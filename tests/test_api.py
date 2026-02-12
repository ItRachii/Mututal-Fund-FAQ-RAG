import httpx
import time
import sys

def test_api():
    url = "http://localhost:8000/chat"
    payload = {"query": "What is the exit load for HDFC Top 100?"}
    
    print(f"Testing API at {url}...")
    # Retry loop to wait for server to start
    for i in range(5):
        try:
            response = httpx.post(url, json=payload, timeout=30)
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.json()}")
            if response.status_code == 200:
                print("API Verification Successful!")
                return
            else:
                print("API Verification Failed with non-200 status.")
                sys.exit(1)
        except httpx.ConnectError:
            print(f"Connection failed (Attempt {i+1}/5). Retrying in 2s...")
            time.sleep(2)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    print("Failed to connect to API after retries.")
    sys.exit(1)

if __name__ == "__main__":
    test_api()
