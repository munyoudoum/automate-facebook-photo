import os
import requests

from PIL import Image, ImageDraw, ImageFont

from apscheduler.schedulers.blocking import BlockingScheduler


sched = BlockingScheduler()

# FACEBOOK
FACEBOOK_HOSTNAME = os.environ.get("HOSTNAME", "graph.facebook.com")
FACEBOOK_API = "https://" + FACEBOOK_HOSTNAME + "/v15.0"
FACEBOOK_ACCESS_TOKEN = os.environ["FACEBOOK_ACCESS_TOKEN"]
FACEBOOK_PHOTOPOST_ID = os.environ["FACEBOOK_PHOTOPOST_ID"]
LIKES = FOLLOWERS = REACTIONS = SHARES = COMMENTS = 0


def get_post_data(post_id):
    """Get post data from Facebook API

    Args:
        post_id (str): Facebook post id. format: "pageid_postid"

    Returns:
        dict: Facebook get post data response

    Examples:
        >>> get_post_data("123456789_123456789")
            {
                "reactions":{
                    "data":[],
                    "summary":{
                        "total_count":2
                    }
                },
                "comments":{
                    "data":[],
                    "summary":{
                        "total_count":0
                    }
                },
                "shares":{
                    "count":1
                },
                "id":"103630545568311_169549302309768"
            }
    """
    response = requests.get(
        FACEBOOK_API + f"/{post_id}",
        params={
            "fields": "reactions.summary(total_count),comments.filter(stream).summary(total_count),shares",
            "access_token": FACEBOOK_ACCESS_TOKEN,
        },
    )
    return response.json()


def update_post_data(post_id, media_fbid):
    response = requests.post(
        FACEBOOK_API + f"/{post_id}",
        json={"attached_media": [{"media_fbid": media_fbid}]},
        params={"access_token": FACEBOOK_ACCESS_TOKEN},
    )
    return response.json()


def create_fbpic(path, likes, followers, reactions, comments, shares):
    img = Image.open(path)
    draw = ImageDraw.Draw(img)
    font = ImageFont.truetype("Inter-Bold.ttf", 45)
    draw.text(
        (55, 950),
        likes,
        font=font,
        fill=(255, 255, 255),
        align="center",
    )
    draw.text(
        (310, 950),
        followers,
        font=font,
        fill=(255, 255, 255),
        align="center",
    )
    draw.text(
        (802, 790),
        f"Reactions: {reactions}",
        font=font,
        fill=(240, 240, 240),
        align="center",
    )
    draw.text(
        (780, 870),
        f"Comments: {comments}",
        font=font,
        fill=(240, 240, 240),
        align="center",
    )
    draw.text(
        (868, 950),
        f"Shares: {shares}",
        font=font,
        fill=(240, 240, 240),
        align="center",
    )
    img.save("facebookpost.png")


def get_likes_followers():
    response = requests.get(
        FACEBOOK_API + f"/me",
        params={
            "fields": "fan_count,followers_count",
            "access_token": FACEBOOK_ACCESS_TOKEN,
        },
    )
    return response.json()


def post_photo():
    response = requests.post(
        FACEBOOK_API + f"/me/photos",
        files={"source": open("facebookpost.png", "rb")},
        params={"access_token": FACEBOOK_ACCESS_TOKEN, "published": False},
    )
    return response.json()


@sched.scheduled_job("interval", minutes=int(os.environ.get("FB_SCHEDULE_INTERVAL", 1)))
def fb_pic():
    global LIKES, FOLLOWERS, REACTIONS, SHARES, COMMENTS
    page_data = get_likes_followers()
    likes = page_data["fan_count"]
    followers = page_data["followers_count"]
    post_data = get_post_data(FACEBOOK_PHOTOPOST_ID)
    shares = post_data["shares"]["count"] if "shares" in post_data else 0
    comments = post_data["comments"]["summary"]["total_count"]
    reactions = post_data["reactions"]["summary"]["total_count"]
    if (
        likes != LIKES
        or followers != FOLLOWERS
        or reactions != REACTIONS
        or comments != COMMENTS
        or shares != SHARES
    ):
        LIKES = likes
        FOLLOWERS = followers
        REACTIONS = reactions
        COMMENTS = comments
        SHARES = shares
        create_fbpic("img.png", str(likes), str(followers), reactions, comments, shares)
        media_fbid = post_photo()["id"]
        print(update_post_data(FACEBOOK_PHOTOPOST_ID, media_fbid))


sched.start()
