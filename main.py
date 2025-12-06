# main.py
import tkinter as tk
import threading
import os
import sys

# OpenAIChatBot import (project의 Code/APIConnect.py 위치에 맞춤)
try:
    from Code.APIConnect import OpenAIChatBot
except Exception:
    project_root = os.path.dirname(os.path.abspath(__file__))
    code_dir = os.path.join(project_root, "Code")
    if code_dir not in sys.path:
        sys.path.insert(0, code_dir)
    from Code.APIConnect import OpenAIChatBot

from Code.GetMap import GetMap
from Code.GuiSetUp import Gui

# None대비, 질문을 소문자로 변환
def _simple_normalize(text: str) -> str:
    return (text or "").lower()

# 지도 관련 질문인지 판단
def is_map_request(user_text: str) -> bool:
    t = _simple_normalize(user_text)
    location_keywords = ["지도", "위치", "어디", "위치 알려", "가는법", "찾아", "찾아줘", "가는 길", "맵"]
    info_keywords = ["층", "호", "무엇", "뭐", "있어", "시설", "교실", "학과", "사무실"]
    has_location = any(k in t for k in location_keywords)
    has_info = any(k in t for k in info_keywords)
    if ("캠퍼스" in t and "맵" in t) or ("캠퍼스 맵" in t):
        return True
    if has_location and not has_info:
        return True
    if has_info:
        return False
    return False


class DongeuiChatbotApp:
    def __init__(self, root):
        self.root = root
        self.bot_name = "동의"

        # AI / RAG 초기화
        self.ai = OpenAIChatBot(base_path=os.path.dirname(os.path.abspath(__file__)))
        try:
            self.ai.init_rag()
        except Exception as e:
            print(f"[main] RAG 초기화 중 오류: {e}")

        project_root = os.path.dirname(os.path.abspath(__file__))
        image_base = project_root

        self.map = GetMap(root=self.root, image_base_path=image_base)

        # GUI 초기화
        self.ui = Gui(self.root, bot_name=self.bot_name)
        self.ui.setup_gui(self.on_send_message)

    def on_send_message(self, text):
        if not text:
            return

        # 사용자 메시지 표시
        self.ui.add_message("나", text)

        # 건물명 매칭
        name, path = self.map.find_building(text)

        # 명확히 지도를 요청하면 지도 반환
        if name and path and is_map_request(text):
            # UI 스레드에서 창을 띄우고 봇 응답 추가
            self.map.show_campus_map(name, path)
            self.ui.add_message(self.bot_name, f"'{name}' 위치를 보여드렸습니다.")
            return

        # 건물명이 있으면 건물명도 포함해서 검색
        rag_query = f"{name}: {text}" if name else text

        # Rag 우선으로 답변
        try:
            rag_context = self.ai.get_rag_context(rag_query)
        except Exception as e:
            print(f"[main] RAG 검색 오류: {e}")
            rag_context = None

        if rag_context and len(rag_context.strip()) > 10:
            threading.Thread(target=self._call_ai_and_display, args=(text, rag_context), daemon=True).start()
            return

        # RAG 결과가 없고 name/path가 있고 사용자가 '지도' 요구로 판단되지 않으면 AI에게 질문
        if name and path:
            # 건물명이 있지만 map 요청이 아니면 AI에게 질문
            query_text = f"{name} 관련: {text}"
            threading.Thread(target=self._call_ai_and_display, args=(query_text, None), daemon=True).start()
            return

        # 건물명도 없고 RAG도 없을 때 일반 AI에게 질의
        threading.Thread(target=self._call_ai_and_display, args=(text, None), daemon=True).start()

    # 백그라운드 스레드에서 AI 호출 후 UI 스레드로 전송
    def _call_ai_and_display(self, user_text, rag_context):
        reply = self.ai.get_openai_response(user_text, context=rag_context)
        self.root.after(0, lambda: self.ui.add_message(self.bot_name, reply))


if __name__ == "__main__":
    root = tk.Tk()
    app = DongeuiChatbotApp(root)
    root.mainloop()