from flask import Flask, render_template, request, jsonify
import googleapiclient.discovery

app = Flask(__name__)

YOUTUBE_API_KEY = "AIzaSyCf4r6vIlVsNcmaEaPS-mm8KARh9KS77sg"

def youtube_client():
    return googleapiclient.discovery.build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

def get_channel_id_from_display_name(youtube, display_name):
    request = youtube.search().list(part="snippet", q=display_name, type="channel", maxResults=1)
    response = request.execute()
    if response.get("items"):
        return response["items"][0]["id"]["channelId"]
    return None

def scrape_yt_data(url, data_type):
    youtube = youtube_client()

    video_id = None
    channel_id = None
    channel_username = None
    display_name = None

    if "watch?v=" in url:
        video_id = url.split("watch?v=")[-1].split("&")[0]
    elif "youtu.be/" in url:
        video_id = url.split("youtu.be/")[-1].split("?")[0]
    elif "/channel/" in url:
        channel_id = url.split("/channel/")[-1].split("/")[0]
    elif "/@" in url:
        display_name = url.split("/@")[-1].split("/")[0]
    else:
        return {"error": "Invalid URL"}

    if video_id:
        if data_type == 'comments':
            request = youtube.commentThreads().list(part="snippet", videoId=video_id, maxResults=100)
            response = request.execute()
            return [
                {
                    "author": item["snippet"]["topLevelComment"]["snippet"]["authorDisplayName"],
                    "text": item["snippet"]["topLevelComment"]["snippet"]["textDisplay"],
                }
                for item in response.get("items", [])
            ]
        elif data_type == 'likes':
            request = youtube.videos().list(part="statistics", id=video_id)
            response = request.execute()
            return {"likes": response.get("items", [])[0]["statistics"]["likeCount"]}
        else:
            return {"error": "Invalid scraping request for YouTube video."}

    if channel_id or display_name:
        if display_name:  
            channel_id = get_channel_id_from_display_name(youtube, display_name)
            if not channel_id:
                return {"error": "Channel not found for the provided display name."}

        if data_type == 'subscribers':
            request = youtube.channels().list(part="statistics", id=channel_id)
            response = request.execute()
            if response.get("items"):
                return {"subscribers": response["items"][0]["statistics"]["subscriberCount"]}
            return {"error": "No data found for the channel."}
        else:
            return {"error": "Invalid scraping request for YouTube channel."}

    return {"error": "Invalid URL or data type"}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    url = request.form['url']
    data_type = request.form['data_type']
    result = scrape_yt_data(url, data_type)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
