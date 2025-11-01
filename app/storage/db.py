# veritas_app/storage/db.py
import datetime
import json
import logging
import threading

logger = logging.getLogger(__name__)


def _parse_real_data():
    raw_data = """
0019506a-995f-4ddb-bc51-2af7af212412	熊之蜜民宿	970台灣花蓮縣花蓮市莊敬路200號		"{""type"": ""Point"", ""coordinates"": [121.5935418, 23.9900037]}"	住宿		{}	NULL	NULL	開放	[]	10/1-10/31				-	0930-631336;官方line ID: @209rmnbs		[]	NULL	2025-10-18 02:41:35.081955+00	2025-10-18 02:41:35.081955+00
00df7fd8-c298-465f-b495-c809fe85dd11	幼兒物資-光復親子館 反查詢	976台灣花蓮縣光復鄉糖廠街19號		"{""type"": ""Point"", ""coordinates"": [121.4199475, 23.656755]}"	醫療		{}	NULL	NULL	關閉	[]					-	-		[]	NULL	2025-10-24 04:43:35.587303+00	2025-10-24 04:43:35.587303+00
018a73aa-6360-46a3-99a5-f41a75d6c914	物資站-馬太鞍教會	976台灣花蓮縣光復鄉中山路三段89巷14號		"{""type"": ""Point"", ""coordinates"": [121.4263269, 23.675416]}"	物資		{}	NULL	NULL	關閉	[]					-	-		[]	NULL	2025-10-18 02:41:14.353656+00	2025-10-18 02:41:14.353656+00
01d8f9aa-d71c-430c-93db-8ae5ca9bc60b	鈺達汽車保養廠	981花蓮縣玉里鎮興國路二段35號		"{""type"": ""Point"", ""coordinates"": [121.3200481, 23.3370231]}"	維修		{}	NULL	NULL	開放	[]					-	038888608		[]	NULL	2025-10-18 02:40:57.498327+00	2025-10-18 02:40:57.498327+00
07e29494-c35b-4152-a382-d420d7498e97	光復鄉大同活動中心	976台灣花蓮縣光復鄉中正路一段370號		"{""type"": ""Point"", ""coordinates"": [121.4309574, 23.6632436]}"	廁所		{https://www.google.com/maps/d/u/0/viewer?mid=1hvkIGwDBe9ehupEHxY6KzVSTuLWsGfU&ll=23.6795603475521%2C121.43595756905647&z=14}	NULL	NULL	開放	"[{""name"": ""流動廁所"", ""unit"": ""座"", ""amount"": 5}]"					-	-		[]	NULL	2025-10-18 02:39:06.66224+00	2025-10-18 02:39:06.66224+00
07f1fa9f-06a4-458b-b2d9-4d5afae24077	976花蓮縣光復鄉75巷2弄	976台灣花蓮縣光復鄉中學街79號		"{""type"": ""Point"", ""coordinates"": [121.4287164, 23.6703743]}"	廁所		{https://www.google.com/maps/d/u/0/viewer?mid=1hvkIGwDBe9ehupEHxY6KzVSTuLWsGfU&ll=23.6795603475521%2C121.43595756905647&z=14}	NULL	NULL	開放	"[{""name"": ""流動廁所(無障礙)"", ""unit"": ""座"", ""amount"": 2}]"					-	-		[]	NULL	2025-10-18 02:38:46.520289+00	2025-10-18 02:38:46.520289+00
0b63d2b3-f653-4108-a372-57852fcac767	測試測試 你好	testaddress		"{""type"": ""Point"", ""coordinates"": [35.139567, 47.8388]}"	醫療		{}	NULL	NULL	開放	[]					-	-		[]	NULL	2025-10-23 17:31:49.677714+00	2025-10-23 17:32:32.86237+00
"""
    places = {}
    for line in raw_data.strip().split('\n'):
        cols = line.strip().split('\t')
        place_id = cols[0]

        def clean_value(value):
            return None if value in ['NULL', ''] else value

        def parse_json_str(s):
            try:
                return json.loads(s.replace('""', '"'))
            except Exception:
                return None

        def parse_url_list(s):
            if s.startswith('{') and s.endswith('}'): return [url for url in s[1:-1].split(',') if url]
            return []

        places[place_id] = {
            "id": place_id, "name": cols[1], "address": cols[2], "coordinates": parse_json_str(cols[4]),
            "type": cols[5], "status": clean_value(cols[10]), "contact_phone": clean_value(cols[17]),
            "open_time": clean_value(cols[8]), "end_time": clean_value(cols[9]),
            "website_url": None, "info_sources": parse_url_list(cols[7]), "created_at": clean_value(cols[21]),
            "updated_at": clean_value(cols[22]), "verified_at": clean_value(cols[20])
        }
    return places


_locks = {"global": {"locked": False, "start_time": None}, "places": {}}
_lock_object = threading.Lock()


def acquire_lock(lock_id: str) -> bool:
    with _lock_object:
        target = _locks["global"] if lock_id == "global" else _locks["places"].get(lock_id, {})
        if target.get("locked"): return False
        lock_data = {"locked": True, "start_time": datetime.datetime.now(datetime.timezone.utc)}
        if lock_id == "global":
            _locks["global"] = lock_data
        else:
            _locks["places"][lock_id] = lock_data
        return True


def release_lock(lock_id: str):
    with _lock_object:
        lock_data = {"locked": False, "start_time": None}
        if lock_id == "global":
            _locks["global"] = lock_data
        elif lock_id in _locks["places"]:
            _locks["places"][lock_id] = lock_data


def get_lock_status(lock_id: str) -> dict:
    with _lock_object:
        if lock_id == "global": return _locks["global"]
        return _locks["places"].get(lock_id, {"locked": False, "start_time": None})


mock_db = {"places": _parse_real_data()}


def get_place_by_id(place_id: str) -> dict | None: return mock_db["places"].get(place_id)


def update_place(place_id: str, updates: dict):
    if place_id in mock_db["places"]:
        mock_db["places"][place_id].update(updates)
        mock_db["places"][place_id]["updated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        mock_db["places"][place_id]["verified_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        logger.info(f"[DB] Place {place_id} updated with: {updates}")
