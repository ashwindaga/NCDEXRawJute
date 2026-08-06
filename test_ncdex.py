import datetime
import json
from playwright.sync_api import sync_playwright


def test_ncdex_fetch():
  # Get yesterday's date in 'DD-MMM-YYYY' format (e.g., 05-Aug-2026)
  yesterday = datetime.date.today() - datetime.timedelta(days=1)
  date_str = yesterday.strftime("%d-%b-%Y")

  print("=" * 60)
  print(f"[INFO] Starting Playwright Test Runner")
  print(f"[INFO] Target Date: {date_str}")
  print("=" * 60)

  with sync_playwright() as p:
    # 1. Launch Headless Chromium Browser
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
    )
    page = context.new_page()

    # 2. Visit NCDEX to execute JS fingerprint challenge
    print("\n[STEP 1] Navigating to NCDEX Spot Prices page...")
    page.goto("https://www.ncdex.com/markets/spotprices", wait_until="networkidle")

    # Wait 3 seconds to ensure client-side security scripts execute and cookies are stored
    page.wait_for_timeout(3000)
    print("[STEP 1] Navigation complete. JS fingerprint cookies acquired.")

    # 3. Trigger POST Request from within authenticated browser environment
    print(
        f"[STEP 2] Dispatching POST request for product JUTRAWKOL on"
        f" {date_str}..."
    )

    fetch_script = f"""
        async () => {{
            const formData = new FormData();
            formData.append('product_id', 'JUTRAWKOL');
            formData.append('from_date', '{date_str}');
            formData.append('to_date', '{date_str}');

            const response = await fetch('https://www.ncdex.com/Market/HistoricalData/GetHistoricalSpotPrices', {{
                method: 'POST',
                body: formData
            }});
            return await response.text();
        }}
        """

    raw_response = page.evaluate(fetch_script)

    print("\n" + "=" * 60)
    print("[CONSOLE LOG - RAW RESPONSE FROM NCDEX]")
    print("=" * 60)

    # 4. Parse & Verify JSON Output
    try:
      parsed_data = json.loads(raw_response)
      print(f"\n[SUCCESS] Response is valid JSON! Records received:")
      print(json.dumps(parsed_data, indent=2))
    except Exception as e:
      print(
          f"\n[FAIL] Could not parse response as JSON. Error: {e}\nRaw"
          " snippet:"
      )
      print(
          raw_response[:2000]
      )  # Print first 2000 characters to inspect output

    browser.close()


if __name__ == "__main__":
  test_ncdex_fetch()
