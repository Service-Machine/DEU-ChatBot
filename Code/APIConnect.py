import os
import traceback
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
openai_client = OpenAI(api_key=API_KEY)


# 새 버전의 OpenAi 우선으로 API를 불러옴
_new_openai_client = None
_legacy_openai = None
try:
    from openai import OpenAI as _OpenAIClient

    _new_openai_client = _OpenAIClient
except Exception:
    try:
        import openai as _openai_legacy  # type: ignore

        _legacy_openai = _openai_legacy
    except Exception:
        _new_openai_client = None
        _legacy_openai = None

# LangChain 위한 RAG 모듈 로드
try:
    from langchain_text_splitters import CharacterTextSplitter
    from langchain_openai import OpenAIEmbeddings
    from langchain_community.vectorstores import Chroma
    from langchain_community.document_loaders import TextLoader

    _RAG_AVAILABLE = True

# 라이브러리 없으면 RAG 비활성화
except Exception:
    CharacterTextSplitter = None
    OpenAIEmbeddings = None
    Chroma = None
    TextLoader = None
    _RAG_AVAILABLE = False


class OpenAIChatBot:
    def __init__(
        self,
        api_key: Optional[str] = None,
        knowledge_file: str = "deu_knowledge.txt",
        base_path: Optional[str] = None,
    ):
        # API 키 설정
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.knowledge_file = knowledge_file
        self.base_path = os.path.abspath(base_path) if base_path else os.getcwd()

        # 클라이언트 선택 저장
        self.client = None
        self._using_new_client = False
        self._using_legacy = False

        # RAG
        self.vectorstore = None

        # 클라이언트 초기화
        self._init_client()

    # OpenAI API 클라이언트 설정
    def _init_client(self):
        if not self.api_key:
            print("[APIConnect] API키가 없습니다.")
            return

        # 신규 클라이언트 우선 시도
        if _new_openai_client is not None:
            try:
                self.client = _new_openai_client(api_key=self.api_key)
                self._using_new_client = True
                return
            except Exception as e:
                print(f"[APIConnect] 새로운 클라이언트를 불러오는데에 실패했습니다: {e}")
                traceback.print_exc()

        # 레거시 클라이언트 시도
        if _legacy_openai is not None:
            try:
                _legacy_openai.api_key = self.api_key
                self.client = _legacy_openai
                self._using_legacy = True
                return
            except Exception as e:
                print(f"[APIConnect] 레거시 클라이언트를 생성하는데에 실패했습니다: {e}")
                traceback.print_exc()

    # 기본 OpenAI 챗 호출
    def get_openai_response(self, user_prompt: str, context: Optional[str] = None, model: str = "gpt-4o-mini", max_tokens: int = 300) -> str:
        if not user_prompt:
            return "질문을 해주세요."

        if not self.client:
            return "AI 서비스 연결에 문제가 있습니다. API 키나 네트워크를 확인해 주세요."

        # 시스템 메시지 구성
        system_message = (
            "당신은 동의대학교 학생들을 돕는 친절한 AI 챗봇 '동의'입니다. "
            "학교 관련 정보를 중심으로 간결하게 답변하세요."
        )
        if context:
            system_message += f"\n[CONTEXT]\n{context}\n[/CONTEXT]"

        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_prompt},
        ]

        try:
            if self._using_new_client:
                # 신규 SDK 방식
                resp = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_completion_tokens=max_tokens,
                )
                return getattr(resp.choices[0].message, "content", str(resp)).strip()
            elif self._using_legacy:
                # 레거시 방식
                resp = self.client.ChatCompletion.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                )
                return resp.choices[0].message["content"].strip()
            else:
                return "AI 클라이언트가 초기화되어 있지 않습니다."
        except Exception as e:
            print(f"[APIConnect] get_openai_response error: {e}")
            traceback.print_exc()
            return f"외부 AI 서비스 오류: {e}"

    # Rag 초기화
    def init_rag(self, knowledge_file: Optional[str] = None, chunk_size: int = 500, chunk_overlap: int = 50):
        kf = knowledge_file or self.knowledge_file
        kf_path = kf if os.path.isabs(kf) else os.path.join(self.base_path, kf)
        kf_path = os.path.normpath(kf_path)

        if not os.path.exists(kf_path):
            self.vectorstore = None
            return

        if not self.api_key:
            self.vectorstore = None
            return

        try:
            loader = TextLoader(kf_path, encoding="utf-8")
            documents = loader.load()

            # 문서 분할
            text_splitter = CharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
            chunks = text_splitter.split_documents(documents)

            # 임베딩 생성 후 벡터스토어 구축
            embeddings = OpenAIEmbeddings(openai_api_key=self.api_key)
            self.vectorstore = Chroma.from_documents(chunks, embeddings)
        except Exception as e:
            print(f"[APIConnect] init_rag failed: {e}")
            traceback.print_exc()
            self.vectorstore = None


    # query에 가장 유사한 문서 k개를 검색해 문맥으로 결합하여 반환.
    def get_rag_context(self, query: str, k: int = 4, min_length_chars: int = 12) -> Optional[str]:
        if not self.vectorstore:
            # RAG 비활성화
            return None

        if not query:
            return None

        try:
            # 스코어 포함 검색
            try:
                docs_and_scores = self.vectorstore.similarity_search_with_score(query, k=k)
                print(f"Rag 정확도 : {docs_and_scores}")
            except Exception:
                docs = self.vectorstore.similarity_search(query, k=k)
                docs_and_scores = [(d, None) for d in docs]

            if not docs_and_scores:
                return None

            combined = []
            for idx, (doc, score) in enumerate(docs_and_scores):
                content = getattr(doc, "page_content", str(doc))
                combined.append(content)

            context = "\n---\n".join(combined).strip()

            # 너무 짧으면 RAG 결과로 사용하지 않음
            if len(context) < min_length_chars:
                return None
            return context
        except Exception as e:
            print(f"[APIConnect] get_rag_context 에러: {e}")
            traceback.print_exc()
            return None
