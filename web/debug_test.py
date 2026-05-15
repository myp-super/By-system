"""Debug: Open browser and check JS errors on the page."""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # Capture console errors
    errors = []
    page.on('console', lambda msg: None)
    page.on('pageerror', lambda err: errors.append(str(err)))

    print('Loading page...')
    page.goto('http://localhost:5000', timeout=15000)
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(2000)

    # Screenshot
    page.screenshot(path='debug_screenshot.png', full_page=True)
    print('Screenshot saved: debug_screenshot.png')

    # Report errors
    if errors:
        print(f'\n=== JS ERRORS FOUND ({len(errors)}) ===')
        for i, err in enumerate(errors[:10]):
            print(f'  Error {i+1}: {err[:200]}')
    else:
        print('No JS errors found')

    # Try clicking nav items
    nav_items = page.locator('.nav-item').all()
    print(f'\nNav items found: {len(nav_items)}')
    for item in nav_items:
        text = item.text_content()[:30]
        print(f'  - {text}')

    # Try clicking first nav item
    if nav_items:
        print('\nClicking second nav item (保研通知)...')
        nav_items[1].click()
        page.wait_for_timeout(1000)
        page.screenshot(path='debug_after_click.png', full_page=True)
        print('Screenshot after click: debug_after_click.png')

    browser.close()
