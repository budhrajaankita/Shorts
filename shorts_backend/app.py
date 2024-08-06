from functools import lru_cache
from flask import Flask, jsonify, request
from flask_cors import CORS
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
from flask_sqlalchemy import SQLAlchemy
import openai
import redis
import os
from dotenv import load_dotenv
from datetime.datetime import datetime


app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@db/ytfull')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')
YT_API_KEY = os.getenv('YT_API_KEY')

# Create a YouTube API client
youtube = build('youtube', 'v3', developerKey=YT_API_KEY)

# TechCrunch channel ID
# channel_id = ''UCCjyq_K1Xwfg8Lndy7lKMpA'
channel_id = 'UCqnbDFdCpuN8CMEg0VuEBqA'

# redis_client = redis.Redis(host='localhost', port=6379, db=0)
# redis_client = redis.Redis(host="redis_db", port=6379)
# redis_client = redis.Redis(host='redis_db', port=6379, db=0)


class VideoSummary(db.Model):
    video_id = db.Column(db.String(20), primary_key=True)
    summary = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime)

    def __init__(self, video_id, summary):
        self.video_id = video_id
        self.summary = summary


def get_summary_from_cache(video_id):
    summary = VideoSummary.query.get(video_id)
    return summary.summary if summary else None


def set_summary_in_cache(video_id, summary):
    video_summary = VideoSummary(video_id=video_id, summary=summary)
    db.session.merge(video_summary)
    db.session.commit()


# Initialize variables for pagination
max_results = 5
current_index = 0
# video_summary_cache = {}
videos_data = []


@app.route('/videos', methods=['GET'])
def get_video_data(max_results=10):
    global videos_data
    videos_data = []
    request = youtube.search().list(
        part="id,snippet",
        channelId=channel_id,
        maxResults=max_results,
        type="video",
        order="date"
    )
    response = request.execute()
   
    for item in response['items']:
        video_id = item['id']['videoId']
        video_title = item['snippet']['title']
        video_thumbnail = item['snippet']['thumbnails']['default']['url']
        summary = fetch_transcript_and_summarize(video_id)
        videos_data.append({
            'video_id': video_id,
            'video_title': video_title,
            'video_thumbnail': video_thumbnail,
            'summary': summary
        })

        print(jsonify(videos_data))
   
    return jsonify(videos_data)



def fetch_transcript_and_summarize(video_id):
    summary = get_summary_from_cache(video_id)
    print("Here")
    if summary:
        return summary
    # if video_id in video_summary_cache:
    #     print("FOUND")
    #     return video_summary_cache[video_id]
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        print("SHUBHAAAAAAAAAAMMMMMMMMMMMMM")

        transcript_text = '\n'.join([entry['text'] for entry in transcript])
        prompt = f"Summarize the following transcript in 100 words:\n{transcript_text}"
        messages = [{"role": "user", "content": prompt}]

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7
        )
        summary = response.choices[0].message["content"]
        # video_summary_cache[video_id] = summary
        set_summary_in_cache(video_id, summary)

        return summary
    except Exception as e:
        print(f"Error processing video ID {video_id}: {e}")
        return None

# Fetch video data (including IDs and thumbnails)
# videos_data = get_video_data(channel_id)


# def set_summary_in_cache(video_id, summary):
#     """
#     Store summary in cache.
#     """
#     redis_client.set(video_id, summary)


# @lru_cache(maxsize=1024)
# @app.route('/api/summary-cache/<video_id>')
# def get_summary_from_cache(video_id):
#     """
#     Retrieve summary from Redis cache.
#     Use LRU cache for efficient cache lookups.
#     """
#     cached_summary = redis_client.get(video_id)
#     if cached_summary:
#         return cached_summary.decode('utf-8')
#     return None




# @app.route('/summary/', methods=['GET'])
# def get_summary():
#     global current_index
#     output = {}
    
#     # Determine the range of videos to process
#     start_index = current_index
#     end_index = min(current_index + 1, len(videos_data))  # Display one card at a time
    
#     for idx in range(start_index, end_index):
#         video_data = videos_data[idx]
#         video_id = video_data['video_id']
#         video_title = video_data['video_title']
#         video_thumbnail = video_data['video_thumbnail']
        
#         print(f"Summarized transcript for video ID {video_id}:")
#         summary = fetch_transcript_and_summarize(video_id)
        
#         if summary:
#             print(f"Summary: {summary}")
#             print(f"Video Title: {video_title}")
#             print(f"Thumbnail URL: {video_thumbnail}")
#             video_detail = {'summary': summary, 'thumbnail_url': video_thumbnail, 'title': video_title}
#             output[video_id] = video_detail
#         else:
#             print("Failed to summarize.")
    
#     current_index = end_index
    
#     return jsonify(output)

@app.route('/summary/', methods=['GET'])
def get_summary():
    global videos_data

    video_id = request.args.get('video_id')
    output = {}

    if video_id:
        # # Check if the summary is in the cache
        # summary = get_summary_from_cache(video_id)
        # if summary:
        #     # Summary found in the cache, retrieve video data and return it
        #     video_data = next((v for v in videos_data if v['video_id'] == video_id), None)
        #     if video_data:
        #         video_title = video_data['video_title']
        #         video_thumbnail = video_data['video_thumbnail']
        #         output = {'summary': summary, 'thumbnail_url': video_thumbnail, 'title': video_title}
        #     else:
        #         print(f"Video data not found for video ID {video_id}")
        # else:
            # Summary not in the cache, fetch and summarize the transcript
            print(f"Summarized transcript for video ID {video_id}:")
            summary = fetch_transcript_and_summarize(video_id)
            if summary:
                print(f"Summary: {summary}")
                video_data = next((v for v in videos_data if v['video_id'] == video_id), None)
                if video_data:
                    video_title = video_data['video_title']
                    video_thumbnail = video_data['video_thumbnail']
                    video_detail = {'summary': summary, 'thumbnail_url': video_thumbnail, 'title': video_title}
                    output = video_detail
                else:
                    print(f"Video data not found for video ID {video_id}")
            else:
                print("Failed to summarize.")
    else:
        print("No video ID provided in the request")

    return jsonify(output)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5050)
