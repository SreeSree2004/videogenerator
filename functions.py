import os
import re
import praw
import time
from gtts import gTTS
import pyttsx3
import random
import asyncio
import openai
import re
from dotenv import load_dotenv
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip
from moviepy.editor import CompositeVideoClip, concatenate_videoclips, TextClip, concatenate_audioclips
from audio import tts
from PIL import Image, ImageDraw, ImageFont

# creates reddit api instance

def __getReddit():
    return praw.Reddit(
    client_id="7ZVYF9ql3kia1JhjoKOoXg",
    client_secret="3hP2IAIIZHIH75gJzCJ_FlL75mi7CA",
    user_agent="mer by u/merry-git",
) 
    
# picks a comment and creates a voice over for it
    
def start(url):
    reddit = __getReddit()
    submission = reddit.submission(url=url)
    submission.comment_sort = 'best'
    good_comments = []
    comment_ids = []
    count = 0
    submission.comments.replace_more(limit=0)
    top_comments = submission.comments.list()[:444]
    
    location = f"videos/{submission.title}/{submission.title}_final.mp4"
    for comment in top_comments:
        if count >= 7:
            print(f"max comments reached: {count}")
            print(f"the length of the comment array is {len(good_comments)}")
            break
        if 500 < len(comment.body) < 700:
            good_comments.append(comment.body)
            comment_ids.append(comment.id)
            count += 1

    count = 1
    for comment in good_comments:
        if count > 1:
            print("generating audio: max comments reached (1)")
            break
        create_voice_over_tiktok(submission.title, count, comment)
        count += 1
        
    print("Done!")
    return submission

# creates the voice over for any text

def create_voice_over_tiktok(title, count, text):
    dir_name = f"videos/{title}"
    voice_options = ["en_us_006"]
    selected_voice = random.choice(voice_options)

    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    file_name = f"{dir_name}/{count}.mp3"
    
    if os.path.exists(file_name):
        print(f"{count}.mp3 already exists")
        return

    print(f"Saving voice-over to {file_name}")
    
    tts(text, selected_voice, file_name, play_sound=False)
    
    return file_name

# create title voice over

def create_title_voice_over_tiktok(directory, text):
    file_path = f"videos/{directory}/title.mp3"
    
    print(f"Saving MP3 to {file_path}")
    
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    if os.path.exists(file_path):
        print("title mp3 already exists")
        return
    
    tts(text, "en_us_006", file_path, play_sound=False)
    
    return

# resizes the image to fit the video

def resize_image_width(image_path, output_path):
    original_image = Image.open(image_path)
    target_width = 760
    
    aspect_ratio = original_image.height / original_image.width
    new_height = int(target_width * aspect_ratio)
    resized_image = original_image.resize((target_width, new_height), Image.Resampling.LANCZOS)
    resized_image.save(output_path)
    print(f"Resized image saved to {output_path}")
    
# creates the video with the voice over and background video
    
def create_movie_with_background_na(directory_name):
    directory_path = f"videos/{directory_name}"
    background_video_path = f"assets/mc!.mp4"
    output_video_path = f"{directory_path}/{directory_name}_final.mp4"

    os.makedirs(directory_path, exist_ok=True)
    gta_clip = VideoFileClip(background_video_path).without_audio()
    title_audio_clip = AudioFileClip(f"{directory_path}/title.mp3")
    silent_clip_gap = AudioFileClip(f"assets/silence.mp3")

    audio_clips = [title_audio_clip, silent_clip_gap]
    for i in range(1, 2):
        audio_clip = AudioFileClip(f"{directory_path}/{i}.mp3")
        audio_clips += [audio_clip, silent_clip_gap]
    
    final_audio_duration = sum(clip.duration for clip in audio_clips)
    max_start = gta_clip.duration - final_audio_duration
    random_start = random.uniform(0, max_start)
    background_clip = gta_clip.subclip(random_start, random_start + final_audio_duration)
    
    title_image_clip = ImageClip(f"{directory_path}/{directory_name}.png", duration=title_audio_clip.duration).set_position("center")
    title_image_clip = title_image_clip.set_position(("center", 0.25), relative=True)
    final_audio = concatenate_audioclips(audio_clips)
    final_clip = CompositeVideoClip([background_clip, title_image_clip.set_start(0)], size=gta_clip.size).set_audio(final_audio)
    final_clip.write_videofile(output_video_path, codec="libx264", audio_codec='aac', preset='ultrafast', threads=4)

    print(f"Video saved to {output_video_path}")
    
# adds text to image for the video
    
def add_text_to_image(title):
    template_path = "assets/starter.png"
    top_margin = 170
    left_margin = 100
    line_length = 40
    line_spacing = 10
    
    image = Image.open(template_path)
    draw = ImageDraw.Draw(image)

    # Choose a font and size
    font_size = 22
    font = ImageFont.truetype("assets/arialbold.ttf", font_size)

    # Starting position of the text (left margin)
    x = left_margin
    y = top_margin

    # Split the text into lines
    lines = []
    words = title.split()
    current_line = ''
    for word in words:
        # Check if adding the word would exceed the line length
        if len(current_line) + len(word) + 1 <= line_length:
            current_line += word + ' '
        else:
            lines.append(current_line)
            current_line = word + ' '
    lines.append(current_line)  # Add the last line

    # Add the text to the image, line by line
    for line in lines:
        # Use textbbox to get the bounding box and calculate text height
        bbox = draw.textbbox((x, y), line, font=font)
        text_height = bbox[3] - bbox[1]

        draw.text((x, y), line, font=font, fill="black")
        y += text_height + line_spacing

    # Save the edited image
    output_path = f'videos/{title}/{title}.png'
    image.save(output_path)

    return output_path