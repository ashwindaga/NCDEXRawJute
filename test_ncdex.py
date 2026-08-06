import datetime
import json
from playwright.sync_api import sync_playwright


def test_ncdex_fetch():
  yesterday = datetime.date.today() - datetime.timedelta(days=1)
  date_ymd = yesterday.strftime("%Y-%m-%d")  # 2026-08-05

  print("=" * 60)
  print(f"[INFO] Running NCDEX Scraper")
  print(f"[INFO] Target Date: {date_ymd}")
  print("=" * 60)

  with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
        ],
    )
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1400, "height": 900},
    )
    page = context.new_page()

    # 1. Initialize session and bypass JS security challenge
    print("[1/4] Loading NCDEX Spot Prices page...")
    page.goto("https://www.ncdex.com/markets/spotprices", wait_until="networkidle")
    page.wait_for_timeout(4000)

    # 2. Inject DOM updates for Product & Duet Date Pickers
    print("[2/4] Setting Product and Duet Date Pickers...")

    fill_script = f"""
        () => {{
            let log = [];
            
            // A. Set Product Dropdown / Select
            let selects = document.querySelectorAll('select');
            let foundProduct = false;
            selects.forEach(s => {{
                for (let opt of s.options) {{
                    if (opt.text.includes('JUTRAWKOL') || opt.value.includes('JUTRAWKOL') || opt.text.includes('Jute Raw')) {{
                        s.value = opt.value;
                        s.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        foundProduct = true;
                        log.push('Selected product: ' + opt.text);
                        break;
                    }}
                }}
            }});

            if (!foundProduct) {{
                let pInput = document.querySelector('input[placeholder*="product" i], input[placeholder*="Choose" i]');
                if (pInput) {{
                    pInput.value = 'JUTRAWKOL (Jute Raw | Kolkatta)';
                    pInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    pInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    log.push('Filled product input box');
                }}
            }}

            // B. Set <duet-date-picker> custom components discovered in logs
            let duetPickers = document.querySelectorAll('duet-date-picker');
            if (duetPickers.length >= 2) {{
                duetPickers[0].value = '{date_ymd}';
                duetPickers[1].value = '{date_ymd}';
                duetPickers[0].dispatchEvent(new Event('duetChange', {{ bubbles: true }}));
                duetPickers[1].dispatchEvent(new Event('duetChange', {{ bubbles: true }}));
                log.push('Set duet-date-picker values to {date_ymd}');
            }}

            // C. Set fallback hidden/text inputs (df & dt)
            let inputs = document.querySelectorAll('input[name="df"], input[name="dt"], input.duet-date__input');
            inputs.forEach(i => {{
                i.value = '{date_ymd}';
                i.dispatchEvent(new Event('input', {{ bubbles: true }}));
                i.dispatchEvent(new Event('change', {{ bubbles: true }}));
            }});

            return log;
        }}
        """

    dom_logs = page.evaluate(fill_script)
    for entry in dom_logs:
      print(f"  -> {entry}")

    # 3. Click 'Show'
    print("[3/4] Clicking 'Show' button...")
    page.evaluate("""() => {
            let btns = Array.from(document.querySelectorAll('button, input[type="button"], input[type="submit"], .btn'));
            let showBtn = btns.find(b => (b.innerText || b.value || '').trim().toLowerCase() === 'show');
            if (showBtn) showBtn.click();
        }""")

    # 4. Poll table until data loads
    print("[4/4] Waiting for data table to render...")

    data_found = False
    result_rows = []

    for _ in range(12):  # Poll for up to 12 seconds
      page.wait_for_timeout(1000)
      rows = page.locator("table tbody tr").all()
      extracted = []

      for r in rows:
        text = r.inner_text().strip()
        if (
            text
            and "No data available" not in text
            and "Loading" not in text
            and "Product Name" not in text
        ):
          cols = [c.strip() for c in text.split("\t") if c.strip()]
          if len(cols) >= 3:
            extracted.append(cols)

      if extracted:
        result_rows = extracted
        data_found = True
        break

    print("\n" + "=" * 60)
    if data_found:
      print("[SUCCESS] Extracted Raw Jute Spot Price:")
      print("=" * 60)
      print(json.dumps(result_rows, indent=2))
    else:
      print("[TABLE SNAPSHOT]:")
      table_text = page.locator("table").inner_text()
      print(table_text)

    browser.close()


if __name__ == "__main__":
  test_ncdex_fetch()
