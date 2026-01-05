import requests

def get_replayed_parts(video_id, number_of_parts=3):
    url = f"http://localhost:8001/most-replayed?videoId={video_id}&numberOfParts={number_of_parts}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data['replayedParts']
    else:
        print(f"Error: Unable to fetch data. Status code {response.status_code}")
        print(f"Response text: {response.text}")
        return []