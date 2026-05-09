import streamlit as st
import random
import json
import os
from datetime import datetime

# ================= 配置与初始化 =================
st.set_page_config(page_title="王者轮回羽毛球赛", page_icon="🏸", layout="centered")

PEAK_FILE = "peak_standings.json"
AVATAR_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "avatars")

if not os.path.exists(AVATAR_DIR):
    os.makedirs(AVATAR_DIR)

# ================= CSS 样式库 =================
def inject_global_css():
    st.markdown("""
    <style>
        #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
        .score-board {
            background: linear-gradient(145deg, #1e1e1e, #2b2b2b); color: #ffffff;
            border-radius: 20px; padding: 20px 10px; text-align: center;
            font-size: 110px; font-weight: 900; font-family: 'Arial Black', sans-serif;
            box-shadow: 5px 5px 15px rgba(0,0,0,0.3); margin-bottom: 15px; line-height: 1.1;
        }
        .p1-board { border-bottom: 8px solid #007BFF; color: #E6F2FF;}
        .p2-board { border-bottom: 8px solid #FF4136; color: #FFEBE9;}
        .player-name { font-size: 24px; font-weight: bold; text-align: center; margin-bottom: 10px; color: #333;}
        
        .profile-header { text-align: center; margin-top: 20px; margin-bottom: 30px; }
        .profile-avatar-img {
            width: 150px; height: 150px; border-radius: 50%; object-fit: cover;
            border: 4px solid #fff; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .profile-name { font-size: 32px; font-weight: bold; margin-top: 10px; color: #222;}
        .profile-pinyin { font-size: 16px; color: #888; font-family: sans-serif; letter-spacing: 1px;}
        
        .stat-card {
            background: #fff; border-radius: 15px; padding: 15px 5px; text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05); border: 1px solid #f0f0f0; height: 110px;
            display: flex; flex-direction: column; justify-content: center; align-items: center;
        }
        .stat-val { font-size: 26px; font-weight: 900; margin-bottom: 5px; line-height: 1;}
        .stat-label { font-size: 12px; color: #666; font-weight: bold;}
        .val-winrate { color: #28a745; } .val-ability { color: #007BFF; } 
        .val-champ { color: #FFC107; } .val-rank { color: #FF5722; }
    </style>
    """, unsafe_allow_html=True)

def inject_landscape_prompt():
    st.markdown("""
    <style>
        @media screen and (max-width: 800px) and (orientation: portrait) {
            body::before {
                content: "🔄 比赛计分中，请旋转手机至横屏";
                position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
                background: rgba(0,0,0,0.95); color: white; z-index: 10000;
                display: flex; align-items: center; justify-content: center;
                font-size: 24px; font-weight: bold; text-align: center; padding: 20px;
            }
        }
    </style>
    """, unsafe_allow_html=True)

# ================= 核心数据结构与逻辑 =================
def load_global_standings():
    if os.path.exists(PEAK_FILE):
        with open(PEAK_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            upgraded = False
            for k, v in data.items():
                if isinstance(v, int):
                    data[k] = {"points": v, "played": v, "won": v, "champs": 0}
                    upgraded = True
            if upgraded:
                save_global_standings(data)
            return data
    return {}

def save_global_standings(data):
    with open(PEAK_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def ensure_player_exists(data, player_name):
    if player_name not in data:
        data[player_name] = {"points": 0, "played": 0, "won": 0, "champs": 0}

def record_match(winner, loser):
    data = load_global_standings()
    ensure_player_exists(data, winner)
    ensure_player_exists(data, loser)
    data[winner]["points"] += 1
    data[winner]["played"] += 1
    data[winner]["won"] += 1
    data[loser]["played"] += 1
    save_global_standings(data)

def record_championship(player_name):
    data = load_global_standings()
    ensure_player_exists(data, player_name)
    data[player_name]["points"] += 3
    data[player_name]["champs"] += 1
    save_global_standings(data)

def check_game_winner_standard(s1, s2):
    if s1 >= 21 or s2 >= 21:
        if abs(s1 - s2) >= 2 or s1 == 30 or s2 == 30: return 1 if s1 > s2 else 2
    return 0

def reset_match_state():
    st.session_state.game_scores = [0, 0]
    st.session_state.match_history = []
    st.session_state.p1_wins = 0
    st.session_state.p2_wins = 0

# --- 状态初始化 ---
if 'stage' not in st.session_state:
    st.session_state.stage = 'splash' 
    st.session_state.players = []
    st.session_state.matches = []
    st.session_state.current_match_idx = 0
    st.session_state.local_standings = {} 
    reset_match_state()
    st.session_state.tb_config = {} 
    st.session_state.viewing_player = None

inject_global_css()

# ================= 阶段 0：开屏海报 (智能侦测版) =================
if st.session_state.stage == 'splash':
    # 智能寻找各种格式的海报图片
    poster_found = None
    for ext in ['jpg', 'png', 'jpeg', 'JPG', 'PNG', 'JPEG']:
        if os.path.exists(f"poster.{ext}"):
            poster_found = f"poster.{ext}"
            break
            
    if poster_found:
        # 找到了图片，完美铺满展示
        st.image(poster_found, use_container_width=True)
    else:
        # 没找到图片，显示好看的占位提示，不会报错
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center; font-size: 60px;'>🏸</h1>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align: center; color: #333;'>王者轮回<br>巅峰周赛</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>如果想显示您的专属海报，<br>请将图片命名为 <b>poster.jpg</b> 或 <b>poster.png</b><br>并放在代码同级目录下。</p>", unsafe_allow_html=True)
        st.markdown("<br><br>", unsafe_allow_html=True)

    # 底部进入按钮
    st.markdown("<div style='margin-top: 20px; padding: 10px;'>", unsafe_allow_html=True)
    if st.button("🚀 点击进入巅峰赛场", type="primary", use_container_width=True):
        st.session_state.stage = 'register'
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

# ================= 选手个人主页 =================
elif st.session_state.stage == 'profile':
    player_name = st.session_state.viewing_player
    data = load_global_standings()
    
    sorted_players = sorted(data.items(), key=lambda x: x[1]['points'], reverse=True)
    rank = "-"
    for idx, (name, info) in enumerate(sorted_players):
        if name == player_name:
            rank = str(idx + 1)
            break
            
    p_data = data.get(player_name, {"points": 0, "played": 0, "won": 0, "champs": 0})
    win_rate = "0.0%"
    if p_data["played"] > 0: win_rate = f"{(p_data['won'] / p_data['played']) * 100:.1f}%"

    avatar_found = False
    for ext in ['jpg', 'png', 'jpeg', 'JPG', 'PNG']:
        path = os.path.join(AVATAR_DIR, f"{player_name}.{ext}")
        if os.path.exists(path):
            st.markdown("<div class='profile-header'>", unsafe_allow_html=True)
            cols = st.columns([1,2,1])
            with cols[1]:
                st.image(path, use_container_width=True, output_format="auto")
            avatar_found = True
            break
            
    if not avatar_found:
        st.markdown("<div class='profile-header'>", unsafe_allow_html=True)
        st.markdown("<div style='font-size:80px; width:150px; height:150px; background:#e0e0e0; border-radius:50%; margin: 0 auto; display:flex; align-items:center; justify-content:center; color:#fff;'>👤</div>", unsafe_allow_html=True)

    st.markdown(f"<div class='profile-name'>{player_name}</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='profile-pinyin'>PLAYER PROFILE</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f"<div class='stat-card'><div class='stat-val val-winrate'>🎯<br>{win_rate}</div><div class='stat-label'>总胜率</div></div>", unsafe_allow_html=True)
    with c2: st.markdown(f"<div class='stat-card'><div class='stat-val val-ability'>⚡<br>{p_data['points']}</div><div class='stat-label'>能力值(分)</div></div>", unsafe_allow_html=True)
    with c3: st.markdown(f"<div class='stat-card'><div class='stat-val val-champ'>🏆<br>{p_data['champs']}</div><div class='stat-label'>周赛冠军</div></div>", unsafe_allow_html=True)
    with c4: st.markdown(f"<div class='stat-card'><div class='stat-val val-rank'>🔥<br>No.{rank}</div><div class='stat-label'>全服排名</div></div>", unsafe_allow_html=True)
    
    st.write("---")
    if st.button("⬅️ 返回大厅", use_container_width=True):
        st.session_state.stage = 'register' 
        st.rerun()

# ================= 正式系统界面 =================
else:
    if st.session_state.stage in ['playing', 'tb_playing']:
        inject_landscape_prompt()

    if st.session_state.stage not in ['playing', 'tb_playing']:
        st.markdown("<h2 style='text-align: center; margin-bottom: 0;'>🏸 轮回羽毛球赛</h2>", unsafe_allow_html=True)
    
    if st.session_state.stage in ['playing', 'tb_playing']:
        tab_main = st.container()
        tab_leaderboard = None
    else:
        tab_main, tab_leaderboard = st.tabs(["🎮 比赛大厅", "🔥 巅峰榜单"])

        with tab_leaderboard:
            data = load_global_standings()
            if data:
                sorted_ranks = sorted(data.items(), key=lambda x: x[1]['points'], reverse=True)
                st.markdown("<h3 style='text-align:center; color:#FF4136; margin-bottom:20px;'>👑 王者巅峰榜</h3>", unsafe_allow_html=True)
                
                for rank, (name, info) in enumerate(sorted_ranks):
                    medal = "🥇" if rank==0 else "🥈" if rank==1 else "🥉" if rank==2 else f"<span style='color:#aaa;font-size:16px;'>{rank+1}</span>"
                    colA, colB = st.columns([3, 1])
                    with colA:
                        st.markdown(f"<div style='font-size:20px; padding:10px 0;'><b>{medal} {name}</b> (积分: {info['points']})</div>", unsafe_allow_html=True)
                    with colB:
                        if st.button("查看主页", key=f"btn_{name}", use_container_width=True):
                            st.session_state.viewing_player = name
                            st.session_state.stage = 'profile'
                            st.rerun()
                    st.markdown("<hr style='margin:5px 0;'>", unsafe_allow_html=True)
            else:
                st.info("暂无数据，赢得第一场比赛即可上榜！")

            # --- 清空巅峰榜单 ---
            st.markdown("<br>", unsafe_allow_html=True)
            with st.expander("⚠️ 危险操作区"):
                st.warning("清空后所有历史积分、胜率、冠军记录将**永久删除**，无法恢复！")
                if 'confirm_clear_peak' not in st.session_state:
                    st.session_state.confirm_clear_peak = False

                if not st.session_state.confirm_clear_peak:
                    if st.button("🗑️ 清空巅峰榜单", use_container_width=True):
                        st.session_state.confirm_clear_peak = True
                        st.rerun()
                else:
                    st.error("⚠️ 确定要清空所有榜单数据吗？此操作不可撤销！")
                    col_yes, col_no = st.columns(2)
                    with col_yes:
                        if st.button("✅ 确认清空", type="primary", use_container_width=True):
                            save_global_standings({})
                            st.session_state.confirm_clear_peak = False
                            st.success("✅ 巅峰榜单已清空！")
                            st.rerun()
                    with col_no:
                        if st.button("❌ 取消", use_container_width=True):
                            st.session_state.confirm_clear_peak = False
                            st.rerun()

    # ================= 主赛场流程 =================
    with tab_main:
        # --- 1. 报名 ---
        if st.session_state.stage == 'register':
            with st.container(border=True):
                st.markdown("### 📝 参赛名单")
                p1 = st.text_input("👤 选手 1", placeholder="输入姓名")
                p2 = st.text_input("👤 选手 2", placeholder="输入姓名")
                p3 = st.text_input("👤 选手 3", placeholder="输入姓名")
                
                if st.button("🎲 抽签并生成对战表", type="primary", use_container_width=True):
                    if p1 and p2 and p3:
                        players = [p1, p2, p3]
                        random.shuffle(players)
                        st.session_state.players = players
                        st.session_state.local_standings = {p: 0 for p in players}
                        st.session_state.matches = [
                            {"p1": players[0], "p2": players[1], "desc": "第1场：揭幕战"},
                            {"p1": players[2], "p2": "第1场负者", "desc": "第2场：败者战轮空"},
                            {"p1": players[2], "p2": "第1场胜者", "desc": "第3场：王者之战"}
                        ]
                        st.session_state.stage = 'confirm_draw'
                        st.rerun()
                    else:
                        st.error("⚠️ 请填写三名选手的姓名")

        # --- 2. 确认抽签 ---
        elif st.session_state.stage == 'confirm_draw':
            st.success(f"🎉 **{st.session_state.players[2]}** 获得首轮轮空！")
            with st.container(border=True):
                for match in st.session_state.matches:
                    st.markdown(f"**{match['desc']}**: {match['p1']} VS {match['p2']}")
            if st.button("🚀 开始比赛 (请横屏手机)", type="primary", use_container_width=True):
                reset_match_state()
                st.session_state.stage = 'playing'
                st.rerun()

        # --- 3. 正赛计分板 ---
        elif st.session_state.stage == 'playing':
            match_idx = st.session_state.current_match_idx
            match_info = st.session_state.matches[match_idx]
            
            p1_name = match_info['p1']
            p2_name = match_info['p2']
            if p2_name == "第1场负者": p2_name = st.session_state.matches[0]['loser']
            elif p2_name == "第1场胜者": p2_name = st.session_state.matches[0]['winner']

            st.markdown(f"<div style='text-align:center; color:gray; font-size:14px;'>正赛 - 21分制(3局2胜) | {match_info['desc']}</div>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='text-align: center; margin-top:5px;'><span style='color:#007BFF;'>🔵 {st.session_state.p1_wins}</span> : <span style='color:#FF4136;'>{st.session_state.p2_wins} 🔴</span></h3>", unsafe_allow_html=True)

            if st.session_state.p1_wins == 2 or st.session_state.p2_wins == 2:
                match_winner = p1_name if st.session_state.p1_wins == 2 else p2_name
                match_loser = p2_name if st.session_state.p1_wins == 2 else p1_name
                
                st.success(f"🎉 {match_winner} 获胜！(胜率/积分已更新)")
                if st.button("➡️ 确认并进入下一步", type="primary", use_container_width=True):
                    record_match(match_winner, match_loser)
                    st.session_state.matches[match_idx]['winner'] = match_winner
                    st.session_state.matches[match_idx]['loser'] = match_loser
                    st.session_state.local_standings[match_winner] += 1 
                    
                    if match_idx < 2:
                        st.session_state.current_match_idx += 1
                        reset_match_state()
                    else:
                        st.session_state.stage = 'finished'
                    st.rerun()
            else:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"<div class='player-name'>🔵 {p1_name}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='score-board p1-board'>{st.session_state.game_scores[0]}</div>", unsafe_allow_html=True)
                    if st.button(f"+1 分", key="p1", use_container_width=True):
                        st.session_state.game_scores[0] += 1; st.rerun()
                with col2:
                    st.markdown(f"<div class='player-name'>🔴 {p2_name}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='score-board p2-board'>{st.session_state.game_scores[1]}</div>", unsafe_allow_html=True)
                    if st.button(f"+1 分", key="p2", use_container_width=True):
                        st.session_state.game_scores[1] += 1; st.rerun()
                
                st.write("")
                if st.button("⏹️ 结算本局", use_container_width=True):
                    s1, s2 = st.session_state.game_scores
                    w_code = check_game_winner_standard(s1, s2)
                    if w_code == 0: st.warning("⚠️ 正赛需达21分且净胜2分 (或达30分)。")
                    else:
                        if w_code == 1: st.session_state.p1_wins += 1
                        else: st.session_state.p2_wins += 1
                        st.session_state.game_scores = [0, 0] 
                        st.rerun()

        # --- 4. 结算 ---
        elif st.session_state.stage == 'finished':
            sorted_st = sorted(st.session_state.local_standings.items(), key=lambda x: x[1], reverse=True)
            if sorted_st[0][1] == 2:
                champion = sorted_st[0][0]
                st.balloons()
                st.success(f"👑 本周王者诞生：{champion} (全胜)！")
                if st.button("🏆 颁发奖杯并重置系统", use_container_width=True, type="primary"):
                    record_championship(champion) 
                    st.session_state.clear() 
                    st.rerun()
            else:
                st.error("🚨 出现全员 1胜1负 平局！")
                if st.button("⚔️ 进入加赛大厅", type="primary", use_container_width=True):
                    st.session_state.stage = 'tb_hub'
                    st.rerun()

        # --- 5. 加赛大厅 ---
        elif st.session_state.stage == 'tb_hub':
            st.markdown("### ⚔️ 平局加赛大厅")
            with st.container(border=True):
                st.markdown("#### 1️⃣ 发起新加赛")
                p1 = st.selectbox("选手 1", st.session_state.players, index=0)
                p2 = st.selectbox("选手 2", st.session_state.players, index=1)
                format_type = st.radio("赛制", ["1局定胜负", "3局2胜"], horizontal=True)
                target = st.select_slider("目标分数", options=[1,3,5,7,11] if format_type=="1局定胜负" else [15,21], value=11 if format_type=="1局定胜负" else 15)
                
                if st.button("🚀 开始本场加赛 (横屏)", type="primary", use_container_width=True):
                    if p1 == p2: st.error("不能自己打自己！")
                    else:
                        st.session_state.tb_config = {"p1": p1, "p2": p2, "format": 1 if format_type=="1局定胜负" else 3, "target": target}
                        reset_match_state(); st.session_state.stage = 'tb_playing'; st.rerun()
            
            with st.container(border=True):
                st.markdown("#### 2️⃣ 加赛结束，结算本周总冠军")
                final_champ = st.selectbox("选择最终捧杯王者", st.session_state.players)
                if st.button("🏆 颁发总冠军奖杯并重置", type="primary", use_container_width=True):
                    record_championship(final_champ)
                    st.session_state.clear(); st.rerun()

        # --- 6. 加赛计分板 ---
        elif st.session_state.stage == 'tb_playing':
            conf = st.session_state.tb_config
            p1_name, p2_name, target, best_of = conf['p1'], conf['p2'], conf['target'], conf['format']
            
            st.markdown(f"<div style='text-align:center; color:gray; font-size:14px;'>加赛模式 | 目标: {target}分 ({best_of}局制)</div>", unsafe_allow_html=True)
            if best_of == 3:
                st.markdown(f"<h3 style='text-align: center;'><span style='color:#007BFF;'>🔵 {st.session_state.p1_wins}</span> : <span style='color:#FF4136;'>{st.session_state.p2_wins} 🔴</span></h3>", unsafe_allow_html=True)

            win_req = 2 if best_of == 3 else 1
            if st.session_state.p1_wins == win_req or st.session_state.p2_wins == win_req:
                winner = p1_name if st.session_state.p1_wins == win_req else p2_name
                loser = p2_name if st.session_state.p1_wins == win_req else p1_name
                st.success(f"🎉 {winner} 拿下了本场加赛！")
                if st.button("↩️ 返回加赛大厅", type="primary", use_container_width=True):
                    record_match(winner, loser)
                    st.session_state.stage = 'tb_hub'; st.rerun()
            else:
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"<div class='player-name'>🔵 {p1_name}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='score-board p1-board'>{st.session_state.game_scores[0]}</div>", unsafe_allow_html=True)
                    if st.button(f"+1 分", key="tb_p1", use_container_width=True):
                        st.session_state.game_scores[0] += 1
                        if st.session_state.game_scores[0] >= target:
                            st.session_state.p1_wins += 1; st.session_state.game_scores = [0, 0]
                        st.rerun()
                        
                with col2:
                    st.markdown(f"<div class='player-name'>🔴 {p2_name}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='score-board p2-board'>{st.session_state.game_scores[1]}</div>", unsafe_allow_html=True)
                    if st.button(f"+1 分", key="tb_p2", use_container_width=True):
                        st.session_state.game_scores[1] += 1
                        if st.session_state.game_scores[1] >= target:
                            st.session_state.p2_wins += 1; st.session_state.game_scores = [0, 0]
                        st.rerun()
