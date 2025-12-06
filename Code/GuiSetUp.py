import tkinter as tk
from tkinter import scrolledtext


class Gui:
    def __init__(self, root, bot_name="동의"):
        self.root = root
        self.bot_name = bot_name
        self.chat_display = None
        self.input_field = None
        self.send_button = None

    def setup_gui(self, send_callback):
        self.root.title("동의대학교 챗봇 - 동의 (AI 통합)")
        self.root.geometry("600x700")
        self.root.configure(bg="#f0f0f0")

        top_frame = tk.Frame(self.root, bg="#003366", height=80)
        top_frame.pack(fill=tk.X)

        title_frame = tk.Frame(top_frame, bg="#003366")
        title_frame.pack(fill=tk.BOTH, expand=True, pady=20)

        tk.Label(title_frame, text="동의대학교 챗봇 - 동의",
                 font=("맑은 고딕", 20, "bold"),
                 bg="#003366", fg="white").pack()

        tk.Label(title_frame, text="반갑습니다 20,000 효민인 여러분!! (AI 통합)",
                 font=("맑은 고딕", 12),
                 bg="#003366", fg="#ffcc00").pack()

        chat_frame = tk.Frame(self.root, bg="#ffffff")
        chat_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

        self.chat_display = scrolledtext.ScrolledText(
            chat_frame, wrap=tk.WORD, width=60, height=25,
            font=("맑은 고딕", 11), bg="#ffffff", state=tk.DISABLED
        )

        self.chat_display.pack(fill=tk.BOTH, expand=True)

        input_frame = tk.Frame(self.root, bg="#f0f0f0")
        input_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        self.input_field = tk.Entry(input_frame, font=("맑은 고딕", 12))
        self.input_field.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)

        self.input_field.bind("<Return>", lambda e: send_callback(self.input_field.get().strip()))

        self.send_button = tk.Button(input_frame, text="전송",
                                     command=lambda: send_callback(self.input_field.get().strip()),
                                     font=("맑은 고딕", 11, "bold"), bg="#003366", fg="white", padx=20)
        self.send_button.pack(side=tk.RIGHT, padx=(10, 0))

        # 초기 봇 메시지
        self.add_message(self.bot_name, "반갑습니다 20,000 효민인 여러분!! 무엇을 도와드릴까요?")

    def add_message(self, sender, message):
        self.chat_display.config(state=tk.NORMAL)

        tag = "bot" if sender == self.bot_name else "user"
        if tag == "bot":
            self.chat_display.insert(tk.END, f"{sender}: ", "bot")
            self.chat_display.tag_config("bot", foreground="#003366", font=("맑은 고딕", 11, "bold"))
        else:
            self.chat_display.insert(tk.END, f"{sender}: ", "user")
            self.chat_display.tag_config("user", foreground="#006600", font=("맑은 고딕", 11, "bold"))

        self.chat_display.insert(tk.END, f"{message}\n\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

        if tag == "user":
            self.input_field.delete(0, tk.END)