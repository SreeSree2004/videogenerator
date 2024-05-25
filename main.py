from functions import *
from audio import *
from addsubtitles import *
from youtube import *

# conda activate reddit

def main(url, title):
    
   submission = start(url)
   location = f"videos/{submission.title}/{submission.title}_final.mp4"
   output_location = f"videos/{submission.title}/subtitled.mp4"
   
   create_title_voice_over_tiktok(submission.title, submission.title)
   add_text_to_image(submission.title)
   resize_image_width(f"videos/{submission.title}/{submission.title}.png", f"videos/{submission.title}/{submission.title}.png")
   create_movie_with_background_na(submission.title)
   subtitled_location = subtitles(location, output_location)
   link = youtube(subtitled_location, f"{title}", "reddit", 10, "reddit, funny, shorts", "public", False)
   return location, link


main("https://www.reddit.com/r/AskReddit/comments/1c7vpsu/what_viral_video_is_fake_but_people_think_its_real/", "#shorts")