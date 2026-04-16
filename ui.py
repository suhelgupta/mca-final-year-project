import sys
import os
import threading
import tkinter as tk
from tkinter import font as tkfont
import time
import math

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'face-recognition'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'hand-guesture'))

# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
BG        = "#05060f"
BG2       = "#0b0d1e"
PANEL     = "#0d1026"
BORDER    = "#1a2a6c"
CYAN      = "#00e5ff"
CYAN_DIM  = "#007a8a"
GREEN     = "#00ff9d"
PURPLE    = "#7b2fff"
WHITE     = "#e0e8ff"
GREY      = "#4a5568"
RED       = "#ff4466"
YELLOW    = "#ffe600"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def run_in_thread(fn, *args, **kwargs):
    t = threading.Thread(target=fn, args=args, kwargs=kwargs, daemon=True)
    t.start()
    return t


# ---------------------------------------------------------------------------
# Pulse / glow canvas animation (decorative ring)
# ---------------------------------------------------------------------------

class PulseRing(tk.Canvas):
    def __init__(self, master, size=120, color=CYAN, **kw):
        super().__init__(master, width=size, height=size,
                         bg=BG, highlightthickness=0, **kw)
        self._size = size
        self._color = color
        self._angle = 0
        self._active = False
        self._draw()

    def _draw(self):
        self.delete("all")
        cx = cy = self._size / 2
        r = self._size / 2 - 6
        # Background ring
        self.create_oval(cx - r, cy - r, cx + r, cy + r,
                         outline=BORDER, width=2)
        # Arc that rotates
        start = self._angle % 360
        self.create_arc(cx - r, cy - r, cx + r, cy + r,
                        start=start, extent=240,
                        outline=self._color, width=3, style="arc")
        # Inner icon
        ir = r * 0.45
        self.create_oval(cx - ir, cy - ir, cx + ir, cy + ir,
                         outline=self._color, width=1, fill=BG)
        # Small dot on arc tip
        tip_rad = math.radians(start)
        dx = cx + r * math.cos(tip_rad)
        dy = cy - r * math.sin(tip_rad)
        self.create_oval(dx - 4, dy - 4, dx + 4, dy + 4,
                         fill=self._color, outline="")

    def start(self):
        self._active = True
        self._spin()

    def stop(self):
        self._active = False

    def _spin(self):
        if self._active:
            self._angle += 6
            self._draw()
            self.after(30, self._spin)


# ---------------------------------------------------------------------------
# Dot processing animation
# ---------------------------------------------------------------------------

class ProcessingDots(tk.Label):
    def __init__(self, master, **kw):
        super().__init__(master, text="", bg=BG2,
                         fg=CYAN, font=("Consolas", 14), **kw)
        self._active = False
        self._frame = 0
        self._frames = ["Processing  ●○○", "Processing  ○●○", "Processing  ○○●",
                        "Processing  ○●○"]

    def start(self):
        self._active = True
        self._animate()

    def stop(self):
        self._active = False
        self.config(text="")

    def _animate(self):
        if self._active:
            self.config(text=self._frames[self._frame % len(self._frames)])
            self._frame += 1
            self.after(300, self._animate)


# ---------------------------------------------------------------------------
# AUTH WINDOW
# ---------------------------------------------------------------------------

class AuthWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Folter Assistant — Authentication")
        self.configure(bg=BG)
        self.resizable(False, False)
        self._center(520, 600)
        self._authenticated = False
        self._build()

    def _center(self, w, h):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _build(self):
        # Top decorative bar
        bar = tk.Frame(self, bg=CYAN, height=3)
        bar.pack(fill="x")

        # Title
        tk.Label(self, text="◈  FOLTER ASSISTANT  ◈",
                 bg=BG, fg=CYAN,
                 font=("Consolas", 18, "bold")).pack(pady=(28, 2))
        tk.Label(self, text="SECURE ACCESS TERMINAL",
                 bg=BG, fg=GREY,
                 font=("Consolas", 9)).pack()

        # Animated ring
        self._ring = PulseRing(self, size=150, color=CYAN)
        self._ring.pack(pady=28)

        # Status label
        self._status = tk.Label(self,
                                text="AWAITING BIOMETRIC SCAN",
                                bg=BG, fg=GREY,
                                font=("Consolas", 10))
        self._status.pack(pady=(0, 20))

        # Authenticate button
        btn_frame = tk.Frame(self, bg=BG)
        btn_frame.pack()
        self._auth_btn = tk.Button(
            btn_frame,
            text="  ▶  AUTHENTICATE  ",
            bg=PANEL, fg=CYAN,
            activebackground=CYAN, activeforeground=BG,
            relief="flat", bd=0,
            font=("Consolas", 13, "bold"),
            padx=20, pady=12,
            cursor="hand2",
            command=self._on_authenticate
        )
        self._auth_btn.pack()
        self._add_hover(self._auth_btn, CYAN, BG, PANEL, CYAN)

        # Subtle border around button
        tk.Frame(btn_frame, bg=CYAN, height=2).pack(fill="x")

        # Info text
        tk.Label(self,
                 text="Position your face clearly in front of the camera",
                 bg=BG, fg=GREY,
                 font=("Consolas", 8)).pack(pady=(18, 0))

        # Bottom decorative bar
        tk.Frame(self, bg=PURPLE, height=2).pack(side="bottom", fill="x")

    def _add_hover(self, widget, hover_fg, hover_bg, normal_bg, normal_fg):
        widget.bind("<Enter>", lambda e: widget.config(bg=hover_bg, fg=hover_fg))
        widget.bind("<Leave>", lambda e: widget.config(bg=normal_bg, fg=normal_fg))

    def _on_authenticate(self):
        self._auth_btn.config(state="disabled", text="  ◌  SCANNING...  ")
        self._status.config(text="OPENING CAMERA — LOOK STRAIGHT AHEAD", fg=YELLOW)
        self._ring.start()
        run_in_thread(self._do_auth)

    def _do_auth(self):
        try:
            from check_user import check_user
            result = check_user(True)
        except Exception as e:
            result = False
            print(f"Auth error: {e}")

        self.after(0, self._auth_done, result)

    def _auth_done(self, success):
        self._ring.stop()
        if success:
            self._status.config(text="✔  IDENTITY VERIFIED", fg=GREEN)
            self._auth_btn.config(text="  ✔  ACCESS GRANTED  ", bg=GREEN, fg=BG)
            self.after(900, self._launch_chat)
        else:
            self._status.config(text="✘  AUTHENTICATION FAILED — TRY AGAIN", fg=RED)
            self._auth_btn.config(state="normal",
                                  text="  ▶  AUTHENTICATE  ",
                                  bg=PANEL, fg=CYAN)

    def _launch_chat(self):
        self.destroy()
        app = ChatWindow()
        app.mainloop()


# ---------------------------------------------------------------------------
# CHAT WINDOW
# ---------------------------------------------------------------------------

class ChatWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Folter Assistant — Chat Interface")
        self.configure(bg=BG)
        self._center(860, 680)
        self.minsize(700, 500)
        self._speak_var  = tk.BooleanVar(value=True)
        self._mic_active = False
        self._session    = {}          # brain conversation state
        self._build()
        self._greet()

    def _center(self, w, h):
        self.update_idletasks()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x  = (sw - w) // 2
        y  = (sh - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def _build(self):
        # ── Top bar ──────────────────────────────────────────────────
        top = tk.Frame(self, bg=PANEL, height=52)
        top.pack(fill="x")
        top.pack_propagate(False)

        tk.Label(top, text="◈", bg=PANEL, fg=CYAN,
                 font=("Consolas", 16)).pack(side="left", padx=(16, 4), pady=12)
        tk.Label(top, text="FOLTER ASSISTANT", bg=PANEL, fg=CYAN,
                 font=("Consolas", 14, "bold")).pack(side="left", pady=12)
        tk.Label(top, text="v1.0  |  AI CHAT TERMINAL", bg=PANEL, fg=GREY,
                 font=("Consolas", 9)).pack(side="left", padx=12, pady=16)

        tk.Checkbutton(top, text="🔊 Voice", variable=self._speak_var,
                       bg=PANEL, fg=CYAN, selectcolor=BG2,
                       activebackground=PANEL, activeforeground=CYAN,
                       font=("Consolas", 9)).pack(side="right", padx=16)

        # Cyan accent line
        tk.Frame(self, bg=CYAN, height=2).pack(fill="x")

        # ── Chat display ──────────────────────────────────────────────
        chat_frame = tk.Frame(self, bg=BG2)
        chat_frame.pack(fill="both", expand=True, padx=12, pady=8)

        self._chat_box = tk.Text(
            chat_frame,
            bg=BG2, fg=WHITE,
            font=("Consolas", 11),
            relief="flat", bd=0,
            wrap="word",
            state="disabled",
            cursor="arrow",
            spacing1=4, spacing3=4,
            insertbackground=CYAN,
            selectbackground=BORDER,
        )
        scrollbar = tk.Scrollbar(chat_frame, command=self._chat_box.yview,
                                 bg=PANEL, troughcolor=BG2,
                                 activebackground=CYAN, bd=0,
                                 highlightthickness=0)
        self._chat_box.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self._chat_box.pack(side="left", fill="both", expand=True)

        self._chat_box.tag_configure("user",   foreground=GREEN,  font=("Consolas", 11, "bold"))
        self._chat_box.tag_configure("bot",    foreground=CYAN,   font=("Consolas", 11))
        self._chat_box.tag_configure("system", foreground=GREY,   font=("Consolas", 9, "italic"))
        self._chat_box.tag_configure("error",  foreground=RED,    font=("Consolas", 11))
        self._chat_box.tag_configure("label",  foreground=PURPLE, font=("Consolas", 10, "bold"))

        # ── Processing animation ──────────────────────────────────────
        self._processing = ProcessingDots(self)
        self._processing.pack(fill="x", padx=14)

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=12)

        # ── Input row ─────────────────────────────────────────────────
        input_frame = tk.Frame(self, bg=BG, pady=10)
        input_frame.pack(fill="x", padx=12, pady=(4, 10))

        tk.Label(input_frame, text="▶", bg=BG, fg=CYAN,
                 font=("Consolas", 12)).pack(side="left", padx=(0, 6))

        self._input = tk.Entry(
            input_frame,
            bg=BG2, fg=WHITE,
            insertbackground=CYAN,
            relief="flat", bd=0,
            font=("Consolas", 12),
        )
        self._input.pack(side="left", fill="x", expand=True, ipady=8)
        self._input.bind("<Return>", self._on_send)
        self._input.focus()

        # Mic button  (placed BEFORE the Send button)
        self._mic_btn = tk.Button(
            input_frame,
            text="🎤",
            bg=BG2, fg=CYAN,
            activebackground=PURPLE, activeforeground=WHITE,
            relief="flat", bd=0,
            font=("Consolas", 13),
            padx=10, pady=6,
            cursor="hand2",
            command=self._on_mic,
        )
        self._mic_btn.pack(side="left", padx=(10, 4))

        # Send button
        self._send_btn = tk.Button(
            input_frame,
            text="SEND ▶",
            bg=CYAN, fg=BG,
            activebackground=GREEN, activeforeground=BG,
            relief="flat", bd=0,
            font=("Consolas", 10, "bold"),
            padx=14, pady=8,
            cursor="hand2",
            command=self._on_send,
        )
        self._send_btn.pack(side="left", padx=(0, 0))

        # Bottom accent bar
        tk.Frame(self, bg=PURPLE, height=2).pack(side="bottom", fill="x")

    # ------------------------------------------------------------------
    # Chat helpers
    # ------------------------------------------------------------------

    def _append(self, text, tag="bot", prefix=""):
        self._chat_box.config(state="normal")
        if prefix:
            self._chat_box.insert("end", prefix, "label")
        self._chat_box.insert("end", text + "\n\n", tag)
        self._chat_box.config(state="disabled")
        self._chat_box.see("end")

    def _greet(self):
        self._append(
            "System initialised. Authentication successful.\n"
            "Type a query, or click 🎤 to speak.  Type 'help' for all commands.",
            tag="system",
        )
        self._append("Hello! How can I assist you today?", tag="bot", prefix="◈ Assistant:  ")
        if self._speak_var.get():
            run_in_thread(self._speak_text, "Hello! How can I assist you today?")

    # ------------------------------------------------------------------
    # Mic button
    # ------------------------------------------------------------------

    def _on_mic(self):
        if self._mic_active:
            return                          # already listening
        self._mic_active = True
        self._mic_btn.config(bg=PURPLE, fg=WHITE, text="🎙")
        self._append("Listening…", tag="system")
        run_in_thread(self._do_listen)

    def _do_listen(self):
        text = ""
        try:
            from Helpers.listern import listen
            text = listen() or ""
        except Exception as e:
            print(f"Listen error: {e}")
        self.after(0, self._mic_done, text)

    def _mic_done(self, text: str):
        self._mic_active = False
        self._mic_btn.config(bg=BG2, fg=CYAN, text="🎤")
        if text:
            self._input.delete(0, "end")
            self._input.insert(0, text)
            self._on_send()
        else:
            self._append("Could not hear anything. Please try again.", tag="error")

    # ------------------------------------------------------------------
    # Send → brain
    # ------------------------------------------------------------------

    def _on_send(self, event=None):
        query = self._input.get().strip()
        if not query:
            return
        self._input.delete(0, "end")
        self._lock_input()
        self._append(query, tag="user", prefix="▶ You:        ")
        self._processing.start()
        run_in_thread(self._process_and_reply, query)

    def _process_and_reply(self, query):
        from brain import Brain
        result = Brain.process(query, self._session)
        self.after(0, self._show_response, result)

    def _show_response(self, result):
        from brain import BrainResult
        self._processing.stop()
        self._unlock_input(result.input_hint if result.needs_input else "Type your query…")

        message = result.message

        # Special exit signal
        if message.startswith("GOODBYE|"):
            actual = message.split("|", 1)[1]
            self._append(actual, tag="bot", prefix="◈ Assistant:  ")
            if self._speak_var.get():
                run_in_thread(self._speak_text, actual)
            self.after(2500, self.destroy)
            return

        self._append(message, tag="bot", prefix="◈ Assistant:  ")
        if self._speak_var.get():
            run_in_thread(self._speak_text, message)

    # ------------------------------------------------------------------
    # Input lock helpers (disabled while brain is working)
    # ------------------------------------------------------------------

    def _lock_input(self):
        self._input.config(state="disabled")
        self._send_btn.config(state="disabled")
        self._mic_btn.config(state="disabled")

    def _unlock_input(self, placeholder="Type your query…"):
        self._input.config(state="normal")
        self._send_btn.config(state="normal")
        self._mic_btn.config(state="normal")
        # update placeholder hint via the entry text colour trick
        self._input.config(fg=GREY)
        self._input.delete(0, "end")
        self._input.insert(0, placeholder)
        self._input.bind("<FocusIn>",  self._clear_hint)
        self._input.bind("<FocusOut>", lambda e: None)
        self._input.focus()

    def _clear_hint(self, event=None):
        self._input.config(fg=WHITE)
        self._input.delete(0, "end")
        self._input.unbind("<FocusIn>")

    # ------------------------------------------------------------------
    # Speak
    # ------------------------------------------------------------------

    def _speak_text(self, text):
        try:
            from Helpers.speak import speak
            speak(text)
        except Exception as e:
            print(f"Speak error: {e}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def launch():
    app = AuthWindow()
    app.mainloop()


if __name__ == "__main__":
    launch()
