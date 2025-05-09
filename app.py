
from flask import Flask, render_template, send_file, request, redirect, url_for
from googleapiclient.discovery import build
import psycopg2
import io
import pandas as pd
from datetime import datetime, timedelta
import pytz
from collections import defaultdict





# Initialize Flask app
app = Flask(__name__)


# YouTube API
API_KEY = 'AIzaSyCYqYWNXCwY__x6oaBTwC_XLCAOEOplRCs'
youtube_key= build('youtube', 'v3', developerKey=API_KEY)



channels_to_check = {
    "Geo News":        "UC_vt34wimdCzdkrzVejwX9g",
    "ARY News":        "UCMmpLL2ucRHAXbNHiCPyIyg",
    "SAMAA TV":        "UCJekW1Vj5fCVEGdye_mBN6Q",
    "Dunya News":      "UCnMBV5Iw4WqKILKue1nP6Hg",
    "92 News HD":      "UCsgC5cbz3DE2Shh34gNKiog",
    "BOL News":        "UCz2yxQJZgiB_5elTzqV7FiQ",
    "Express News":    "UCTur7oM6mLL0rM2k0znuZpQ",
    "HUM News":        "UC0Um3pnZ2WGBEeoA3BX2sKw",
    "GNN":             "UC35KuZBNIj4S5Ls0yjY-UHQ",
    "Public News":     "UCElJZvY_RVra6qjD8WSQYog",
    "Aaj News":        "UCgBAPAcLsh_MAPvJprIz89w",
    "24 News HD":      "UCcmpeVbSSQlZRvHfdC-CRwg",
    "Neo News HD":     "UCAsvFcpUQegneSh0QAUd64A",
    "City 42":         "UCdTup4kK7Ze08KYp7ReiuMw",
    "Abb Takk News":   "UC5mwDEzm4FzXKoHPBDnuUQQ"
}


channel_ids = set(channels_to_check.values())
id_to_name   = {cid:name for name, cid in channels_to_check.items()}

# Database connection function
def get_db_connection():
    return psycopg2.connect(
        "postgresql://neondb_owner:npg_LWYK2wRoc7QJ@ep-red-violet-a45y3nzx-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require"
    )


# ---------------- Database Routes ----------------





USERNAME = "IMM"
PASSWORD = "imm@geotv"

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = request.form['username']
        pw = request.form['password']
        if user == USERNAME and pw == PASSWORD:
            return redirect(url_for('youtube'))
        else:
            return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')




@app.route('/youtube')
def youtube():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, subscribers, views, videos FROM youtube_stats order by subscribers desc")
        stats_data = cursor.fetchall()
        cursor.close()
        conn.close()

        if not stats_data:
            return render_template('youtube.html', error="No data found")
        return render_template('youtube.html', stats_data=stats_data)
    except Exception as e:
        return f"Database error: {e}"


@app.route('/facebook')
def facebook():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT page_name, follower, likes, following
FROM facebook_stats
ORDER BY
  CASE
    WHEN LOWER(follower) LIKE '%m%' THEN 
      REPLACE(LOWER(follower), 'm followers', '')::FLOAT * 1000000
    WHEN LOWER(follower) LIKE '%k%' THEN 
      REPLACE(LOWER(follower), 'k followers', '')::FLOAT * 1000
    ELSE
      REPLACE(LOWER(follower), 'followers', '')::FLOAT
  END DESC;""")
        stats_data = cursor.fetchall()
        cursor.close()
        conn.close()

        if not stats_data:
            return render_template('facebook.html', error="No data found")
        return render_template('facebook.html', stats_data=stats_data)
    except Exception as e:
        return f"Database error: {e}"


@app.route('/instagram')
def instagram():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            """ SELECT page_name, followers, following, posts
    FROM instagram_stats
    ORDER BY
      CASE
        WHEN LOWER(followers) LIKE '%m%' THEN 
          REGEXP_REPLACE(LOWER(followers), '[^0-9.]', '', 'g')::FLOAT * 1000000
        WHEN LOWER(followers) LIKE '%k%' THEN 
          REGEXP_REPLACE(LOWER(followers), '[^0-9.]', '', 'g')::FLOAT * 1000
        ELSE
          REGEXP_REPLACE(LOWER(followers), '[^0-9.]', '', 'g')::FLOAT
      END DESC;"""
        )
        stats_data = cursor.fetchall()
        cursor.close()
        conn.close()

        if not stats_data:
            return render_template('instagram.html', error="No data found")
        return render_template('instagram.html', stats_data=stats_data)
    except Exception as e:
        return f"Database error: {e}"


@app.route('/simple_stats')
def all_channel_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        channels = {
            "GEO News": "youtube_videos",
            "ARY_News": "ary_videos"
        }

        all_data = {}

        for channel_name, table_name in channels.items():
            cursor.execute(f"""
                SELECT title, channel_name, view_count FROM {table_name}
                WHERE channel_name = %s
                ORDER BY view_count DESC LIMIT 1
            """, (channel_name,))
            most_viewed = cursor.fetchone()

            cursor.execute(f"""
                SELECT title, channel_name, view_count FROM {table_name}
                WHERE channel_name = %s
                ORDER BY view_count ASC LIMIT 1
            """, (channel_name,))
            least_viewed = cursor.fetchone()

            cursor.execute(f"""
                SELECT title, channel_name, like_count FROM {table_name}
                WHERE channel_name = %s
                ORDER BY like_count DESC LIMIT 1
            """, (channel_name,))
            most_liked = cursor.fetchone()

            cursor.execute(f"""
                SELECT title, channel_name, like_count FROM {table_name}
                WHERE channel_name = %s
                ORDER BY like_count ASC LIMIT 1
            """, (channel_name,))
            least_liked = cursor.fetchone()

            print(f"Channel: {channel_name}")
            print(f"Most Viewed: {most_viewed}")
            print(f"Least Viewed: {least_viewed}")
            print(f"Most Liked: {most_liked}")
            print(f"Least Liked: {least_liked}")

            # all_data[channel_name] = {
            #     "most_viewed": most_viewed or ("No data", channel_name, 0),
            #     "least_viewed": least_viewed or ("No data", channel_name, 0),
            #     "most_liked": most_liked or ("No data", channel_name, 0),
            #     "least_liked": least_liked or ("No data", channel_name, 0),
            # }


            all_data[channel_name] = {
                "most_viewed": most_viewed if most_viewed else ("No data", channel_name, 0),
                "least_viewed": least_viewed if least_viewed else  ("No data", channel_name, 0),
                "most_liked": most_liked if most_liked else  ("No data", channel_name, 0),
                "least_liked": least_liked if least_liked else  ("No data", channel_name, 0),
            }


        
        print(f"All Data for {channel_name}: {all_data[channel_name]}")
        cursor.close()
        conn.close()

        return render_template("simple_stats.html", all_data=all_data)

    except Exception as e:
        return f"Database error: {e}"

# @app.route('/youtube_tags', methods=['GET', 'POST'])
# def youtube_tags():
#     stats_data = []
#     error = None

#     if request.method == 'POST':
#         keyword = request.form.get('keyword', '').strip()
#         if not keyword:
#             return render_template('youtube_tags.html', stats_data=[], error="Please enter a keyword")

#         try:
#             # 1) build your YouTube search
#             published_after = (datetime.now(pytz.UTC) - timedelta(days=3)).isoformat()
#             search_resp = youtube_key.search().list(
#                 q=keyword,
#                 part='snippet',
#                 type='video',
#                 order='relevance',
#                 maxResults=25,
#                 regionCode='PK',               # or 'IN' if you prefer
#                 publishedAfter=published_after
#             ).execute()

#             # 2) collect only videos from your allowed channels
#             video_ids = []
#             for item in search_resp['items']:
#                 cid = item['snippet']['channelId']
#                 if cid in channel_ids:
#                     video_ids.append(item['id']['videoId'])

#             # 3) if we found anything, fetch stats + snippet
#             videos = []
#             if video_ids:
#                 vid_resp = youtube_key.videos().list(
#                     part='statistics,snippet',
#                     id=','.join(video_ids)
#                 ).execute()

#                 for itm in vid_resp['items']:
#                     title = itm['snippet']['title']
#                     cid   = itm['snippet']['channelId']
#                     views = int(itm['statistics'].get('viewCount', 0))
#                     ch    = id_to_name[cid]
#                     url   = f"https://www.youtube.com/watch?v={itm['id']}"
#                     videos.append((title, views, ch, url))

#                 # 4) sort & save to DB
#                 videos.sort(reverse=True)
#                 conn   = get_db_connection()
#                 cursor = conn.cursor()
#                 for title, views, ch, url in videos:
#                     cursor.execute("""
#                         INSERT INTO youtube_tags (title, views, channel_name, link)
#                         VALUES (%s, %s, %s, %s)
#                         on conflict (title) do update set views = excluded.views
#                     """, (title, views, ch, url))
#                 conn.commit()
#                 cursor.close()
#                 conn.close()

#             # 5) pass results back to template
#             stats_data = videos

#         except Exception as e:
#             error = f"Error: {e}"

#     return render_template('youtube_tags.html', stats_data=stats_data, error=error)








# @app.route('/youtube_tags1', methods=['GET', 'POST'])
# def youtube_tags1():
#     stats_data = []
#     error = None

#     if request.method == 'POST':
#         keyword = request.form.get('keyword', '').strip()
#         if not keyword:
#             return render_template('youtube_tags1.html', stats_data=[], error="Please enter a keyword")

#         try:
#             published_after = (datetime.now(pytz.UTC) - timedelta(days=7)).isoformat()

#             videos = []

#             for channel_name, channel_id in channels.items():
#                 search_resp = youtube.search().list(
#                     q=keyword,
#                     part='snippet',
#                     type='video',
#                     channelId=channel_id,
#                     publishedAfter=published_after,
#                     maxResults=25,
#                     order='date'
#                 ).execute()

#                 video_ids = [item['id']['videoId'] for item in search_resp.get('items', [])]

#                 if video_ids:
#                     vid_resp = youtube.videos().list(
#                         part='statistics,snippet',
#                         id=','.join(video_ids)
#                     ).execute()

#                     for itm in vid_resp['items']:
#                         title = itm['snippet']['title'].lower()
#                         if keyword.lower() in title:
#                             views = int(itm['statistics'].get('viewCount', 0))
#                             # url = f"https://www.youtube.com/watch?v={itm['id']}"
#                             videos.append((views, channel_name))

#             # Sort by views
#             videos.sort(reverse=True)

#             # Save to DB
#             conn = get_db_connection()
#             cursor = conn.cursor()
#             for views, ch in videos:
#                 cursor.execute("""
#                     INSERT INTO youtube_tags1 (views, channel_name)
#                     VALUES (%s, %s, %s)
#                     ON CONFLICT (link) DO UPDATE SET views = EXCLUDED.views
#                 """, (views, ch))
#             conn.commit()
#             cursor.close()
#             conn.close()

#             stats_data = videos

#         except Exception as e:
#             error = f"Error: {e}"

#     return render_template('youtube_tags1.html', stats_data=stats_data, error=error)









@app.route('/youtube_tags', methods=['GET', 'POST'])
def youtube_tags():
    stats_data = []
    error = None

    if request.method == 'POST':
        keyword = request.form.get('keyword', '').strip()
        if not keyword:
            return render_template('youtube_tags.html', stats_data=[], error="Please enter a keyword")

        try:
            published_after = (datetime.now(pytz.UTC) - timedelta(days=3)).isoformat()

            # Step 1: Search for relevant videos
            search_response = youtube.search().list(
                q=keyword,
                part='snippet',
                type='video',
                order='relevance',
                maxResults=25,
                regionCode='IN',
                publishedAfter=published_after
            ).execute()

            # Step 2: Extract video IDs
            video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]

            videos = []
            if video_ids:
                # Step 3: Get video details
                video_response = youtube.videos().list(
                    part='statistics,snippet',
                    id=','.join(video_ids)
                ).execute()

                for item in video_response.get('items', []):
                    title = item['snippet']['title']
                    channel = item['snippet']['channelTitle']
                    views = int(item['statistics'].get('viewCount', 0))
                    video_id = item['id']
                    url = f"https://www.youtube.com/watch?v={video_id}"
                    videos.append((views, title, channel, url))

                # Step 4: Sort by views
                videos.sort(reverse=True)

                # Step 5: Save to database
                conn = get_db_connection()
                cursor = conn.cursor()
                for views, title, channel, url in videos:
                    cursor.execute("""
                        INSERT INTO youtube_tags (title, views, channel_name, link)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (title) DO UPDATE SET views = EXCLUDED.views
                    """, (title, views, channel, url))
                conn.commit()
                cursor.close()
                conn.close()

            stats_data = videos

        except Exception as e:
            error = f"Error: {e}"

    return render_template('youtube_tags.html', stats_data=stats_data, error=error)



@app.route('/download/<platform>')
def download_excel(platform):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Choose SQL query and sheet name based on platform
        if platform == 'facebook':
            cursor.execute("SELECT page_name, follower, likes, following FROM facebook_stats")
            columns = ['Page Name', 'Follower', 'Likes', 'Following']
            filename = 'facebook_stats.xlsx'
            sheet_name = 'Facebook Stats'
        elif platform == 'youtube':
            cursor.execute("SELECT name, subscribers, views, videos FROM youtube_stats")
            columns = ['Channel Name', 'Subscribers', 'Views', 'Videos']
            filename = 'youtube_stats.xlsx'
            sheet_name = 'YouTube Stats'
        elif platform == 'youtube_tags':
            cursor.execute("SELECT title, views, channel_name, link FROM youtube_tags")
            columns = ['title', 'views', 'channel_name', 'url']
            filename = 'youtube_tags.xlsx'
            sheet_name = 'YouTube tags'

        elif platform == 'youtube_tags1':
            cursor.execute("SELECT  views, channel_name, link FROM youtube_tags")
            columns = ['views', 'channel_name', 'url']
            filename = 'youtube_tags1.xlsx'
            sheet_name = 'YouTube tags1'
        elif platform == 'instagram':
            cursor.execute("SELECT page_name, followers, following, posts FROM instagram_stats")
            columns = ['Page Name', 'Followers', 'Following', 'Posts']
            filename = 'instagram_stats.xlsx'
            sheet_name = 'Instagram Stats'
        else:
            return "Invalid platform"

        rows = cursor.fetchall()
        cursor.close()
        conn.close()

        df = pd.DataFrame(rows, columns=columns)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name)
        output.seek(0)

        return send_file(
            output,
            download_name=filename,
            as_attachment=True,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        return f"Download failed: {e}"


# Run the app on Replit
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000)
