import io
import threading
import time
import tkinter as  tk
from datetime import datetime

import numpy as np
import requests
from PIL import Image, ImageTk

ESP_IP = ""
SNAPSHOT_URL = f"http://{ESP_IP}/snapshot"
REFRESH_MS = 30
CAM_W, CAM_H = 160, 120
DISP_W, DISP_H = 640, 480


class ESP32CameraGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ESP32 Camera")
        self.root.resizable(False, False)
        self.current_pil = None
        self.current_tk = None
        self.running = True

        self.image_label = tk.Label(root, bg="black", width=DISP_W, height=DISP_H)
        self.image_label.pack()

        tk.Button(
            root,
            text="Capture Frame",
            command=self.capture,
            font=("Helvetica", 12, "bold"),
            bg="#2ecc71",
            fg="white",
            activebackground="#27ae60",
            relief="flat",
            padx=20,
            pady=8,
        ).pack(pady=10)

        threading.Thread(target=self._fetch_loop, daemon=True).start()

    def _fetch_loop(self):
        while self.running:
            try:
                r = requests.get(SNAPSHOT_URL, timeout=2)
                r.raise_for_status()

                raw = r.content
                expected = CAM_W * CAM_H

                if len(raw) == expected:
                    # ── Raw grayscale bytes ──────────────────────────
                    arr = np.frombuffer(raw, dtype=np.uint8).reshape((CAM_H, CAM_W))
                    img = Image.fromarray(arr, mode="L").convert("RGB")
                else:
                    # ── Try JPEG decode as fallback ──────────────────
                    img = Image.open(io.BytesIO(raw)).convert("RGB")

                self.current_pil = img.copy()
                display = img.resize((DISP_W, DISP_H), Image.Resampling.NEAREST)
                tk_img = ImageTk.PhotoImage(display)
                self.root.after(0, self._update_display, tk_img)

            except Exception as e:
                print("Fetch error:", e)

            time.sleep(REFRESH_MS / 1000)

    def _update_display(self, tk_img):
        self.current_tk = tk_img
        self.image_label.configure(image=self.current_tk)

    def capture(self):
        if self.current_pil is None:
            return
        filename = datetime.now().strftime("capture_%Y%m%d_%H%M%S.jpg")
        self.current_pil.save(filename)
        print("Saved:", filename)

        
if __name__ == "__main__":
    root = tk.Tk()
    app = ESP32CameraGUI(root)
    root.protocol(
        "WM_DELETE_WINDOW", lambda: (setattr(app, "running", False), root.destroy())
    )
    root.mainloop()