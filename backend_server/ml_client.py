import requests

#local
# ML_SERVER_URL = "http://localhost:8001/predict"

#server
ML_SERVER_URL = "http://34.174.35.119:8001/predict"



def request_inference(text: str) -> float:
    try:
        res = requests.post(
            ML_SERVER_URL,
            json={"text": text},
            timeout=5
        )
        res.raise_for_status()
        data = res.json()
        return data["prob_ad"]
    except Exception as e:
        print(f"[ML SERVER ERROR] {e}")
        return 0.0
