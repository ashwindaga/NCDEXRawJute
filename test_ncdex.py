import datetime
import json
from playwright.sync_api import sync_playwright


def test_ncdex_fetch():
  # 1. Format date as YYYY-MM-DD
  yesterday = datetime.date.today() - datetime.timedelta(days=1)
  date_str = yesterday.strftime("%Y-%m-%d")

  print("=" * 60)
  print(f"[INFO] Starting CSRF-Authenticated NCDEX API Test")
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

    # Step 1: Load page to establish session & pass JS challenge
    print("\n[STEP 1] Navigating to NCDEX Spot Prices page...")
    page.goto("https://www.ncdex.com/markets/spotprices", wait_until="networkidle")
    page.wait_for_timeout(3000)

    # Step 2: Extract CSRF Token from DOM
    print("\n[STEP 2] Extracting CSRF Token from DOM...")
    csrf_token = page.evaluate("""() => {
            const meta = document.querySelector('meta[name="csrf-token"]');
            if (meta) return meta.getAttribute('content');
            const input = document.querySelector('input[name="_token"]');
            if (input) return input.value;
            return window.Laravel ? window.Laravel.csrfToken : '';
        }""")

    print(
        f"  Extracted CSRF Token:"
        f" {csrf_token[:10]}...{csrf_token[-10:] if csrf_token else 'NONE'}"
    )

    # Step 3: Execute fetch INSIDE the browser page context
    print(
        f"\n[STEP 3] Executing in-page AJAX fetch for date {date_str} with CSRF"
        " token..."
    )

    fetch_js = f"""
        async () => {{
            const token = '{csrf_token}';
            const params = new URLSearchParams();
            params.append('product', 'JUTRAWKOL');
            params.append('df', '{date_str}');
            params.append('dt', '{date_str}');
            if (token) params.append('_token', token);

            const headers = {{
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json, text/javascript, */*; q=0.01'
            }};
            if (token) headers['X-CSRF-TOKEN'] = token;

            const response = await fetch('/spotprices/get_data', {{
                method: 'POST',
                headers: headers,
                body: params.toString()
            }});

            return await response.text();
        }}
        """

    raw_response = page.evaluate(fetch_js)

    print("\n" + "=" * 60)
    print("[RESULTS] API Response:")
    print("=" * 60)

    try:
      data = json.loads(raw_response)
      print(json.dumps(data, indent=2))
    except Exception as e:
      print(f"Failed to parse JSON ({e}). Raw response:")
      print(raw_response[:1000])

    browser.close()


if __name__ == "__main__":
  test_ncdex_fetch()
