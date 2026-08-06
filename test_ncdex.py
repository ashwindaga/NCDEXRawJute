import datetime
import json
from playwright.sync_api import sync_playwright


def test_ncdex_fetch():
  yesterday = datetime.date.today() - datetime.timedelta(days=1)
  date_str = yesterday.strftime("%d-%b-%Y")  # e.g. 05-Aug-2026

  print("=" * 60)
  print(f"[INFO] Starting Playwright Test Scraper")
  print(f"[INFO] Target Date: {date_str}")
  print("=" * 60)

  with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1400, "height": 900},
    )
    page = context.new_page()

    # Track network traffic to uncover exact internal endpoints
    intercepted_responses = []

    def handle_response(response):
      try:
        url = response.url.lower()
        content_type = response.headers.get("content-type", "").lower()
        if "json" in content_type or "spot" in url or "historical" in url:
          if response.status == 200:
            intercepted_responses.append({
                "url": response.url,
                "status": response.status,
                "body": response.text()[:1000],
            })
      except Exception:
        pass

    page.on("response", handle_response)

    # STEP 1: Navigate to page
    print("\n[STEP 1] Navigating to NCDEX Spot Prices page...")
    page.goto("https://www.ncdex.com/markets/spotprices", wait_until="networkidle")
    page.wait_for_timeout(4000)
    print("[STEP 1] Session initialized.")

    # STEP 2: Element Inspection Debugging
    print("\n[DEBUG] Discovering UI Form Inputs:")
    inputs = page.locator("input").all()
    for idx, inp in enumerate(inputs):
      try:
        ph = inp.get_attribute("placeholder") or ""
        val = inp.input_value() or ""
        name = inp.get_attribute("name") or ""
        cls = inp.get_attribute("class") or ""
        print(
            f"  Input #{idx+1}: name='{name}', class='{cls}',"
            f" placeholder='{ph}', val='{val}'"
        )
      except Exception:
        pass

    # STEP 3: Interact with Product Search Autocomplete
    print("\n[STEP 2] Typing 'JUTRAWKOL' into Product Search...")
    prod_input = page.locator(
        "input[placeholder*='Choose product'], input[placeholder*='product'],"
        " input[type='text']"
    ).first
    prod_input.click()
    prod_input.fill("JUTRAWKOL")
    page.wait_for_timeout(1500)

    # Look for and click autocomplete dropdown item
    suggestion = page.locator(
        "li:has-text('JUTRAWKOL'), div:has-text('JUTRAWKOL'),"
        " .ui-menu-item, .select2-result"
    ).first
    if suggestion.count() > 0 and suggestion.is_visible():
      print("  [ACTION] Clicking autocomplete suggestion option...")
      suggestion.click()
    else:
      print("  [ACTION] Pressing Enter key...")
      page.keyboard.press("Enter")

    page.wait_for_timeout(1000)

    # STEP 4: Set Date Fields
    print("\n[STEP 3] Setting Date Filters...")
    date_fields = page.locator(
      "input[placeholder*='date'], input[placeholder*='Date'],"
      " input.hasDatepicker, input[name*='date']"
    ).all()

    if len(date_fields) >= 2:
      print(
          f"  Found {len(date_fields)} date fields. Setting to"
          f" '{date_str}'..."
      )
      date_fields[0].click()
      date_fields[0].fill(date_str)
      date_fields[1].click()
      date_fields[1].fill(date_str)
      page.keyboard.press("Escape")
    elif len(date_fields) == 1:
      date_fields[0].fill(date_str)

    # STEP 5: Click Show Button
    print("\n[STEP 4] Clicking 'Show' button...")
    show_btn = page.locator(
        "button:has-text('Show'), input[value='Show'], .btn-primary,"
        " #btnShow"
    ).first
    show_btn.click()

    print("  Waiting 5 seconds for data table render...")
    page.wait_for_timeout(5000)

    # STEP 6: Extract Table Data
    print("\n" + "=" * 60)
    print("[RESULTS] Rendered Table Data from DOM:")
    print("=" * 60)

    rows = page.locator("table tr").all()
    extracted_table = []
    for r in rows:
      text = r.inner_text().strip()
      if text:
        cols = [c.strip() for c in text.split("\t") if c.strip()]
        if cols:
          extracted_table.append(cols)

    print(json.dumps(extracted_table, indent=2))

    # STEP 7: Print Network Interception Findings
    if intercepted_responses:
      print("\n" + "=" * 60)
      print("[DEBUG] Intercepted Background Network Endpoints:")
      print("=" * 60)
      for resp in intercepted_responses:
        print(f"URL: {resp['url']} | Status: {resp['status']}")
        print(f"Snippet: {resp['body']}\n")

    browser.close()


if __name__ == "__main__":
  test_ncdex_fetch()
