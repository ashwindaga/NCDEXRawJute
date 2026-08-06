import datetime
import json
from playwright.sync_api import sync_playwright


def test_ncdex_fetch():
  # 1. Target Date (Yesterday in 'DD-MMM-YYYY' format, e.g., 05-Aug-2026)
  yesterday = datetime.date.today() - datetime.timedelta(days=1)
  date_str = yesterday.strftime("%d-%b-%Y")

  print("=" * 60)
  print(f"[INFO] Starting Playwright Test Scraper")
  print(f"[INFO] Target Date: {date_str}")
  print("=" * 60)

  with sync_playwright() as p:
    # 2. Launch Chromium Browser
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1280, "height": 800},
    )
    page = context.new_page()

    # Navigate to establish session & acquire security cookies
    print("\n[STEP 1] Navigating to NCDEX Spot Prices page...")
    page.goto("https://www.ncdex.com/markets/spotprices", wait_until="networkidle")
    page.wait_for_timeout(3000)
    print("[STEP 1] Session initialized.")

    # -------------------------------------------------------------
    # STRATEGY 1: Corrected POST Request with URLSearchParams & Headers
    # -------------------------------------------------------------
    print(f"\n[STEP 2 - API] Dispatching POST request with URLSearchParams...")

    api_script = f"""
        async () => {{
            const params = new URLSearchParams();
            params.append('product_id', 'JUTRAWKOL');
            params.append('from_date', '{date_str}');
            params.append('to_date', '{date_str}');

            const response = await fetch('https://www.ncdex.com/Market/HistoricalData/GetHistoricalSpotPrices', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                    'X-Requested-With': 'XMLHttpRequest',
                    'Accept': 'application/json, text/javascript, */*; q=0.01'
                }},
                body: params.toString()
            }});
            return await response.text();
        }}
        """

    raw_response = page.evaluate(api_script)

    is_json = False
    try:
      parsed_data = json.loads(raw_response)
      is_json = True
      print("\n" + "=" * 60)
      print("[SUCCESS] API returned valid JSON response:")
      print("=" * 60)
      print(json.dumps(parsed_data, indent=2))
    except Exception:
      print("[WARN] Direct API call returned non-JSON. Falling back to UI automation...")

    # -------------------------------------------------------------
    # STRATEGY 2: UI Automation Fallback (DOM Extraction)
    # -------------------------------------------------------------
    if not is_json:
      print("\n[STEP 2 - UI] Interacting with page form directly...")

      # Click 'Show' button to populate grid
      show_btn = page.locator("button:has-text('Show'), #btnShow, .btn-primary")
      if show_btn.count() > 0:
        show_btn.first.click()
        page.wait_for_timeout(4000)

      # Extract table rows directly from page DOM
      table_rows = page.locator("table tr").all()
      extracted_data = []

      for row in table_rows:
        text = row.inner_text().strip()
        if text:
          cols = [c.strip() for c in text.split("\t") if c.strip()]
          extracted_data.append(cols)

      print("\n" + "=" * 60)
      print(
          f"[SUCCESS] Scraped {len(extracted_data)} row(s) directly from UI Table DOM:"
      )
      print("=" * 60)
      print(json.dumps(extracted_data, indent=2))

    browser.close()


if __name__ == "__main__":
  test_ncdex_fetch()
