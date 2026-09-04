"""
youtube_publish.py — YouTube Upload & SEO Metadata Engine for Anime Studio.

Ported from Node.js (pipeline/youtube-upload.mjs & pipeline/seo.mjs) into Python.
Features:
  1. Automated SEO title, description, and high-traffic Hindi kids' tags generation.
  2. Peak IST scheduling (8:00, 13:00, 18:00 IST -> converted precisely to UTC).
  3. COPPA compliance: status.selfDeclaredMadeForKids = True explicitly sent.
  4. Non-fatal error handling: uploads wrapped in try/except so render files remain intact on failure.
  5. OAuth2 authentication via google-api-python-client with .yt-token.json credential cache.
  6. Supports --dry-run mode for pre-flight validation without consuming API quotas.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv

load_dotenv()

# Peak IST viewing hours for Indian children's content:
# 08:00 IST (before school) -> 02:30 UTC
# 13:00 IST (after lunch)   -> 07:30 UTC
# 18:00 IST (evening play)  -> 12:30 UTC
PEAK_HOURS_IST = [8, 13, 18]

BASE_TAGS = [
    "hindi rhymes for kids", "hindi rhymes", "nursery rhymes hindi", "kids songs hindi",
    "baby songs", "hindi cartoon", "kids video", "balgeet", "hindi poem for kids",
    "rhymes for children", "toddler songs", "hindi kahani", "kids learning video",
    "cartoon for kids in hindi", "children songs", "preschool learning"
]


def ist_to_utc(year: int, month: int, day: int, hour_ist: int, minute_ist: int = 0) -> datetime:
    """
    Converts an Indian Standard Time (IST = UTC+5:30) wall-clock time into UTC datetime.
    Math: UTC = IST - 5 hours - 30 minutes.
    Example: 08:00 IST -> 02:30 UTC.
             13:00 IST -> 07:30 UTC.
    """
    ist_naive = datetime(year, month, day, hour_ist, minute_ist, 0)
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    ist_dt = ist_naive.replace(tzinfo=ist_tz)
    return ist_dt.astimezone(timezone.utc)


def next_peak_times_utc(count: int, start_from: Optional[datetime] = None) -> List[str]:
    """
    Computes the next N peak publish times in ISO-8601 UTC format.
    Starts from tomorrow morning relative to start_from (or now in UTC).
    """
    now_utc = start_from if start_from else datetime.now(timezone.utc)
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    now_ist = now_utc.astimezone(ist_tz)
    
    times = []
    day_offset = 1
    while len(times) < count:
        target_date = now_ist.date() + timedelta(days=day_offset)
        for hour in PEAK_HOURS_IST:
            if len(times) >= count:
                break
            slot_utc = ist_to_utc(target_date.year, target_date.month, target_date.day, hour, 0)
            if slot_utc > now_utc:
                times.append(slot_utc.strftime("%Y-%m-%dT%H:%M:%SZ"))
        day_offset += 1
    return times


def build_metadata(video_type: str, title: str, topic: Optional[str] = None, keywords: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Constructs high-converting SEO metadata for YouTube videos.
    """
    is_rhyme = (video_type.lower() == "rhyme")
    topic_str = topic or title
    keywords = keywords or []
    
    if is_rhyme:
        seo_title = f"{title} | Hindi Rhymes for Kids | Nursery Rhymes | Kids Songs"
        desc_lines = [
            f"{title} - A fun sing-along {topic_str} song for kids! Watch, sing and dance with us!",
            "",
            "Is video mein bacche seekhenge naye words, colors aur numbers - gaane ke saath! Perfect for toddlers, preschoolers and young children.",
            "",
            "SUBSCRIBE for new videos every day! Naye videos ke liye subscribe karein!",
            "",
            f"#HindiRhymes #KidsSongs #{''.join(c for c in title if c.isalnum())} #NurseryRhymes #HindiKahani #KidsVideo #Balgeet #CartoonForKids"
        ]
    else:
        seo_title = f"{title} | Hindi Kahani for Kids | Moral Stories | Kids Cartoon"
        desc_lines = [
            f"{title} - A beautiful animated story with a moral for kids! {topic_str}",
            "",
            "Yeh kahani bacchon ko achhi seekh deti hai. Perfect for bedtime stories and moral learning!",
            "",
            "SUBSCRIBE for new videos every day! Naye videos ke liye subscribe karein!",
            "",
            f"#HindiKahani #MoralStories #{''.join(c for c in title if c.isalnum())} #KidsCartoon #HindiStories #Balgeet #KidsStories"
        ]

    # Deduplicate tags and limit to 30
    seen = set()
    deduped_tags = []
    for t in keywords + BASE_TAGS:
        t_clean = t.strip()
        if t_clean and t_clean.lower() not in seen:
            seen.add(t_clean.lower())
            deduped_tags.append(t_clean)
            
    return {
        "title": seo_title[:100],
        "description": "\n".join(desc_lines)[:5000],
        "tags": deduped_tags[:30],
        "categoryId": "24",  # Entertainment
        "defaultLanguage": "hi",
        "defaultAudioLanguage": "hi",
        "selfDeclaredMadeForKids": True
    }


def get_youtube_client(token_path: str = ".yt-token.json"):
    """
    Initializes and returns an authenticated Google YouTube v3 client.
    """
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    
    if not os.path.exists(token_path):
        raise FileNotFoundError(
            f"YouTube credentials token not found at '{token_path}'. "
            "Please run authentication setup or ensure .yt-token.json is present."
        )
        
    with open(token_path, "r", encoding="utf-8") as f:
        token_data = json.load(f)
        
    creds = Credentials.from_authorized_user_info(token_data)
    
    client_id = os.getenv("YT_CLIENT_ID")
    client_secret = os.getenv("YT_CLIENT_SECRET")
    
    if creds.expired and creds.refresh_token and client_id and client_secret:
        from google.auth.transport.requests import Request
        creds.refresh(Request())
        with open(token_path, "w", encoding="utf-8") as f:
            f.write(creds.to_json())
            
    return build("youtube", "v3", credentials=creds)


def upload_video_to_youtube(
    video_path: str,
    title: str,
    topic: Optional[str] = None,
    video_type: str = "story",
    keywords: Optional[List[str]] = None,
    publish_at: Optional[str] = None,
    privacy_status: str = "private",
    dry_run: bool = False,
    token_path: str = ".yt-token.json"
) -> Dict[str, Any]:
    """
    Uploads a video to YouTube with scheduled publishing and MadeForKids status.
    Wraps upload in try/except so errors do not crash caller pipelines.
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
        
    meta = build_metadata(video_type=video_type, title=title, topic=topic, keywords=keywords)
    
    request_body = {
        "snippet": {
            "title": meta["title"],
            "description": meta["description"],
            "tags": meta["tags"],
            "categoryId": meta["categoryId"],
            "defaultLanguage": meta["defaultLanguage"],
            "defaultAudioLanguage": meta["defaultAudioLanguage"],
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": meta["selfDeclaredMadeForKids"],  # Explicit COPPA requirement
        }
    }
    
    if publish_at:
        request_body["status"]["publishAt"] = publish_at

    # Print request body so selfDeclaredMadeForKids can be explicitly verified in output logs
    print("\n[YouTube Upload] Prepared Video Metadata & Status:")
    print(json.dumps(request_body, indent=2))
    
    if dry_run:
        print(f"[YouTube Upload] [DRY RUN] Would upload '{video_path}' as '{meta['title']}'. Skipping API call.")
        return {
            "success": True,
            "dry_run": True,
            "video_id": "DRY_RUN_ID",
            "title": meta["title"],
            "publish_at": publish_at,
            "selfDeclaredMadeForKids": request_body["status"]["selfDeclaredMadeForKids"]
        }

    try:
        from googleapiclient.http import MediaFileUpload
        yt = get_youtube_client(token_path=token_path)
        media = MediaFileUpload(video_path, chunksize=1024*1024*4, resumable=True)
        
        print(f"[YouTube Upload] Initiating upload of {video_path}...")
        request = yt.videos().insert(
            part="snippet,status",
            body=request_body,
            media_body=media
        )
        
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"[YouTube Upload] Upload progress: {int(status.progress() * 100)}%")
                
        video_id = response.get("id")
        print(f"[YouTube Upload] [SUCCESS] Uploaded! Video URL: https://youtube.com/watch?v={video_id}")
        return {
            "success": True,
            "video_id": video_id,
            "title": meta["title"],
            "publish_at": publish_at,
            "selfDeclaredMadeForKids": True
        }
        
    except Exception as e:
        print(f"[YouTube Upload] [ERROR] Upload failed for {video_path}: {e}", file=sys.stderr)
        return {
            "success": False,
            "error": str(e),
            "video_path": video_path
        }


def main():
    parser = argparse.ArgumentParser(description="YouTube Publisher & SEO Metadata Engine for Anime Studio")
    parser.add_argument("--video", required=True, help="Path to rendered MP4 video")
    parser.add_argument("--title", required=True, help="Video title")
    parser.add_argument("--topic", help="Video topic/synopsis")
    parser.add_argument("--type", choices=["story", "rhyme"], default="story", help="Video genre")
    parser.add_argument("--publish-at", help="Scheduled publishAt ISO-8601 UTC timestamp")
    parser.add_argument("--auto-schedule", action="store_true", help="Auto-calculate next peak IST time slot")
    parser.add_argument("--dry-run", action="store_true", help="Validate request body and metadata without uploading")
    parser.add_argument("--token-path", default=".yt-token.json", help="Path to OAuth token file")
    args = parser.parse_args()
    
    publish_at = args.publish_at
    if args.auto_schedule and not publish_at:
        slots = next_peak_times_utc(1)
        publish_at = slots[0] if slots else None
        print(f"[YouTube Publish] Auto-scheduled slot (UTC): {publish_at}")
        
    result = upload_video_to_youtube(
        video_path=args.video,
        title=args.title,
        topic=args.topic,
        video_type=args.type,
        publish_at=publish_at,
        dry_run=args.dry_run,
        token_path=args.token_path
    )
    
    if not result.get("success"):
        sys.exit(1)


if __name__ == "__main__":
    main()
