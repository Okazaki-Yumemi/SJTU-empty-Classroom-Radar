from flask import Flask, render_template, request, jsonify
import requests
import datetime

app = Flask(__name__)

# 楼栋代码字典
BUILDING_MAP = {
    "上院": "126", "中院": "128", "下院": "127", "东上院": "122",
    "东中院": "564", "东下院": "124", "陈瑞球楼": "125"
}

def get_schedule_data(build_id, date_str):
    """负责去学校服务器拉取原始数据"""
    # ⚠️ TODO: 把下面这个 URL 换成你在抓包时找到的真实的接口地址！！
    url = "https://ids.sjtu.edu.cn/build/findBuildRoomType"
    
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload = {"buildId": build_id, "courseDate": date_str}
    
    try:
        response = requests.post(url, headers=headers, data=payload, timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"请求报错: {e}")
    return None

# 用户访问主页时，发送 HTML 页面
@app.route('/')
def home():
    return render_template('index.html')

# 这个是专属的数据接口，供网页上的 JavaScript 提取数据
@app.route('/api/search', methods=['POST'])
def search_empty_rooms():
    # 接收网页发来的 JSON 数据
    data = request.json
    building_name = data.get('building')
    start_sec = int(data.get('start_sec'))
    end_sec = int(data.get('end_sec'))
    
    build_id = BUILDING_MAP.get(building_name)
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    
    raw_data = get_schedule_data(build_id, today_str)
    if not raw_data:
        return jsonify({"status": "error", "msg": "教务系统数据拉取失败"})

    # 核心算法：筛选空闲教室
    empty_rooms = []
    floors = raw_data.get("data", {}).get("floorList", [])
    
    for floor in floors:
        for room in floor.get("children", []):
            is_free = True
            courses = room.get("roomCourseList", [])
            
            for course in courses:
                c_start = course.get("startSection", 0)
                c_end = course.get("endSection", 0)
                
                # 时间重叠判定逻辑
                if not (end_sec < c_start or start_sec > c_end):
                    is_free = False
                    break 
            
            if is_free:
                empty_rooms.append(room.get("name"))
                
    # 把结果打包成 JSON 发回给网页
    return jsonify({
        "status": "success", 
        "rooms": empty_rooms,
        "date": today_str
    })

if __name__ == '__main__':
    # 重新启动服务器！
    print("🌟 服务器重启中...")
    app.run(debug=True)