import tkinter as tk
import threading

from APIConnect import OpenAIChatBot
from GetMap import GetMap
from GuiSetUp import Gui


class DongeuiChatbotApp:
    def __init__(self, root):
        self.root = root
        self.bot_name = "동의"

        # AI / RAG 초기화
        self.ai = OpenAIChatBot()
        self.ai.InitRag()

        # 지도
        self.map = GetMap(root=root, image_base_path="")  # image_base_path를 필요에 따라 설정

        # GUI 초기화
        self.ui = Gui(root, bot_name=self.bot_name)
        self.ui.setup_gui(self.on_send_message)

    def on_send_message(self, text):

        # 빈 입력 무시
        if not text:
            return

        # 사용자 메시지 표시
        self.ui.add_message("나", text)

        # 지도와 간단한 봇 응답 요청
        name, path = self.map.find_building(text)
        if name:
            self.map.show_campus_map(name, path)
            self.ui.add_message(self.bot_name, f"'{name}' 위치를 보여드겠습니다")
            return

        threading.Thread(target=self._fetch_and_display_ai, args=(text,), daemon=True).start()

    # AI와 RAG를 가져옴
    def _fetch_and_display_ai(self, user_text):
        context = self.ai.get_rag_context(user_text)
        reply = self.ai.GetOpenAi(user_text, context=context)
        self.root.after(0, lambda: self.ui.add_message(self.bot_name, reply))


if __name__ == "__main__":
    root = tk.Tk()
    app = DongeuiChatbotApp(root)
    root.mainloop()