import os
from openai import OpenAI
from dotenv import load_dotenv

# LangChain/RAG 관련 라이브러리
from langchain_text_splitters import CharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_community.document_loaders import TextLoader

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=API_KEY)

class OpenAIChatBot():
    def __init__(self):
        self.openai_client = openai_client
        self.vectorstore = None

    def GetOpenAi(self, user_prompt, context=None):
        if not self.openai_client:
            return "죄송합니다. AI 서비스 연결에 문제가 있습니다. API 키를 확인해 주세요."

        system_message = (
            "당신은 동의대학교 학생들을 돕는 친절한 AI 챗봇 '동의'입니다."
            "학교 관련 정보를 중심으로 간결하게 답변하세요."
        )

        if context:
            system_message += f"\n[CONTEXT]\n{context}\n[/CONTEXT]"

        # gpt에게 어떤 성격으로 어떻게 말해야하고 어떤 정보 위주로 답해야하는지 설정
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt}
        ]

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # 연동 문제로 4o-mini로 변경
                messages=messages,
                max_completion_tokens=300
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            return f"외부 AI 서비스 오류 (GPT-4o mini 호출 실패): {str(e)}"

    # Rag 생성
    def InitRag(self):
        knowledge_file = "deu_knowledge.txt"

        # 디버깅 용
        if not os.path.exists(knowledge_file):
            print(f"지식 파일 '{knowledge_file}' 없음, RAG 비활성화")
            return

        if not API_KEY:
            print("API키 없음, RAG 비활성화")
            return

        try:
            loader = TextLoader(knowledge_file, encoding='utf-8')
            documents = loader.load()
            text_splitter = CharacterTextSplitter(chunk_size=500, chunk_overlap=0)
            texts = text_splitter.split_documents(documents)

            embeddings = OpenAIEmbeddings(openai_api_key=API_KEY)
            self.vectorstore = Chroma.from_documents(texts, embeddings)

        except Exception as e:
            print(f"RAG 초기화 오류: {e}")   # 오류 발생시 디버깅
            self.vectorstore = None

    # Rag 설정
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

