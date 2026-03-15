
from youtube_transcript_api import YouTubeTranscriptApi

def test_inspect():
    video_id = "jNQXAC9IVRw"
    try:
        api = YouTubeTranscriptApi()
        res = api.fetch(video_id)
        if res and hasattr(res, 'snippets'):
            print(f"Count: {len(res.snippets)}")
            if len(res.snippets) > 0:
                s = res.snippets[0]
                print(f"Snippet Type: {type(s)}")
                print(f"Dir: {dir(s)}")
                print(f"Vars: {vars(s)}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_inspect()
