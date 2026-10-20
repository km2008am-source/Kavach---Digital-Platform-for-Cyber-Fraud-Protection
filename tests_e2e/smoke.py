from playwright.sync_api import sync_playwright
B="http://localhost:8000/#"
errs=[]
with sync_playwright() as p:
    b=p.chromium.launch(); pg=b.new_page(viewport={'width':1100,'height':900})
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type=="error" and "tile.openstreetmap" not in m.text and "ERR_" not in m.text else None)
    # Analyze
    pg.goto(B+"/analyze"); pg.click("text=Try a sample scam"); pg.click("text=Check it")
    pg.wait_for_selector(".verdict"); print("analyze:", pg.inner_text(".pill"), "| demo badge:", pg.locator(".demo-badge").count())
    pg.screenshot(path="analyze.png")
    # Services / News
    pg.goto(B+"/services"); pg.wait_for_selector(".svc-group"); print("services cards:", pg.locator("article.card").count(), "demo:", pg.locator(".demo-badge").count())
    pg.goto(B+"/news"); pg.wait_for_selector(".news-item"); print("news items:", pg.locator(".news-item").count())
    # Simulator full run
    pg.goto(B+"/simulator"); pg.click("text=Start"); pg.wait_for_selector(".quiz-q")
    for i in range(4): pg.locator(f"input[name=q{i}]").nth(1 if i<3 else 0).check()   # no,no,no,yes
    pg.click("text=Continue"); pg.wait_for_selector(".thread")
    for m in ["ok sir what should i do","I am scared please dont arrest me","no I will not pay, this is a scam"]:
        pg.fill("input[aria-label='Your reply']", m); pg.click("button:has-text('Reply')"); pg.wait_for_timeout(500)
    pg.click("button:has-text('Hang up')")
    pg.wait_for_selector(".quiz-q")
    for i in range(4): pg.locator(f"input[name=q{i}]").nth(1 if i<3 else 0).check()
    pg.click("text=Continue"); pg.wait_for_selector(".score")
    print("score card:", pg.inner_text(".score-grid").replace("\n"," "))
    pg.screenshot(path="sim.png", full_page=True)
    # Pulse
    pg.goto(B+"/pulse"); pg.click("text=Replay demo wave"); pg.wait_for_timeout(6500)
    print("pulse:", pg.inner_text(".alert-list")[:160].replace("\n"," "), "| markers:", pg.locator("path.leaflet-interactive").count())
    pg.screenshot(path="pulse.png")
    b.close()
print("errors:", errs)
