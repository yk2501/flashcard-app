import streamlit as st
import sqlite3
from datetime import datetime, timedelta

REVIEW_INTERVALS = {
    0: 20,     # 20分後
    1: 60,      # 1時間後
    2: 1440,    # 1日後
    3: 8640,    # 6日後
    4: 43200    # 1ヶ月後
}

def init_db():
    conn = sqlite3.connect('flashcards.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT,
            answer TEXT,
            created_at DATETIME,
            next_review DATETIME,
            stage INTEGER DEFAULT 0,
            correct_count INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    return conn

def get_due_cards(conn):
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c = conn.cursor()
    c.execute('SELECT * FROM cards WHERE next_review <= ? ORDER BY next_review', (now,))
    return c.fetchall()

def update_card(conn, card_id, is_correct):
    c = conn.cursor()
    c.execute('SELECT stage, correct_count FROM cards WHERE id = ?', (card_id,))
    stage, correct_count = c.fetchone()

    if is_correct:
        new_stage = min(stage + 1, 4)
        new_count = correct_count + 1
    else:
        new_stage = max(stage - 1, 0)
        new_count = max(correct_count - 1, 0)

    interval = REVIEW_INTERVALS[new_stage]
    next_review = datetime.now() + timedelta(minutes=interval)

    c.execute('''
        UPDATE cards 
        SET stage = ?, 
            correct_count = ?,
            next_review = ?
        WHERE id = ?
    ''', (new_stage, new_count, next_review, card_id))
    conn.commit()

# アプリ本体
def main():
    st.title("📚 忘却曲線対応 復習管理アプリ")
    conn = init_db()

    # 新規カード追加
    with st.expander("新しいカードを追加"):
        question = st.text_input("問題文")
        answer = st.text_input("解答")
        if st.button("追加"):
            conn.execute('INSERT INTO cards (question, answer, created_at, next_review) VALUES (?,?,?,?)',
                        (question, answer, datetime.now(), datetime.now()))
            st.success("カードを追加しました！")

    # 復習セクション
    due_cards = get_due_cards(conn)
    if due_cards:
        st.subheader(f"復習が必要なカード: {len(due_cards)}枚")
        
        for card in due_cards:
            with st.container(border=True):
                st.markdown(f"#### {card[1]}")
                if st.button("解答を表示", key=f"show_{card[0]}"):
                    st.markdown(f"**解答**: {card[2]}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("⭕ 正解", key=f"correct_{card[0]}"):
                            update_card(conn, card[0], True)
                            st.rerun()
                    with col2:
                        if st.button("❌ 不正解", key=f"wrong_{card[0]}"):
                            update_card(conn, card[0], False)
                            st.rerun()
    else:
        st.success("🎉 現在復習が必要なカードはありません")

if __name__ == "__main__":
    main()
