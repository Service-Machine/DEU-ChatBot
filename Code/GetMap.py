import os
import re
import difflib
import tkinter as tk
from tkinter import Toplevel, messagebox
from PIL import Image, ImageTk


# 정규화
def _normalize(text: str) -> str:
    if not text:
        return ""
    text = text.lower()
    text = re.sub(r"[^\w\sㄱ-ㅎㅏ-ㅣ가-힣]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def _strip_korean_particles(text: str) -> str:
    if not text:
        return text
    particles = ["에서", "에게", "으로", "로", "의", "에", "을", "를", "가", "이", "은", "는", "도", "와", "과"]
    for p in particles:
        if text.endswith(p) and len(text) > len(p):
            return text[:-len(p)]
    return text


class GetMap:
    def __init__(self, root=None, image_base_path=""):

        self.root = root
        # 이미지 경로의 기준 경로 (추후 위의 빈문자열을 수정하여 기준 경로를 설정)
        self.image_base_path = image_base_path


        self.building_db = {
            "캠퍼스 지도": "campus_map/CampusImg.jpg",
            "본관": "campus_map/1.jpg",
            "법정관": "campus_map/2.jpg",
            "상경관": "campus_map/3.jpg",
            "국제관": "campus_map/5.jpg",
            "동의스포츠센터": "campus_map/6.jpg",
            "상영관(제2학생회관)": "campus_map/7.jpg",
            "수덕전(학생회관)": "campus_map/8.jpg",
            "제1인문관": "campus_map/9.jpg",
            "제2인문관": "campus_map/10.jpg",
            "효민체육관": "campus_map/11.jpg",
            "중앙도서관": "campus_map/12.jpg",
            "성파글로벌관": "campus_map/13.jpg",
            "제2효민생활관": "campus_map/14.jpg",
            "의료보건과": "campus_map/15.jpg",
            "생활과학관": "campus_map/16.jpg",
            "음악관": "campus_map/17.jpg",
            "창의관": "campus_map/18.jpg",
            "지천관": "campus_map/19.jpg",
            "산학협력관": "campus_map/20.jpg",
            "건윤관": "campus_map/21.jpg",
            "공학관": "campus_map/22.jpg",
            "정보공학관": "campus_map/23.jpg",
            "제1효민생활관": "campus_map/24.jpg",
            "학생군사교육단": "campus_map/25.jpg",
            "행복기숙사(미래생활관)": "campus_map/26.jpg",
            "효민야구장": "campus_map/A.jpg",
            "효민축구장": "campus_map/B.jpg",
            "효민원(교육이념비)": "campus_map/C.jpg",
            "햇발터(혜안지)": "campus_map/D.jpg",
            "정심정": "campus_map/E.jpg",
            "야외음악당": "campus_map/F.jpg",
            "테니스장": "campus_map/G.jpg",
            "건학이념비": "campus_map/H.jpg",
            "정문": "campus_map/I.jpg",
            "지천주차장": "campus_map/J.jpg"
        }

        # 정규화된 이름 -> (원래이름, 전체경로)
        self._normalized_db = {}
        for name, rel in self.building_db.items():
            norm = _normalize(name)
            full_path = os.path.join(self.image_base_path, rel) if self.image_base_path else rel
            self._normalized_db[norm] = (name, full_path)

    def find_building(self, user_text: str):
        """
        사용자 입력에서 가장 적합한 건물을 찾아 (표시이름, 이미지경로)를 반환.
        못찾으면 (None, None).
        """
        if not user_text:
            return None, None

        user_norm = _normalize(user_text)
        # 디버그 출력 (필요시 활성화)
        # print(f"[GetMap] user_norm: '{user_norm}'")
        # print(f"[GetMap] db keys: {list(self._normalized_db.keys())}")

        # 1) DB 이름이 사용자 입력에 포함되는지 (강한 매칭)
        for norm_name, (orig_name, path) in self._normalized_db.items():
            if norm_name and norm_name in user_norm:
                # 이미지 경로 전체 조립
                if not os.path.isabs(path) and self.image_base_path:
                    full_path = os.path.join(self.image_base_path, path)
                else:
                    full_path = path
                if os.path.exists(full_path):
                    return orig_name, full_path
                print(f"[GetMap] 이미지 파일을 찾지 못함: {full_path}")
                return None, None

        # 사용자 입력의 단어 중 DB와 일치하는 것이 있는지 (조사 제거 포함)
        text = user_norm.split()

        for tok in text:
            text_stripped = _strip_korean_particles(tok)

            # 토큰이 정규화된 건물 이름의 일부라면 매칭
            for norm_name, (orig_name, path) in self._normalized_db.items():
                if text_stripped and text_stripped in norm_name:
                    full_path = os.path.join(self.image_base_path, path) if (self.image_base_path and not os.path.isabs(path)) else path
                    if os.path.exists(full_path):
                        return orig_name, full_path
                    return None, None

        # difflab으로 사용자 질문과 근접한 건물의 지도를 출력
        db_keys = list(self._normalized_db.keys())
        matches = difflib.get_close_matches(user_norm, db_keys, n=1, cutoff=0.6)
        if matches:
            best = matches[0]
            orig_name, path = self._normalized_db[best]
            full_path = os.path.join(self.image_base_path, path) if (self.image_base_path and not os.path.isabs(path)) else path
            if os.path.exists(full_path):
                return orig_name, full_path
            return None, None
        return None, None

    def show_campus_map(self, campus_name, campus_path):
        if campus_name is None or campus_path is None:
            return

        if not os.path.exists(campus_path):
            messagebox.showerror("이미지 없음", f"지도 이미지 파일을 찾을 수 없습니다: {campus_path}")
            return

        map_window = Toplevel(self.root)
        title_text = "동의대학교 캠퍼스 지도" if campus_name == "캠퍼스 지도" else f"{campus_name} 위치"
        map_window.title(title_text)
        map_window.geometry("1000x700")
        map_window.configure(bg="#f0f0f0")

        tk.Label(map_window, text=title_text, font=("맑은 고딕", 16, "bold"),
                 bg="#003366", fg="white", pady=10).pack(fill=tk.X)

        img = Image.open(campus_path)
        img = img.resize((900, 550), Image.Resampling.LANCZOS)
        img_tk = ImageTk.PhotoImage(img)

        img_label = tk.Label(map_window, image=img_tk)
        img_label.image = img_tk
        img_label.pack(pady=10)

        tk.Button(map_window, text="닫기", command=map_window.destroy,
                  font=("맑은 고딕", 11, "bold"), bg="#003366", fg="white",
                  padx=30, pady=5).pack(pady=8)
