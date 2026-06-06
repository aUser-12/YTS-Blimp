import io
import queue
import socket
import struct
import threading
from datetime import datetime

import numpy as np
from PIL import Image, ImageTk
import tkinter as tk

UDP_HOST       = "0.0.0.0"
UDP_PORT       = 5005
CAM_W, CAM_H   = 160, 120
DISP_W, DISP_H = 640, 480
SOCK_BUF       = 512 * 1024


class ESP32CameraGUI:
    def __init__(self, root: tk.Tk):
        self.root        = root
        self.root.title("ESP32 Camera — UDP")
        self.root.resizable(False, False)

        self.current_pil = None
        self.current_tk  = None
        self.running     = True
        self._frame_q    = queue.Queue(maxsize=2)  # maxsize=2 drops stale frames naturally

        self.image_label = tk.Label(root, bg="black", width=DISP_W, height=DISP_H)
        self.image_label.pack()

        tk.Button(
            root,
            text="Capture Frame",
            command=self.capture,
            font=("Helvetica", 12, "bold"),
            bg="#2ecc71", fg="white",
            activebackground="#27ae60",
            relief="flat", padx=20, pady=8,
        ).pack(pady=10)

        threading.Thread(target=self._recv_loop,   daemon=True).start()
        threading.Thread(target=self._decode_loop, daemon=True).start()

    def _recv_loop(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, SOCK_BUF)
        sock.bind((UDP_HOST, UDP_PORT))
        sock.settimeout(2.0)
        print(f"Listening for UDP on port {UDP_PORT}…")

        while self.running:
            try:
                # Step 1: 4-byte frame-length header
                header, _ = sock.recvfrom(4)
                if len(header) != 4:
                    continue
                expected = struct.unpack(">I", header)[0]

                if expected == 0 or expected > 1_000_000:
                    print(f"Bad frame length: {expected}")
                    continue

                # Step 2: collect chunks until full frame received
                buf = bytearray()
                sock.settimeout(1.0)
                while len(buf) < expected:
                    try:
                        chunk, _ = sock.recvfrom(SOCK_BUF)
                        buf.extend(chunk)
                    except socket.timeout:
                        print("Timeout waiting for frame data — dropping partial frame")
                        buf.clear()
                        break
                sock.settimeout(2.0)

                if len(buf) < expected:
                    continue

                # Step 3: enqueue raw bytes; drop frame if decode thread is behind
                try:
                    self._frame_q.put_nowait(bytes(buf[:expected]))
                except queue.Full:
                    pass

            except socket.timeout:
                pass
            except Exception as e:
                print("Recv error:", e)


    def _decode_loop(self):
        while self.running:
            try:
                raw = self._frame_q.get(timeout=1.0)
            except queue.Empty:
                continue

            try:
                if len(raw) == CAM_W * CAM_H:
                    arr = np.frombuffer(raw, dtype=np.uint8).reshape((CAM_H, CAM_W))
                    img = Image.fromarray(arr, mode="L").convert("RGB")
                else:
                    img = Image.open(io.BytesIO(raw)).convert("RGB")

                self.current_pil = img.copy()
                display = img.resize((DISP_W, DISP_H), Image.Resampling.NEAREST)
                tk_img  = ImageTk.PhotoImage(display)
                self.root.after(0, self._update_display, tk_img)

            except Exception as e:
                print("Decode error:", e)

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
    app  = ESP32CameraGUI(root)
    root.protocol(
        "WM_DELETE_WINDOW",
        lambda: (setattr(app, "running", False), root.destroy())
    )
    root.mainloop()