from flask import Flask, render_template, request, jsonify
import requests
import datetime
import re

app = Flask(__name__)

# 因为 ID 一样，我们用回最简单的映射
BUILDING_MAP = {
    "上院": "126", "中院": "128", "下院": "127", "东上院": "122",
    "东中院": "564", "东下院": "124", "陈瑞球楼": "125"
}

def get_realtime_data(build_id):
    session = requests.Session()
    main_url = "https://ids.sjtu.edu.cn/classroomUse/goPage?param=00f9e7d21b8915f2595bcf4c5e38d41e5fa0251ff700451747b9ebe10b033327"
    api_url = "https://ids.sjtu.edu.cn/classroomUse/findSchoolCourseInfo"

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": main_url,
        "X-Requested-With": "XMLHttpRequest"
    }

    try:
        session.get(main_url, headers=headers, timeout=5)
        response = session.post(api_url, headers=headers, data={"buildId": build_id}, timeout=5)
        
        if response.status_code == 200:
            json_res = response.json()
            # 🌟 修正：从 data 字典里的 roomList 键获取列表
            room_list = json_res.get('data', {}).get('roomList', [])
            
            realtime_dict = {}
            for item in room_list:
                raw_name = item.get("name", "")
                # 归一化：上院100 -> 100
                clean_key = "".join(re.findall(r'\d+', str(raw_name)))
                if clean_key:
                    realtime_dict[clean_key] = {
                        "actual": item.get("actualStuNum", 0),
                        "total": item.get("zws", 0),
                        "temp": item.get("sensorTemp", "-"),
                        "hum": item.get("sensorHum", "-"),
                        "co2": item.get("sensorCo2", "-"),
                        "pm25": item.get("sensorPm25", "-")
                    }
            print(f"✅ 成功解析 {len(realtime_dict)} 间教室实时数据")
            return realtime_dict
    except Exception as e:
        print(f"❌ 实时数据拉取失败: {e}")
    return {}

def get_schedule_data(build_id, date_str):
    url = "https://ids.sjtu.edu.cn/build/findBuildRoomType"
    payload = {"buildId": build_id, "courseDate": date_str}
    try:
        r = requests.post(url, data=payload, timeout=5)
        return r.json()
    except:
        return None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/search', methods=['POST'])
def search_empty_rooms():
    data = request.json
    target_date = data.get('date')
    building_name = data.get('building')
    start_sec = int(data.get('start_sec', 3))
    end_sec = int(data.get('end_sec', 4))
    
    bid = BUILDING_MAP.get(building_name, "126")
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    
    raw_schedule = get_schedule_data(bid, target_date)
    if not raw_schedule:
        return jsonify({"status": "error", "msg": "教务数据拉取失败"})

    realtime_info = {}
    if target_date == today_str:
        realtime_info = get_realtime_data(bid)

    empty_rooms = []
    # 课表层级是 data -> floorList
    floors = raw_schedule.get("data", {}).get("floorList", [])
    
    for floor in floors:
        for room in floor.get("children", []):
            is_free = True
            for course in room.get("roomCourseList", []):
                c_start, c_end = course.get("startSection", 0), course.get("endSection", 0)
                if not (end_sec < c_start or start_sec > c_end):
                    is_free = False
                    break
            
            if is_free:
                r_name = room.get("name", "")
                # 同样归一化课表教室名：上院100 -> 100
                m_key = "".join(re.findall(r'\d+', str(r_name)))
                info = realtime_info.get(m_key, {})
                empty_rooms.append({"name": r_name, "info": info})

    return jsonify({"status": "success", "rooms": empty_rooms, "date": target_date})

if __name__ == '__main__':
    app.run(debug=True, port=5000)