from fastapi import FastAPI, Query
import httpx
from utils import apply_differential_privacy

app = FastAPI()
buyers = {
    "buyer_1": {"tokens": 10},
    "buyer_2": {"tokens": 5}
}

hospitals = {
    "Hospital_A": {"tokens": 0},
    "Hospital_B": {"tokens": 0}
}

@app.get("/analytics/average-age")
async def get_avg_age(
    condition: str = Query(..., example="diabetes"),
    buyer_id: str = Query(..., example="buyer_1")
):
    # Check if buyer exists
    if buyer_id not in buyers:
        return {"error": "Buyer ID not recognised"}

    # Check token balance
    if buyers[buyer_id]["tokens"] <= 0:
        return {"error": "Insufficient tokens", "code": 402}

    # Deduct one token
    buyers[buyer_id]["tokens"] -= 1
    # Distribute tokens to hospitals (equal split)
    hospitals["Hospital_A"]["tokens"] += 0.5
    hospitals["Hospital_B"]["tokens"] += 0.5


    # Query both hospitals
    urls = [
        f"http://localhost:8001/query?condition={condition}",
        f"http://localhost:8002/query?condition={condition}"
    ]

    results = []
    async with httpx.AsyncClient() as client:
        for url in urls:
            try:
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    results.append(data["avg_age"])
            except Exception as e:
                continue  # Skip if a hospital is down

    if not results:
        return {"error": "No data returned from any hospital"}

    # Aggregate results
    combined_avg = sum(results) / len(results)

    # Apply differential privacy
    noisy_avg = apply_differential_privacy(combined_avg)

    return {
        "buyer_id": buyer_id,
        "condition": condition,
        "noisy_average_age": round(noisy_avg, 2),
        "sources": len(results),
        "tokens_remaining": buyers[buyer_id]["tokens"],
        "hospital_earnings": {
            "Hospital_A": hospitals["Hospital_A"]["tokens"],
            "Hospital_B": hospitals["Hospital_B"]["tokens"]
        }
    }