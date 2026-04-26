import os
import time
from playwright.sync_api import sync_playwright

BASE_URL = "http://127.0.0.1"
SCREENSHOT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")

USERNAME = "admin"
PASSWORD = "admin123"

def capture_auth_session():
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Setup context. The same context shares cookies.
        context = browser.new_context(viewport={"width": 1920, "height": 1080}, device_scale_factor=2)
        page = context.new_page()

        print(f"Navigating to {BASE_URL}/accounts/login/ for explicit login...")
        page.goto(f"{BASE_URL}/accounts/login/")
        
        # 1. Login Page Capture
        time.sleep(1)
        page.screenshot(path=os.path.join(SCREENSHOT_DIR, "00_login.png"), full_page=True)
        print("Captured 00_login.png")

        # Perform Login explicitly
        if page.locator("input[name='username']").count() > 0:
            print(f"Logging in with {USERNAME} / {PASSWORD}")
            page.fill("input[name='username']", USERNAME)
            page.fill("input[name='password']", PASSWORD)
            
            # Click submit. We don't always need expect_navigation if JS handles it, but usually it's a form post.
            page.click("button[type='submit']")
            page.wait_for_load_state("networkidle")
            time.sleep(2)
            
            print("Login completed. Current URL:", page.url)
        
        # List of pages to capture sequentially
        # We use relative paths and append to BASE_URL.
        pages_to_capture = [
            ("01_hms_dashboard", "/"),
            ("02_admissions_dashboard", "/admissions/"),
            ("03_admissions_admit", "/admissions/admit/"),
            ("04_appointments_staff", "/appointments/staff-dashboard/"),
            ("05_appointments_doctor", "/appointments/doctor-console/"),
            ("06_billing_dashboard", "/billing/dashboard/"),
            ("07_pharmacy_dashboard", "/pharmacy/dashboard/"),
            ("08_pharmacy_pos", "/pharmacy/pos/"),
            ("09_pharmacy_purchase_orders", "/pharmacy/purchase-orders/"),
            ("10_pharmacy_returns", "/pharmacy/return/"),
            ("11_inventory_dashboard", "/inventory/dashboard/"),
            ("12_inventory_list", "/inventory/list/"),
            ("13_inventory_vendors", "/inventory/vendors/"),
            ("14_doctors_list", "/doctors/doctors/"),
            ("15_departments", "/doctors/specialities/"),
            ("16_staff_attendance", "/staff/dashboard/"),
            ("17_staff_admin", "/staff/admin/"),
            ("18_admin_console", "/admin/"),
        ]

        for name, path in pages_to_capture:
            url = f"{BASE_URL}{path}"
            print(f"Navigating to {url}...")
            # We use the SAME page object so the session cookie is guaranteed to be sent
            page.goto(url)
            page.wait_for_load_state("networkidle")
            time.sleep(2)  # Allow animations, charts or lazy-loaded tables to render
            
            # Additional check: If we somehow got redirected to login, printing it helps debug
            if "login" in page.url.lower():
                print(f"WARNING: Redirected to login while trying to access {url}")
            
            filepath = os.path.join(SCREENSHOT_DIR, f"{name}.png")
            page.screenshot(path=filepath, full_page=True)
            print(f"Captured {name}.png")

        browser.close()
        print(f"\nAll screenshots saved to {SCREENSHOT_DIR}")

if __name__ == "__main__":
    capture_auth_session()
