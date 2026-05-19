from flask import Flask, render_template, request, jsonify, Response
import json
import os
import pandas as pd
import io

app = Flask(__name__)

DATA_FILE = 'players.json'

# 初始化資料
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/players', methods=['GET', 'POST'])
def handle_players():
    players = load_data()
    if request.method == 'POST':
        new_player = request.json
        # 限制隊伍人數 (3-13人)
        team_count = len([p for p in players if p['team'] == new_player['team']])
        if team_count >= 13:
            return jsonify({"error": "該隊已達13人上限"}), 400
        
        # 初始化數據欄位
        stats = {
            "id": len(players) + 1,
            "name": new_player['name'],
            "number": new_player['number'],
            "team": new_player['team'],
            "fgm": 0, "fga": 0, "tpm": 0, "tpa": 0, 
            "ftm": 0, "fta": 0, "orb": 0, "drb": 0, 
            "ast": 0, "stl": 0, "blk": 0, "tov": 0, "pf": 0
        }
        players.append(stats)
        save_data(players)
        return jsonify(stats)
    return jsonify(players)

@app.route('/api/update', methods=['POST'])
def update_stat():
    data = request.json
    players = load_data()
    for p in players:
        if p['id'] == data['id']:
            field = data['field']
            delta = data['delta']
            
            # 處理虛擬欄位 (twopm, twopa) 避免 KeyError
            if field in ['twopm', 'twopa']:
                if field == 'twopm':
                    if delta > 0:
                        p['fgm'] += 1
                        p['fga'] += 1
                    elif delta < 0:
                        p['fgm'] = max(0, p['fgm'] - 1)
                        p['fga'] = max(0, p['fga'] - 1)
                elif field == 'twopa':
                    if delta > 0:
                        p['fga'] += 1
                    elif delta < 0:
                        p['fga'] = max(0, p['fga'] - 1)
            else:
                p[field] = max(0, p[field] + delta)
                # 連動邏輯：投進球，出手數也要加
                if delta > 0:
                    if field == 'tpm': 
                        p['tpa'] += 1
                        p['fgm'] += 1
                        p['fga'] += 1
                    elif field == 'tpa': 
                        p['fga'] += 1
                    elif field == 'ftm': 
                        p['fta'] += 1
                elif delta < 0:
                    if field == 'tpm': 
                        p['tpa'] = max(0, p['tpa'] - 1)
                        p['fgm'] = max(0, p['fgm'] - 1)
                        p['fga'] = max(0, p['fga'] - 1)
                    elif field == 'tpa':
                        p['fga'] = max(0, p['fga'] - 1)
                    elif field == 'ftm':
                        p['fta'] = max(0, p['fta'] - 1)
            break
    save_data(players)
    return jsonify({"status": "success"})

@app.route('/api/players/<int:player_id>', methods=['DELETE'])
def delete_player(player_id):
    players = load_data()
    # 過濾掉指定的球員
    players = [p for p in players if p['id'] != player_id]
    save_data(players)
    return jsonify({"status": "success"})

@app.route('/export')
def export_csv():
    players = load_data()
    df_list = []
    for p in players:
        pts = max(0, p['fgm'] - p['tpm']) * 2 + p['tpm'] * 3 + p['ftm']
        reb = p['orb'] + p['drb']
        fg_pct = f"{(p['fgm']/p['fga']*100):.1f}%" if p['fga'] > 0 else "0%"
        tp_pct = f"{(p['tpm']/p['tpa']*100):.1f}%" if p['tpa'] > 0 else "0%"
        
        df_list.append({
            "隊伍": p['team'], "姓名": p['name'], "號碼": p['number'],
            "得分": pts, "籃板": reb, "進攻籃板": p['orb'], "防守籃板": p['drb'],
            "助攻": p['ast'], "抄截": p['stl'], "阻攻": p['blk'], "失誤": p['tov'], "犯規": p['pf'],
            "總進球": p['fgm'], "總出手": p['fga'], "命中率": fg_pct,
            "兩分進球": max(0, p['fgm'] - p['tpm']),
            "三分進球": p['tpm'], "三分出手": p['tpa'], "三分命中率": tp_pct,
            "罰球進球": p['ftm'], "罰球出手": p['fta']
        })
    
    columns = ["隊伍", "姓名", "號碼", "得分", "籃板", "進攻籃板", "防守籃板", 
               "助攻", "抄截", "阻攻", "失誤", "犯規", 
               "總進球", "總出手", "命中率", 
               "兩分進球",
               "三分進球", "三分出手", "三分命中率", 
               "罰球進球", "罰球出手"]
    df = pd.DataFrame(df_list, columns=columns)
    output = io.BytesIO()
    # 使用 UTF-8-SIG 確保 Excel 打開不亂碼
    df.to_csv(output, index=False, encoding='utf-8-sig')
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-disposition": "attachment; filename=stats.csv"}
    )

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)