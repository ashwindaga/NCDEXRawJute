import datetime
import json
import os
from playwright.sync_api import sync_playwright


def fetch_latest_price():
  # Yesterday's date in YYYY-MM-DD format
  yesterday = datetime.date.today() - datetime.timedelta(days=1)
  date_str = yesterday.strftime("%Y-%m-%d")

  result_payload = {
      "status": "error",
      "message": f"No price found for {date_str}",
      "product": "JUTRAWKOL",
      "center": "Kolkatta",
      "date": date_str,
      "time": "N/A",
      "price": "N/A",
  }

  with sync_playwright() as p:
    # 1. Launch browser in headful/headless container context
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    try:
      # 2. Establish session & pass JS challenge
      page.goto(
          "https://www.ncdex.com/markets/spotprices", wait_until="networkidle"
      )
      page.wait_for_timeout(2500)

      # 3. Direct AJAX query against backend DataTables endpoint
      ajax_script = f"""
            async () => {{
                return new Promise((resolve) => {{
                    if (window.jQuery) {{
                        window.jQuery.ajax({{
                            url: '/spotprices/get_data',
                            type: 'POST',
                            data: {{
                                draw: 1,
                                start: 0,
                                length: 10,
                                product: 'JUTRAWKOL',
                                df: '{date_str}',
                                dt: '{date_str}'
                            }},
                            headers: {{
                                'X-CSRF-TOKEN': jQuery('meta[name="csrf-token"]').attr('content')
                            }},
                            success: function(res) {{ resolve(res); }},
                            error: function() {{ resolve(null); }}
                        }});
                    }} else {{
                        resolve(null);
                    }}
                }});
            }}
            """

      response = page.evaluate(ajax_script)

      # 4. Parse JSON Response
      if response and "data" in response and len(response["data"]) > 0:
        latest_record = response["data"][-1]  # Get most recent intraday quote

        # Standard array structure: [Product, Center, Date, Time, Price]
        result_payload = {
            "status": "success",
            "product": latest_record[0]
            if len(latest_record) > 0
            else "JUTRAWKOL",
            "center": latest_record[1] if len(latest_record) > 1 else "Kolkatta",
            "date": latest_record[2] if len(latest_record) > 2 else date_str,
            "time": latest_record[3] if len(latest_record) > 3 else "N/A",
            "price": latest_record[4] if len(latest_record) > 4 else "N/A",
        }

    except Exception as e:
      result_payload["message"] = str(e)
    finally:
      browser.close()

  # 5. Output clean JSON file for iOS Shortcut consumption
  os.makedirs("data", exist_ok=True)
  with open("data/latest.json", "w", encoding="utf-8") as f:
    json.dump(result_payload, f, indent=2)

  print("[INFO] Execution payload saved to data/latest.json:")
  print(json.dumps(result_payload, indent=2))


if __name__ == "__main__":
  fetch_latest_price()
