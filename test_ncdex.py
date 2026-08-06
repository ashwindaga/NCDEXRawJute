import datetime
import json
from playwright.sync_api import sync_playwright


def test_ncdex_fetch():
  # 1. Format date as YYYY-MM-DD (e.g., 2026-08-05) as required by NCDEX
  yesterday = datetime.date.today() - datetime.timedelta(days=1)
  date_str = yesterday.strftime("%Y-%m-%d")

  print("=" * 60)
  print(f"[INFO] Starting Final NCDEX API Test")
  print(f"[INFO] Target Date: {date_str}")
  print("=" * 60)

  with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
    )
    page = context.new_page()

    # Step 1: Initialize session and bypass JS challenge
    print("\n[STEP 1] Initializing browser session...")
    page.goto("https://www.ncdex.com/markets/spotprices", wait_until="networkidle")
    page.wait_for_timeout(3000)

    # Step 2: Query the exact endpoint discovered in logs
    print(
        f"\n[STEP 2] Fetching data directly from /spotprices/get_data for date"
        f" {date_str}..."
    )

    endpoint = "https://www.ncdex.com/spotprices/get_data"

    # Query using session cookies with correct parameter names
    response = context.request.post(
        endpoint,
        form={"product": "JUTRAWKOL", "df": date_str, "dt": date_str},
        headers={
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://www.ncdex.com/markets/spotprices",
            "Accept": "application/json, text/javascript, */*; q=0.01",
        },
    )

    print(f"[HTTP STATUS] Code: {response.status}")
    response_text = response.text()

    print("\n" + "=" * 60)
    print("[RESULTS] API Payload Response:")
    print("=" * 60)

    try:
      data = json.loads(response_text)
      print(json.dumps(data, indent=2))
    except Exception as e:
      print(f"Failed to parse JSON ({e}). Raw response:")
      print(response_text[:1000])

    browser.close()


if __name__ == "__main__":
  test_ncdex_fetch()
