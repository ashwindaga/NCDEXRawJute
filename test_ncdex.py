import datetime
import json
from playwright.sync_api import sync_playwright


def test_ncdex_fetch():
  # Target Date in YYYY-MM-DD format
  yesterday = datetime.date.today() - datetime.timedelta(days=1)
  date_str = yesterday.strftime("%Y-%m-%d")

  print("=" * 60)
  print(f"[INFO] Starting DataTables-Compliant NCDEX Scraper")
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

    # Step 1: Initialize Session
    print("\n[STEP 1] Initializing page session...")
    page.goto("https://www.ncdex.com/markets/spotprices", wait_until="networkidle")
    page.wait_for_timeout(3000)

    # Step 2: Execute Native jQuery DataTables AJAX Call
    print(
        f"\n[STEP 2] Executing jQuery DataTables request for 'JUTRAWKOL' on"
        f" {date_str}..."
    )

    script = f"""
        async () => {{
            return new Promise((resolve) => {{
                if (window.jQuery) {{
                    window.jQuery.ajax({{
                        url: '/spotprices/get_data',
                        type: 'POST',
                        data: {{
                            draw: 1,
                            start: 0,
                            length: 50,
                            product: 'JUTRAWKOL',
                            df: '{date_str}',
                            dt: '{date_str}',
                            'search[value]': '',
                            'search[regex]': 'false'
                        }},
                        headers: {{
                            'X-CSRF-TOKEN': jQuery('meta[name="csrf-token"]').attr('content')
                        }},
                        success: function(data) {{
                            resolve(JSON.stringify(data));
                        }},
                        error: function(xhr, status, error) {{
                            resolve(JSON.stringify({{
                                error: true,
                                status: xhr.status,
                                statusText: status,
                                responseText: xhr.responseText ? xhr.responseText.substring(0, 500) : ''
                            }}));
                        }}
                    }});
                }} else {{
                    resolve(JSON.stringify({{ error: true, message: 'jQuery not found on page' }}));
                }}
            }});
        }}
        """

    result_text = page.evaluate(script)

    print("\n" + "=" * 60)
    print("[RESULTS] API Payload Response:")
    print("=" * 60)

    try:
      parsed = json.loads(result_text)
      print(json.dumps(parsed, indent=2))
    except Exception as e:
      print(f"Failed to parse output ({e}):\n{result_text[:1000]}")

    browser.close()


if __name__ == "__main__":
  test_ncdex_fetch()
