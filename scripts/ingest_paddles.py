import asyncio
import pandas as pd
from playwright.async_api import async_playwright

TARGET_URL = "https://thepickleballstudio.notion.site/5bdf3ee752c940eba864a81bc3281164?v=a5170d43e5ab4573b18f48c363cce7ec"
OUTPUT_FILE = "data/raw/paddle_stats_dump.csv"

async def scrape_notion_table():
    async with async_playwright() as p:
        print("Launching browser...")
        browser = await p.chromium.launch(headless=True)
        # 4k Viewport
        context = await browser.new_context(viewport={'width': 3840, 'height': 2160}) 
        page = await context.new_page()

        print(f"Navigating to {TARGET_URL}...")
        await page.goto(TARGET_URL)
        
        print("Waiting for network idle...")
        try:
            await page.wait_for_load_state("networkidle", timeout=60000)
        except:
            pass

        print("Waiting for table rows...")
        await page.wait_for_selector('.notion-table-view-row', state="visible", timeout=30000)

        # Identifying the scrollable container
        scroller_selector = ".notion-scroller" 
        try:
            await page.wait_for_selector(scroller_selector, timeout=5000)
            use_window_scroll = False
        except:
            print("Specific scroller not found, using window scroll.")
            use_window_scroll = True

        unique_data = {} 
        
        scroll_position_y = 0
        scroll_step_y = 600
        
        print("Starting scrape + scroll loop...")
        
        no_new_data_count = 0
        
        while True:
            # Explicit Horizontal Scroll Check
            # Scroll Right to ensure right-side columns are loaded
            if not use_window_scroll:
                await page.evaluate(f"document.querySelector('{scroller_selector}').scrollTo(2000, {scroll_position_y})")
                await asyncio.sleep(0.5)
                await page.evaluate(f"document.querySelector('{scroller_selector}').scrollTo(0, {scroll_position_y})")
                await asyncio.sleep(0.5)
            
            # Now read
            row_elements = await page.locator('.notion-table-view-row').all()
            
            new_data_in_batch = False
            
            for row in row_elements:
                text = await row.inner_text()
                parts = text.split('\n')
                parts = [p.strip() for p in parts if p.strip()]
                
                if not parts or len(parts) < 2: continue
                
                key = f"{parts[0]}_{parts[1]}"
                
                if key not in unique_data:
                    unique_data[key] = parts
                    new_data_in_batch = True
                else:
                    if len(parts) > len(unique_data[key]):
                        unique_data[key] = parts

            if not new_data_in_batch:
                no_new_data_count += 1
            else:
                no_new_data_count = 0
            
            if no_new_data_count >= 10:
                print("No new data found. Finishing.")
                break

            # Scroll Down
            scroll_position_y += scroll_step_y
            if use_window_scroll:
                 await page.evaluate(f"window.scrollTo(0, {scroll_position_y})")
            else:
                 await page.evaluate(f"document.querySelector('{scroller_selector}').scrollTo(0, {scroll_position_y})")
            
            await asyncio.sleep(0.5)

        # Output
        print(f"Total unique rows collected: {len(unique_data)}")
        all_rows = list(unique_data.values())
        if not all_rows:
            print("No data found!")
            await browser.close()
            return

        max_len = max([len(r) for r in all_rows])
        print(f"Max columns detected: {max_len}")
        
        cols = [f"Col_{i}" for i in range(max_len)]
        data_for_df = []
        for r in all_rows:
            row_data = r + [None] * (max_len - len(r))
            data_for_df.append(row_data)
            
        df = pd.DataFrame(data_for_df, columns=cols)
        
        print("Saving raw dump to CSV...")
        df.to_csv(OUTPUT_FILE, index=False)
        print("Done.")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_notion_table())
