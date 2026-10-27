import datetime
import json
import os
import urllib.request
import urllib.error

API_KEY = "579b464db66ec23bdd0000013bffa05263a6484060f3933e651f550b"
RESOURCE_ID = "35985678-0d79-46b4-9ed6-6f13308a1d24"


def fetch(label, url):
    print(f"\n=== {label} ===")
    print(url.replace(API_KEY, "<api-key>"))
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
                "Accept": "application/json, text/plain, */*",
            },
        )
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            code = resp.status
    except urllib.error.HTTPError as e:
        code = e.code
        body = e.read().decode("utf-8", errors="replace")
    except Exception as e:
        return {"label": label, "exception": str(e)}

    result = {"label": label, "http_code": code, "body_len": len(body), "body_start": body[:300]}
    try:
        j = json.loads(body)
        result["status"] = j.get("status")
        result["total"] = j.get("total")
        result["count"] = j.get("count")
        result["message"] = j.get("message")
    except Exception:
        result["parsed"] = False
    return result


def main():
    yesterday = datetime.date.today() - datetime.timedelta(days=1)
    date_str = yesterday.strftime("%d-%m-%Y")

    base = (
        f"https://api.data.gov.in/resource/{RESOURCE_ID}"
        f"?api-key={API_KEY}&format=json&filters[Commodity]=Jute"
    )
    dated = f"{base}&filters[Arrival_Date]={date_str}&limit=5"
    undated = f"{base}&limit=1"

    results = [
        fetch("1) Dated request (same as Apps Script tracker)", dated),
        fetch("2) Undated reachability check", undated),
    ]

    for r in results:
        print(json.dumps(r, indent=2))

    os.makedirs("data", exist_ok=True)
    with open("data/agmarknet_test_result.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "tested_date": date_str,
                "run_at_utc": datetime.datetime.utcnow().isoformat(),
                "results": results,
            },
            f,
            indent=2,
        )


if __name__ == "__main__":
    main()
