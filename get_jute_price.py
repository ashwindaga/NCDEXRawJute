import datetime
import json
import os
from playwright.sync_api import sync_playwright


def fetch_latest_price():
  yesterday = datetime.date.today() - datetime.timedelta(days=1)
  date_ymd = yesterday.strftime("%Y-%m-%d")

  result_payload = {
      "status": "error",
      "message": f"No price found for {date_ymd}",
      "product": "JUTRAWKOL",
      "center": "Kolkatta",
      "date": date_ymd,
      "time": "N/A",
      "price": "N/A",
  }

  with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=True,
        args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
    )
    context = browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            " (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        viewport={"width": 1400, "height": 900},
    )
    page = context.new_page()

    try:
      # 1. Load NCDEX page
      page.goto(
          "https://www.ncdex.com/markets/spotprices", wait_until="networkidle"
      )
      page.wait_for_timeout(3500)

      # 2. Inject DOM Updates (Product + Duet Date Pickers)
      fill_script = f"""
            () => {{
                let selects = document.querySelectorAll('select');
                selects.forEach(s => {{
                    for (let opt of s.options) {{
                        if (opt.text.includes('JUTRAWKOL') || opt.value.includes('JUTRAWKOL')) {{
                            s.value = opt.value;
                            s.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            break;
                        }}
                    }}
                }});

                let duetPickers = document.querySelectorAll('duet-date-picker');
                if (duetPickers.length >= 2) {{
                    duetPickers[0].value = '{date_ymd}';
                    duetPickers[1].value = '{date_ymd}';
                    duetPickers[0].dispatchEvent(new Event('duetChange', {{ bubbles: true }}));
                    duetPickers[1].dispatchEvent(new Event('duetChange', {{ bubbles: true }}));
                }}

                let inputs = document.querySelectorAll('input[name="df"], input[name="dt"], input.duet-date__input');
                inputs.forEach(i => {{
                    i.value = '{date_ymd}';
                    i.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    i.dispatchEvent(new Event('change', {{ bubbles: true }}));
                }});
            }}
            """
      page.evaluate(fill_script)

      # 3. Click Show
      page.evaluate("""() => {
                let btns = Array.from(document.querySelectorAll('button, input[type="button"], input[type="submit"], .btn'));
                let showBtn = btns.find(b => (b.innerText || b.value || '').trim().toLowerCase() === 'show');
                if (showBtn) showBtn.click();
            }""")

      # 4. Poll table for results
      extracted_rows = []
      for _ in range(10):
        page.wait_for_timeout(1000)
        rows = page.locator("table tbody tr").all()
        for r in rows:
          text = r.inner_text().strip()
          if (
              text
              and "No data available" not in text
              and "Loading" not in text
              and "Product Name" not in text
          ):
            cols = [c.strip() for c in text.split("\t") if c.strip()]
            if len(cols) >= 4:
              extracted_rows.append(cols)
        if extracted_rows:
          break

      if extracted_rows:
        latest = extracted_rows[-1]  # Extract latest intraday price
        result_payload = {
            "status": "success",
            "product": latest[0] if len(latest) > 0 else "JUTRAWKOL",
            "center": latest[1] if len(latest) > 1 else "Kolkatta",
            "date": latest[2] if len(latest) > 2 else date_ymd,
            "time": latest[3] if len(latest) > 3 else "N/A",
            "price": latest[4] if len(latest) > 4 else "N/A",
        }

    except Exception as e:
      result_payload["message"] = str(e)
    finally:
      browser.close()

  # Write output
  os.makedirs("data", exist_ok=True)
  with open("data/latest.json", "w", encoding="utf-8") as f:
    json.dump(result_payload, f, indent=2)

  print("[INFO] Execution payload saved to data/latest.json:")
  print(json.dumps(result_payload, indent=2))


if __name__ == "__main__":
  fetch_latest_price()
