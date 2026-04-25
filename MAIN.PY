import streamlit as st
import json
import os
from datetime import datetime
import pandas as pd

# --- 模組一：JsonHandler (資料持久化) ---
class JsonHandler:
    def __init__(self, filename='history.json'):
        self.filename = filename
        if not os.path.exists(self.filename):
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump([], f)

    def load_data(self):
        with open(self.filename, 'r', encoding='utf-8') as f:
            return json.load(f)

    def save_record(self, name, score, soul_type):
        data = self.load_data()
        new_record = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S"),
            "name": name,
            "score": score,
            "type": soul_type,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        data.append(new_record)
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def delete_record(self, record_id):
        data = self.load_data()
        updated_data = [r for r in data if r['id'] != record_id]
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(updated_data, f, ensure_ascii=False, indent=4)

# --- 模組二：SoulManager (核心邏輯) ---
class SoulManager:
    def __init__(self):
        self.questions = [
            {"q": "你是否常覺得內心深處隱藏著一些連自己都尚未察覺的潛力？", "a": "是的", "b": "不"},
            {"q": "在社交場合中，你是否會根據對象的不同而調整表現方式？", "a": "是的", "b": "不"},
            {"q": "你是否曾感覺到，雖然表面自律，但內心偶爾會感到焦慮？", "a": "經常", "b": "很少"},
            {"q": "對於別人的讚美，你是否內心深處存有一點點懷疑？", "a": "會", "b": "不會"},
            {"q": "你是否傾向於對自己要求嚴苛，有時會過度批判自己？", "a": "是的", "b": "不"},
            {"q": "在做決定時，你是否希望得到他人認可但又想保有自主？", "a": "是的", "b": "不"},
            {"q": "你是否覺得有些夢想目前遙不可及，但仍不願放棄？", "a": "是的", "b": "不"},
            {"q": "你是否時而外向平易近人，時而內向沉默？", "a": "是的", "b": "不"},
            {"q": "你是否認為生活應該要有更多變化，而非一成不變？", "a": "是的", "b": "不"},
            {"q": "你是否曾覺得自己的某些想法太前衛，他人難以理解？", "a": "是的", "b": "不"},
            {"q": "處理問題時，你是否會同時考慮邏輯與直覺？", "a": "是的", "b": "不"},
            {"q": "你是否認為自己是一個獨立思考者，不輕信無據之談？", "a": "是的", "b": "不"}
        ]
        self.personalities = {
            "Glimmer": {"name": "流光編織者", "desc": "感知力強，善於在矛盾中尋找平衡。", "range": range(0, 4)},
            "Mirror": {"name": "幻鏡守門人", "desc": "內心強大且自律，是守護秘密的導師。", "range": range(4, 7)},
            "Stardust": {"name": "星塵觀測者", "desc": "格局超脫，在混亂中保持冷靜。", "range": range(7, 10)},
            "Abyssal": {"name": "深淵迴聲者", "desc": "情感深邃，蘊含改變世界的原始力量。", "range": range(10, 13)}
        }

    def analyze_result(self, score):
        for key, data in self.personalities.items():
            if score in data["range"]: return data
        return self.personalities["Stardust"]

# --- UI 樣式設定 ---
def inject_custom_css():
    st.markdown("""
    <style>
        .stApp { background: linear-gradient(135deg, #1a0a2e 0%, #020c2b 100%); color: #e0e0e0; }
        .main-title { text-align: center; color: #b388ff; text-shadow: 0 0 15px #7c4dff; }
        div.stButton > button { 
            width: 100%; border-radius: 25px; border: 1px solid #7c4dff; 
            background-color: rgba(124, 77, 255, 0.1); color: white; transition: 0.3s;
        }
        div.stButton > button:hover { background-color: rgba(124, 77, 255, 0.4); box-shadow: 0 0 20px #7c4dff; }
        .result-card { background: rgba(255,255,255,0.05); padding: 20px; border-radius: 15px; border: 1px solid #7c4dff; text-align: center; }
    </style>
    """, unsafe_allow_html=True)

# --- 主程式 ---
def main():
    st.set_page_config(page_title="靈魂透視系統", layout="wide")
    inject_custom_css()
    
    db = JsonHandler()
    if 'manager' not in st.session_state: st.session_state.manager = SoulManager()
    if 'step' not in st.session_state: st.session_state.step = -1
    if 'score' not in st.session_state: st.session_state.score = 0
    if 'user_name' not in st.session_state: st.session_state.user_name = ""

    # --- 側邊欄：管理員後台 (CRUD - Read, Search, Delete) ---
    with st.sidebar:
        st.title("🛠 管理員後台")
        admin_mode = st.checkbox("開啟管理模式")
        if admin_mode:
            st.write("---")
            all_records = db.load_data()
            if all_records:
                df = pd.DataFrame(all_records)
                
                # 搜尋功能
                search_query = st.text_input("🔍 搜尋姓名")
                if search_query:
                    df = df[df['name'].str.contains(search_query)]
                
                st.dataframe(df[['name', 'score', 'type', 'time']], use_container_width=True)
                
                # 刪除功能
                st.write("🗑 刪除紀錄")
                delete_id = st.selectbox("選擇要刪除的 ID", options=[r['id'] for r in all_records], format_func=lambda x: next(r['name'] for r in all_records if r['id'] == x))
                if st.button("確認刪除"):
                    db.delete_record(delete_id)
                    st.success("紀錄已刪除")
                    st.rerun()
            else:
                st.info("目前尚無測驗紀錄")

    # --- 主要介面 ---
    st.markdown("<h1 class='main-title'>🔮 靈魂透視系統</h1>", unsafe_allow_html=True)

    if st.session_state.step == -1:
        st.write("在進入儀式前，請告訴我們你的名字：")
        name = st.text_input("輸入名字", key="input_name")
        if st.button("開始啟程"):
            if name:
                st.session_state.user_name = name
                st.session_state.step = 0
                st.rerun()
            else: st.warning("請先輸入名字")

    elif 0 <= st.session_state.step < 12:
        q_idx = st.session_state.step
        q_data = st.session_state.manager.questions[q_idx]
        st.progress((q_idx + 1) / 12)
        st.write(f"### {q_data['q']}")
        if st.button(f"A) {q_data['a']}", key=f"a{q_idx}"):
            st.session_state.score += 1
            st.session_state.step += 1
            st.rerun()
        if st.button(f"B) {q_data['b']}", key=f"b{q_idx}"):
            st.session_state.step += 1
            st.rerun()

    else:
        result = st.session_state.manager.analyze_result(st.session_state.score)
        st.markdown(f"""<div class="result-card"><h2>{st.session_state.user_name} 的原型</h2><h1 style="color:#b388ff;">{result['name']}</h1><p>{result['desc']}</p></div>""", unsafe_allow_html=True)
        
        # 儲存到 JSON (只存一次)
        if 'saved' not in st.session_state:
            db.save_record(st.session_state.user_name, st.session_state.score, result['name'])
            st.session_state.saved = True
            st.toast("測驗結果已成功存入系統歷史檔案")

        if st.button("重新測試"):
            for key in ['step', 'score', 'user_name', 'saved']:
                if key in st.session_state: del st.session_state[key]
            st.rerun()

if __name__ == "__main__":
    main()