import datetime
import json
from playwright.sync_api import sync_playwright


def test_ncdex_fetch():
  # Target Date (Yesterday formatted as 'DD-MMM-YYYY', e.g., 05-Aug-2026)
  yesterday = datetime.date.today() - datetime.timedelta(days=1)
  date_str = yesterday.strftime("%d-%b-%Y")

  print("=" * 60)
  print(f"[INFO] Starting Playwright Test Scraper")
  print(f"[INFO] Target Date: {date_str}")
  print("=" * 60)

  with sync_playwright() as p:
    # 1. Launch Browser
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1400, "height": 900},
    )
    page = context.new_page()

    # 2. Pass JavaScript Fingerprint Challenge
    print("\n[STEP 1] Navigating to NCDEX Spot Prices page...")
    page.goto("https://www.ncdex.com/markets/spotprices", wait_until="networkidle")
    page.wait_for_timeout(3000)
    print("[STEP 1] Session initialized & fingerprint challenge passed.")

    # 3. Method 1: Context Request (Re-uses session cookies & posts form-urlencoded)
    print(
        f"\n[STEP 2] Dispatching form-encoded POST via Playwright context request..."
    )

    endpoint = (
        "https://www.ncdex.com/Market/HistoricalData/GetHistoricalSpotPrices"
    )
    response = context.request.post(
        endpoint,
        form={
            "product_id": "JUTRAWKOL",
            "from_date": date_str,
            "to_date": date_str,
        },
        headers={
            "X-Requested-With": "XMLHttpRequest",
            "Referer": "https://www.ncdex.com/markets/spotprices",
            "Accept": "application/json, text/javascript, */*; q=0.01",
        },
    )

    status_code = response.status
    response_text = response.text()

    print(f"[HTTP STATUS] Code: {status_code}")

    # 4. Process & Verify Response Output
    is_success = False
    try:
      data = json.loads(response_text)
      print("\n" + "=" * 60)
      print("[SUCCESS] Received clean JSON response from NCDEX:")
      print("=" * 60)
      print(json.dumps(data, indent=2))
      is_success = True
    except Exception as e:
      print(
          f"[WARN] Response was not valid JSON ({e}). Raw snippet:"
          f" {response_text[:500]}"
      )

    # 5. Method 2 Fallback: Native Select2 JS Injection & Form Trigger
    if not is_success:
      print(
          "\n[STEP 3] Fallback: Injecting Select2 dropdown value & triggering"
          " form submit..."
      )

      # Inject form values directly via JavaScript
      page.evaluate(
          f"""() => {{
                if (window.jQuery) {{
                    jQuery('select').val('JUTRAWKOL').trigger('change');
                    jQuery('input[name*="from"], #from_date').val('{date_str}');
                    jQuery('input[name*="to"], #to_date').val('{date_str}');
                }}
            }}"""
      )

      # Click 'Show' button
      show_button = page.locator("button:has-text('Show'), #btnShow").first
      if show_button.count() > 0:
        show_button.click()
        page.wait_for_timeout(4000)

      # Extract table text directly
      rows = page.locator("table tr").all()
      table_data = [
          [c.strip() for c in r.inner_text().split("\t") if c.strip()]
          for r in rows
          if r.inner_text().strip()
      ]

      print("\n" + "=" * 60)
      print("[SUCCESS] Table DOM Scrape Result:")
      print("=" * 60)
      print(json.dumps(table_data, indent=2))

    browser.close()


if __name__ == "__main__":
  test_ncdex_fetch()
