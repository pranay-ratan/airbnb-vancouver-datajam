"""Render the 3D room tour to video.

The scene (scene.html, three.js) is a one-bedroom downtown condo that switches from the
May-August nightly set-up to the September-April furnished set-up. Every number shown in
it is read from outputs/metrics.json and injected here, so the video cannot disagree
with the pitch.

    cd deliverables/room_tour && npm install && python3 -I build_room_tour.py
    -> outputs/pitch/room_tour.mp4 and outputs/pitch/room_tour.jpg (poster frame)

Needs Google Chrome (for H.264-capable rendering) and ffmpeg.
"""
import sys, json, pathlib, shutil, subprocess, threading, functools, http.server, socketserver
sys.path.insert(0, "")
from playwright.sync_api import sync_playwright

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "outputs/pitch"; OUT.mkdir(parents=True, exist_ok=True)
FRAMES = HERE / "frames"
FPS, W, H = 30, 1600, 900

M = json.loads((ROOT / "outputs/metrics.json").read_text())
A, R, S = M["assumptions"], M["recommendation"], M["seasonality"]
CFG = {
    "furnish": A["furnish_base"]["condo"] + A["furnish_per_bed"] * 1,   # one-bedroom condo
    "midRent": A["mid_rent"]["1"],
    "midMonths": A["mid_months"],
    "summerNights": round(R["unit_nights"] * S["peak_share"]),
    "units": R["units"],
}

class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass

def serve():
    handler = functools.partial(Quiet, directory=str(HERE))
    srv = socketserver.TCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv

def main():
    if FRAMES.exists(): shutil.rmtree(FRAMES)
    FRAMES.mkdir()
    srv = serve(); port = srv.server_address[1]
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path="/usr/bin/google-chrome",
                              args=["--no-sandbox", "--use-angle=swiftshader", "--enable-unsafe-swiftshader", "--ignore-gpu-blocklist"])
        pg = b.new_page(viewport={"width": W, "height": H})
        pg.add_init_script(f"window.__CFG = {json.dumps(CFG)};")
        pg.goto(f"http://127.0.0.1:{port}/scene.html")
        pg.wait_for_function("window.ready === true", timeout=120000)
        dur = pg.evaluate("window.DUR")
        n = int(dur * FPS)
        for i in range(n):
            pg.evaluate(f"window.renderAt({i / FPS})")
            pg.screenshot(path=str(FRAMES / f"f{i:04d}.png"))
            if i % 150 == 0: print(f"frame {i}/{n}", flush=True)
        pg.evaluate("window.renderAt(9.0)")                       # poster: the home, labelled
        pg.screenshot(path=str(OUT / "room_tour.jpg"), type="jpeg", quality=88)
        b.close()
    srv.shutdown()
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", str(FRAMES / "f%04d.png"),
                    "-c:v", "libx264", "-preset", "slow", "-crf", "22", "-pix_fmt", "yuv420p",
                    "-movflags", "+faststart", str(OUT / "room_tour.mp4")], check=True)
    shutil.rmtree(FRAMES)
    mb = (OUT / "room_tour.mp4").stat().st_size / 1e6
    print(f"wrote outputs/pitch/room_tour.mp4 ({mb:.1f} MB, {n} frames, {dur:.0f}s) and room_tour.jpg")

if __name__ == "__main__":
    main()
