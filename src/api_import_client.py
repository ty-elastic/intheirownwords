import json
import requests

API_PORT=8502

def enqueue(source_url, title, date, kind, origin, save_frames, persist_days=None, youtube_url=None, local_path=None):
    u = {}
    u['youtube_url'] = youtube_url
    u['source_url'] = source_url
    u['title'] = title
    u['date'] = date.strftime('%Y-%m-%d')
    u['kind'] = kind
    u['origin'] = origin
    u['save_frames'] = save_frames
    u['persist_days'] = persist_days
    u['youtube_url'] = youtube_url
    u['local_path'] = local_path

    response = requests.post(f"http://ingest:{API_PORT}/import", json=u)


def get_status():
    response = requests.get(f"http://ingest:{API_PORT}/import/status")
    data = response.json()
    print(f"status={data}")
    return data
