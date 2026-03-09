import requests
import datetime

# 💡 1. 建立我们交大的专属数据字典
# 根据你的截图完美复刻的时间表
TIME_MAP = {
    1: "08:00-08:45", 2: "08:55-09:40", 3: "10:00-10:45", 4: "10:55-11:40",
    5: "12:00-12:45", 6: "12:55-13:40", 7: "14:00-14:45", 8: "14:55-15:40",
    9: "16:00-16:45", 10: "16:55-17:40", 11: "18:00-18:45", 12: "18:55-19:40",
    13: "20:00-20:45", 14: "20:55-21:40"
}

# 楼栋代码字典（你之前找出来的宝藏）
BUILDING_MAP = {
    "上院": "126", "中院": "128", "下院": "127", "东上院": "122",
    "东中院": "564", "东下院": "124", "陈瑞球楼": "125"
}

def get_schedule_data(build_id, date_str):
    """专门负责去学校服务器拉取原始数据"""
    url = "https://ids.sjtu.edu.cn/build/findBuildRoomType" # ⚠️ 记得填入你的真实 URL
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload = {"buildId": build_id, "courseDate": date_str}
    
    try:
        response = requests.post(url, headers=headers, data=payload)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"请求报错: {e}")
    return None

def find_empty_rooms():
    """交互式寻找空闲教室"""
    print("🌟 欢迎使用 SJTU 空闲教室雷达 🌟")
    
    # 获取日期
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    
    # 模拟网页上的下拉选择
    building_name = input("📍 请选择教学楼 (上院/中院/下院/东上院/东下院/陈瑞球楼) [默认下院]: ") or "下院"
    start_sec = int(input("⏰ 请选择开始节次 (1-14) [默认3]: ") or 3)
    end_sec = int(input("⏰ 请选择结束节次 (1-14) [默认4]: ") or 4)
    
    build_id = BUILDING_MAP.get(building_name)
    if not build_id:
        print("❌ 找不到这栋楼，请检查拼写！")
        return

    print(f"\n🚀 正在扫描 {building_name} 在 {today_str} 第 {start_sec}-{end_sec} 节的空闲状态...")
    
    raw_data = get_schedule_data(build_id, today_str)
    if not raw_data:
        print("❌ 数据拉取失败")
        return

    # 核心算法：筛选空闲教室
    empty_rooms = []
    floors = raw_data.get("data", {}).get("floorList", [])
    
    for floor in floors:
        for room in floor.get("children", []):
            is_free = True # 先假设它是空闲的
            courses = room.get("roomCourseList", [])
            
            for course in courses:
                c_start = course.get("startSection", 0)
                c_end = course.get("endSection", 0)
                
                # 判断这节课是否和我们的目标时间有重叠（交集）
                # 只要不是【完全在这节课之前】或【完全在这节课之后】，就是有重叠！
                if not (end_sec < c_start or start_sec > c_end):
                    is_free = False
                    break # 发现有课冲突，直接放弃这间教室，检查下一个
            
            if is_free:
                empty_rooms.append(room.get("name"))

    # 打印结果
    time_display = f"{TIME_MAP[start_sec][:5]} - {TIME_MAP[end_sec][-5:]}"
    print("-" * 50)
    print(f"✅ 扫描完成！时段: 第{start_sec}-{end_sec}节 ({time_display})")
    print(f"🏫 【{building_name}】共有 {len(empty_rooms)} 间空闲教室：")
    
    # 每行打印 5 个教室，看起来更整齐
    for i in range(0, len(empty_rooms), 5):
        print("  ".join(empty_rooms[i:i+5]))
    print("-" * 50)

if __name__ == "__main__":
    find_empty_rooms()