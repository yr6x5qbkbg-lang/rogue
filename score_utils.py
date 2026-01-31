import json
import os
import time
from datetime import datetime

VERSION = "v 0.1.3+"

SCORES_FILE = "high_scores.json"
DEBUG_LOG_FILE = "high_scores.txt"

def save_score(gold: int, floor: int, level: int):
    # 既存のスコアを読み込む
    scores = load_scores()
    
    # 新しいスコアを追加
    new_score = {
        "gold": gold,
        "floor": floor,
        "level": level,
    }
    scores.append(new_score)
    
    # ゴールド順にソートして、上位30件だけ残す
    scores.sort(key=lambda x: x["gold"], reverse=True)
    scores = scores[:30]
    
    with open(SCORES_FILE, "w") as f:
        json.dump(scores, f)

def save_detailed_score(engine, gold, is_cleared=False):          # ===デバッグ記録用===
    player = engine.player
    elapsed_time = int(time.time() - engine.start_time)
    minutes, seconds = divmod(elapsed_time, 60)
    
    clear_mark = "☆" if is_cleared else " "

    # 記録用データの作成
    score_data = {
        "version": VERSION,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "gold": gold,
        "bonus_from_items": engine.item_bonus_gold,
        "floor": engine.game_world.current_floor,
        "level": player.level.current_level,
        "turns": engine.turn_count,
        "time_sec": elapsed_time,
        "total_exp": engine.total_exp,
        "damage_dealt": engine.total_damage_dealt,
        "total_rooms": engine.total_rooms,
        "damage_taken": engine.total_damage_taken,
        "attacked_count": engine.times_attacked,
        "stats": {
            "max_hp": player.fighter.max_hp,
            "power": player.fighter.power,
            "defense": player.fighter.defense,
        "clear_mark": clear_mark
        }
    }

    # --- 1. JSON (ランキング用) の更新 ---
    scores = load_scores()
    scores.append(score_data)
    scores.sort(key=lambda x: x["gold"], reverse=True)
    with open(SCORES_FILE, "w") as f:
        json.dump(scores[:30], f)

    # --- 2. TXT (デバッグログ用) への追記 ---
    with open(DEBUG_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"{'-' * 30} {clear_mark}\n")
        f.write(f"Date: {score_data['date']}\n")
        f.write(f"Result: Gold {score_data['gold']}g,{score_data['floor']}F, Lv.{score_data['level']}\n")
        f.write(f"Turns: {score_data['turns']}, Time: {elapsed_time}s, < {minutes}m {seconds:02d}s >\n")
        f.write(f"Total Damage Dealt: {score_data['damage_dealt']}, Total Rooms: {score_data['total_rooms']}\n")
        f.write(f"Exp: {score_data['total_exp']}, Damage Taken: {score_data['damage_taken']}, Bonus: {score_data['bonus_from_items']}g\n")
        f.write(f"Final Stats: HP {player.fighter.max_hp}, ATK {player.fighter.power}, DEF {player.fighter.defense}\n")
        f.write(f"{'-'* 30} [ {VERSION} ]\n\n")

    return score_data

def load_scores():
    if not os.path.exists(SCORES_FILE):
        return []
    with open(SCORES_FILE, "r") as f:
        return json.load(f)