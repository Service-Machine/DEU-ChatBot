import tkinter as tk
from tkinter import scrolledtext, Toplevel
from PIL import Image, ImageTk
import os
import openai
from dotenv import load_dotenv
import webbrowser

# LangChain/RAG 관련 라이브러리
from langchain_text_splitters import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import TextLoader


class DongeuiChatbotGUI:
    def __init__(self):
        self.bot_name = "동의"
        self.school_info = {
            "위치": "47340 부산광역시 부산진구 엄광로 176 (가야동)",
            "전화번호": "051-890-1114",
            "팩스": "FAX 051-890-1234",
            "홈페이지": "https://www.deu.ac.kr"
        }
        self.faq = {
            "도서관": "도서관 운영시간은 평일 09:00-22:00, 주말은 휴무입니다.",
            "학식": "학생식당은 양지관, 국제관, 상록원에 있으며 점심시간은 11:00-15:00입니다.",
            "셔틀버스": "서면, 연산, 해운대 방면 셔틀버스가 운행됩니다.",
            "수강신청": "수강신청은 매 학기 초 학사일정을 확인하세요."
        }

        # === AI/RAG 관련 초기화 ===
        self.openai_client = None
        self.vectorstore = None

        print("1. DongeuiChatbotGUI 초기화 시작")
        self.initialize_openai()
        self.initialize_rag()
        self.setup_gui()
        print("4. GUI 설정 완료, mainloop 대기 중")



    def initialize_openai(self):
        """OpenAI 클라이언트를 초기화합니다."""

        # 실제 발급받은 모델 API Key 입력
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        try:
            self.openai_client = openai.OpenAI(api_key=api_key)
            print("2. OpenAI 클라이언트 초기화 성공")
        except Exception as e:
            print(f"OpenAI 클라이언트 초기화 오류: {e}")
            self.openai_client = None


    def initialize_rag(self):
        """RAG를 위한 벡터 데이터베이스를 초기화하고 문서를 로드"""
        knowledge_file = "deu_knowledge.txt"
        if not os.path.exists(knowledge_file):
            print(f"⚠️ RAG 지식 파일 '{knowledge_file}'을 찾을 수 없습니다. RAG 기능 비활성화.")
            return

        if not openai.api_key or openai.api_key == "YOUR_OPENAI_API_KEY_HERE":
            print("⚠️ OpenAI API 키가 설정되지 않아 RAG 초기화를 건너뜁니다.")
            return

        try:
            # 문서 로드 및 분할
            loader = TextLoader(knowledge_file, encoding='utf-8')
            documents = loader.load()
            text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=0)
            texts = text_splitter.split_documents(documents)

            # 임베딩 및 벡터스토어 생성
            embeddings = OpenAIEmbeddings(openai_api_key=openai.api_key)
            self.vectorstore = Chroma.from_documents(texts, embeddings)
            print("3. RAG 벡터 데이터베이스 초기화 성공")

        except Exception as e:
            print(f"RAG 초기화 오류: {e}")
            self.vectorstore = None

    def get_rag_context(self, query):
        if not self.vectorstore:
            return None

        try:
            # 질문과 가장 유사한 2개의 문서 조각 검색
            docs = self.vectorstore.similarity_search(query, k=2)

            # 검색된 문서를 하나의 문자열로 결합
            context = "\n---\n".join([doc.page_content for doc in docs])
            return context
        except Exception as e:
            print(f"RAG 검색 중 오류 발생: {e}")
            return None

    # AI 연결
    def get_openai_response(self, user_prompt, context=None):

        if not self.openai_client:
            return "죄송합니다. AI 서비스 연결에 문제가 있습니다. API 키를 확인해 주세요."

        system_message = (
            "당신은 동의대학교 학생들을 돕는 친절한 AI 챗봇 '동의'입니다."
            "학교 관련 정보를 중심으로 간결하게 답변하세요."
        )

        if context:
            system_message += f"\n[CONTEXT]\n{context}\n[/CONTEXT]"


        messages = [
            {"role": "system", "content": system_message},      # gpt에게 어떤 성격으로 어떻게 말해야하고 어떤 정보 위주로 답해야하는지 설정
            {"role": "user", "content": user_prompt}            # 유저가 질문한 내용
        ]


        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",        # 연동 문제로 4o-mini로 변경
                messages=messages,
                max_completion_tokens=300
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            return f"외부 AI 서비스 오류 (GPT-4o mini 호출 실패): {str(e)}"


    def setup_gui(self):
        self.root = tk.Tk()
        self.root.title("동의대학교 챗봇 - 동의 (AI 통합)")
        self.root.geometry("600x700")
        self.root.configure(bg="#f0f0f0")

        top_frame = tk.Frame(self.root, bg="#003366", height=80)
        top_frame.pack(fill=tk.X)

        title_frame = tk.Frame(top_frame, bg="#003366")
        title_frame.pack(fill=tk.BOTH, expand=True, pady=20)

        tk.Label(title_frame, text="동의대학교 챗봇 - 동의", font=("맑은 고딕", 20, "bold"),
                 bg="#003366", fg="white").pack()
        tk.Label(title_frame, text="반갑습니다 20,000 효민인 여러분!! (AI 통합)", font=("맑은 고딕", 12),
                 bg="#003366", fg="#ffcc00").pack()

        chat_frame = tk.Frame(self.root, bg="#ffffff")
        chat_frame.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

        self.chat_display = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, width=60, height=25,
                                                      font=("맑은 고딕", 11), bg="#ffffff", state=tk.DISABLED)
        self.chat_display.pack(fill=tk.BOTH, expand=True)

        input_frame = tk.Frame(self.root, bg="#f0f0f0")
        input_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

        self.input_field = tk.Entry(input_frame, font=("맑은 고딕", 12))
        self.input_field.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=5)
        self.input_field.bind("<Return>", lambda e: self.send_message())

        tk.Button(input_frame, text="전송", command=self.send_message, font=("맑은 고딕", 11, "bold"),
                  bg="#003366", fg="white", padx=20).pack(side=tk.RIGHT, padx=(10, 0))

        self.add_message(self.bot_name, "반갑습니다 20,000 효민인 여러분!! 무엇을 도와드릴까요?")


    def find_image_file(self, base_name):
        """이미지 파일을 다양한 확장자로 찾기"""
        extensions = ['.jpg', '.jpeg', '.png', '.JPG', '.JPEG', '.PNG']
        for ext in extensions:
            file_path = base_name + ext
            if os.path.exists(file_path):
                return file_path
        return None


    def show_campus_map(self):
        try:
            map_window = Toplevel(self.root)
            map_window.title("동의대학교 캠퍼스 지도")
            map_window.geometry("1000x650")
            map_window.configure(bg="#f0f0f0")

            tk.Label(map_window, text="동의대학교 캠퍼스 맵", font=("맑은 고딕", 16, "bold"),
                     bg="#003366", fg="white", pady=10).pack(fill=tk.X)

            image_path = self.find_image_file("학교캠퍼스")
            if not image_path:
                self.add_message(self.bot_name, "죄송합니다. 캠퍼스 지도 이미지 파일을 찾을 수 없습니다.")
                map_window.destroy()
                return

            campus_image = Image.open(image_path)
            campus_image = campus_image.resize((950, 530), Image.Resampling.LANCZOS)
            campus_photo = ImageTk.PhotoImage(campus_image)

            image_frame = tk.Frame(map_window, bg="#ffffff", relief=tk.SOLID, borderwidth=2)
            image_frame.pack(padx=10, pady=10)

            image_label = tk.Label(image_frame, image=campus_photo, bg="#ffffff")
            image_label.image = campus_photo
            image_label.pack()

            tk.Button(map_window, text="닫기", command=map_window.destroy, font=("맑은 고딕", 11, "bold"),
                      bg="#003366", fg="white", padx=30, pady=5).pack(pady=10)
        except Exception as e:
            self.add_message(self.bot_name, f"캠퍼스 지도를 표시하는 중 오류가 발생했습니다: {str(e)}")
            if 'map_window' in locals():
                map_window.destroy()


    def show_bonggwan_direction(self):
        try:
            map_window = Toplevel(self.root)
            map_window.title("대학본관 가는 방법")
            map_window.geometry("1000x650")
            map_window.configure(bg="#f0f0f0")

            tk.Label(map_window, text="대학본관 가는 방법", font=("맑은 고딕", 16, "bold"),
                     bg="#003366", fg="white", pady=10).pack(fill=tk.X)

            image_path = self.find_image_file("1")
            if not image_path:
                self.add_message(self.bot_name, "죄송합니다. 대학본관 가는 방법 이미지 파일을 찾을 수 없습니다.")
                map_window.destroy()
                return

            campus_image = Image.open(image_path)
            campus_image = campus_image.resize((950, 530), Image.Resampling.LANCZOS)
            campus_photo = ImageTk.PhotoImage(campus_image)

            image_frame = tk.Frame(map_window, bg="#ffffff", relief=tk.SOLID, borderwidth=2)
            image_frame.pack(padx=10, pady=10)

            image_label = tk.Label(image_frame, image=campus_photo, bg="#ffffff")
            image_label.image = campus_photo
            image_label.pack()

            tk.Button(map_window, text="닫기", command=map_window.destroy, font=("맑은 고딕", 11, "bold"),
                      bg="#003366", fg="white", padx=30, pady=5).pack(pady=10)
        except Exception as e:
            self.add_message(self.bot_name, f"대학본관 가는 방법을 표시하는 중 오류가 발생했습니다: {str(e)}")
            if 'map_window' in locals():
                map_window.destroy()


    def show_Beopjeonggwan_direction(self):
        try:
            map_window = Toplevel(self.root)
            map_window.title("법정관 가는 방법")
            map_window.geometry("1000x650")
            map_window.configure(bg="#f0f0f0")

            tk.Label(map_window, text="법정관 가는 방법", font=("맑은 고딕", 16, "bold"),
                     bg="#003366", fg="white", pady=10).pack(fill=tk.X)

            image_path = self.find_image_file("2")
            if not image_path:
                self.add_message(self.bot_name, "죄송합니다. 법정관 가는 방법 이미지 파일을 찾을 수 없습니다.")
                map_window.destroy()
                return

            campus_image = Image.open(image_path)
            campus_image = campus_image.resize((950, 530), Image.Resampling.LANCZOS)
            campus_photo = ImageTk.PhotoImage(campus_image)

            image_frame = tk.Frame(map_window, bg="#ffffff", relief=tk.SOLID, borderwidth=2)
            image_frame.pack(padx=10, pady=10)

            image_label = tk.Label(image_frame, image=campus_photo, bg="#ffffff")
            image_label.image = campus_photo
            image_label.pack()

            tk.Button(map_window, text="닫기", command=map_window.destroy, font=("맑은 고딕", 11, "bold"),
                      bg="#003366", fg="white", padx=30, pady=5).pack(pady=10)
        except Exception as e:
            self.add_message(self.bot_name, f"법정관 가는 방법을 표시하는 중 오류가 발생했습니다: {str(e)}")
            if 'map_window' in locals():
                map_window.destroy()

    def show_Sanggyeonggwan_direction(self):
        try:
            map_window = Toplevel(self.root)
            map_window.title("상경관 가는 방법")
            map_window.geometry("1000x650")
            map_window.configure(bg="#f0f0f0")

            tk.Label(map_window, text="상경관 가는 방법", font=("맑은 고딕", 16, "bold"),
                     bg="#003366", fg="white", pady=10).pack(fill=tk.X)

            image_path = self.find_image_file("3")
            if not image_path:
                self.add_message(self.bot_name, "죄송합니다. 상경관 가는 방법 이미지 파일을 찾을 수 없습니다.")
                map_window.destroy()
                return

            campus_image = Image.open(image_path)
            campus_image = campus_image.resize((950, 530), Image.Resampling.LANCZOS)
            campus_photo = ImageTk.PhotoImage(campus_image)

            image_frame = tk.Frame(map_window, bg="#ffffff", relief=tk.SOLID, borderwidth=2)
            image_frame.pack(padx=10, pady=10)

            image_label = tk.Label(image_frame, image=campus_photo, bg="#ffffff")
            image_label.image = campus_photo
            image_label.pack()

            tk.Button(map_window, text="닫기", command=map_window.destroy, font=("맑은 고딕", 11, "bold"),
                      bg="#003366", fg="white", padx=30, pady=5).pack(pady=10)
        except Exception as e:
            self.add_message(self.bot_name, f"상경관 가는 방법을 표시하는 중 오류가 발생했습니다: {str(e)}")
            if 'map_window' in locals():
                map_window.destroy()


    def add_message(self, sender, message):
        self.chat_display.config(state=tk.NORMAL)
        if sender == self.bot_name:
            self.chat_display.insert(tk.END, f"{sender}: ", "bot")
            self.chat_display.tag_config("bot", foreground="#003366", font=("맑은 고딕", 11, "bold"))
        else:
            self.chat_display.insert(tk.END, f"{sender}: ", "user")
            self.chat_display.tag_config("user", foreground="#006600", font=("맑은 고딕", 11, "bold"))
        self.chat_display.insert(tk.END, f"{message}\n\n")
        self.chat_display.config(state=tk.DISABLED)
        self.chat_display.see(tk.END)

    def send_message(self):
        user_input = self.input_field.get().strip()
        if not user_input:
            return

        self.add_message("나", user_input)
        self.input_field.delete(0, tk.END)

        if user_input.lower() in ["종료", "exit", "quit", "bye", "끝"]:
            self.add_message(self.bot_name, "이용해 주셔서 감사합니다!")
            self.root.after(2000, self.root.destroy)
            print("5. mainloop 종료, 프로그램 종료")
            return

        response = self.get_response(user_input)
        self.add_message(self.bot_name, response)

    def get_response(self, user_input):
        user_input_lower = user_input.lower().strip()

        # 1. 특정 기능 및 정형화된 FAQ 키워드 매칭 (가장 높은 우선순위)
        if any(word in user_input_lower for word in ["안녕", "하이", "hello", "도와줘", "안녕하세요"]):
            return "반갑습니다 20,000 효민인 여러분!! 무엇을 도와드릴까요? (예: 본관 위치, 수강신청 기간)"

        if any(word in user_input_lower for word in ["양정캠퍼스", "한의학관", "간호학관", "동의의료원", "부속한방병원", "4번", "4"]):
            return "죄송합니다. 챗봇 '동의'는 가야동 **승학캠퍼스** 위주로 정보를 제공합니다."

        if any(great in user_input_lower for great in ["짱이다", "고마워", "good", "thankyou"]):
            return "감사합니다!! 도움이 될 수 있어서 다행이에요~ 효민인 여러분께 봉사할 수 있어 기쁩니다!"

        # 길 찾기 기능 실행 (이미지 Toplevel 창)
        if any(word in user_input_lower for word in ["본관", "대학본관", "1", "1번"]):
            self.show_bonggwan_direction()
            return "대학본관 가는 방법입니다!!"

        if any(word in user_input_lower for word in ["법정관", "법정", "2", "2번"]):
            self.show_Beopjeonggwan_direction()
            return "법정관 가는 방법입니다!!"

        if any(word in user_input_lower for word in ["상경관", "상경", "3", "3번"]):
            self.show_Sanggyeonggwan_direction()
            return "상경관 가는 방법입니다!!"

        if any(word in user_input_lower for word in ["지도", "캠퍼스", "맵", "map", "campus", "건물", "위치도", "학교위치", "학교지도"]):
            self.show_campus_map()
            return "동의대학교 캠퍼스 지도 입니다!!"

        if "주소" in user_input_lower or "위치" in user_input_lower:
            return f"동의대 위치: {self.school_info['위치']}"

        if "전화" in user_input_lower or "연락처" in user_input_lower:
            return f"대표 전화번호: {self.school_info['전화번호']}"

        if "홈페이지" in user_input_lower or "웹사이트" in user_input_lower:
            return f"홈페이지: {self.school_info['홈페이지']}"

        # 기존 FAQ 처리
        for keyword, answer in self.faq.items():
            if keyword in user_input_lower:
                return answer

        # 2. RAG 검색 및 GPT 답변 생성 (두 번째 우선순위: 상세 정보)
        context = self.get_rag_context(user_input)
        if context:
            # RAG Context와 함께 GPT 모델 호출
            return self.get_openai_response(user_input, context=context)

        # 3. 일반 GPT 답변 생성 (세 번째 우선순위: 일반적인 질문)
        return self.get_openai_response(user_input)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    chatbot = DongeuiChatbotGUI()
    chatbot.run()