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
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1400, "height": 900},
    )
    page = context.new_page()

    print("\n[STEP 1] Navigating to NCDEX Spot Prices page...")
    page.goto("https://www.ncdex.com/markets/spotprices", wait_until="networkidle")
    page.wait_for_timeout(3000)

    # -------------------------------------------------------------
    # STEP 2: Fill UI Form Controls
    # -------------------------------------------------------------
    print("[STEP 2] Filling form controls...")

    # Select Product (JUTRAWKOL)
    product_input = page.locator(
        "input[placeholder*='Choose product'], input[aria-label*='Choose"
        " product'], .select2-search__field, #select2-product-container,"
        " input.select2-input"
    )

    # Click product dropdown area
    page.locator(".select2-selection, .select-product, #product_id").first.click(
        timeout=5000
    )
    page.wait_for_timeout(500)

    # Type 'JUTRAWKOL' and select from suggestions
    page.keyboard.type("JUTRAWKOL", delay=100)
    page.wait_for_timeout(1000)
    page.keyboard.press("Enter")

    # Set Date Inputs
    date_inputs = page.locator(
        "input[type='text'][placeholder*='Select date'], input.datepicker,"
        " #from_date, #to_date"
    )
    if date_inputs.count() >= 2:
      # Fill 'From Date'
      date_inputs.nth(0).click()
      date_inputs.nth(0).fill(date_str)
      # Fill 'To Date'
      date_inputs.nth(1).click()
      date_inputs.nth(1).fill(date_str)
      page.keyboard.press("Escape")  # Close calendar popup if open

    print("[STEP 2] Form inputs filled successfully.")

    # -------------------------------------------------------------
    # STEP 3: Click 'Show' & Intercept API Response
    # -------------------------------------------------------------
    print(
        "\n[STEP 3] Clicking 'Show' and listening for API response payload..."
    )

    captured_json = None

    try:
      # Expect the backend API call triggered by clicking 'Show'
      with page.expect_response(
          lambda res: "GetHistoricalSpotPrices" in res.url
          and res.status == 200,
          timeout=10000,
      ) as response_info:
        page.locator(
            "button:has-text('Show'), input[value='Show'], .btn-show"
        ).first.click()

      response = response_info.value
      captured_json = response.json()

    except Exception as e:
      print(
          f"[WARN] Network listener timed out or missed response ({e})."
          " Fallback to scraping table DOM directly..."
      )

    # -------------------------------------------------------------
    # STEP 4: Output Captured Results
    # -------------------------------------------------------------
    print("\n" + "=" * 60)
    if captured_json:
      print("[SUCCESS] Intercepted Clean JSON API Data:")
      print("=" * 60)
      print(json.dumps(captured_json, indent=2))
    else:
      # Fallback: Extract rendered DOM table rows
      page.wait_for_timeout(3000)
      rows = page.locator("table tr").all()
      table_data = [
          [c.strip() for c in r.inner_text().split("\t") if c.strip()]
          for r in rows
      ]
      print("[SUCCESS] Extracted Data from Rendered Table DOM:")
      print("=" * 60)
      print(json.dumps(table_data, indent=2))

    browser.close()


if __name__ == "__main__":
  test_ncdex_fetch()
