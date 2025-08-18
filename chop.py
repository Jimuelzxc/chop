import subprocess
import os
import glob
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def run_command(command):
    """Runs a command in the shell and prints its output."""
    print(f"Executing: {' '.join(command)}")
    result = subprocess.run(command, capture_output=True, text=True, shell=True)
    if result.returncode != 0:
        print("Error:")
        print(result.stderr)
        return False, None
    print("Success!")
    # print(result.stdout) # Uncomment for debugging
    return True, result.stdout

def find_latest_file(extension):
    """Finds the most recently created file with a given extension."""
    list_of_files = glob.glob(f'*.{extension}')
    if not list_of_files:
        return None
    latest_file = max(list_of_files, key=os.path.getctime)
    return latest_file

def main():
    """Main function to run the video clipping process."""
    youtube_url = input("Please enter the YouTube URL: ")
    
    while True:
        try:
            num_clips_str = input("How many clips would you like to generate? (e.g., 1-5): ")
            num_clips = int(num_clips_str)
            if num_clips > 0:
                break
            else:
                print("Please enter a positive number.")
        except ValueError:
            print("Invalid input. Please enter a number.")
    
    # --- STEP 1: Download Video ---
    print("\n--- Step 1: Downloading Video ---")
    video_command = [
        'youtube-dl.exe',
        youtube_url
    ]
    success, _ = run_command(video_command)
    if not success:
        print("Failed to download video. Exiting.")
        return

    video_filename = find_latest_file('mp4')
    if not video_filename:
        video_filename = find_latest_file('webm') # Fallback for webm
    if not video_filename:
        print("Could not find the downloaded video file (.mp4 or .webm). Exiting.")
        return
    print(f"Found video file: {video_filename}")

    # --- STEP 2: Download Subtitles ---
    print("\n--- Step 2: Downloading Subtitles ---")
    subtitle_command = [
        'yt-dlp',
        '--write-auto-subs',
        '--sub-lang', 'en',
        '--skip-download',
        '-o', '"%(title)s.%(ext)s"',
        youtube_url
    ]
    success, _ = run_command(subtitle_command)
    if not success:
        print("Failed to download subtitles. Exiting.")
        return

    subtitle_file = find_latest_file('en.vtt')
    if not subtitle_file:
        print("Could not find the downloaded subtitle file (.vtt). Exiting.")
        return
        
    print(f"Found subtitle file: {subtitle_file}")

    # --- STEP 3: Get Viral Moment from Gemini ---
    print("\n--- Step 3: Finding The Viral Moment with Gemini AI ---")
    
    try:
        with open(subtitle_file, 'r', encoding='utf-8') as f:
            subtitle_content = f.read()
    except FileNotFoundError:
        print(f"Error: The subtitle file '{subtitle_file}' was not found.")
        return

    # Configure the Gemini AI client
    # The client gets the API key from the environment variable `GEMINI_API_KEY`.
    try:
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        model = genai.GenerativeModel('gemini-2.5-flash')
    except Exception as e:
        print(f"Error configuring Gemini AI: {e}")
        print("Please make sure you have set the GEMINI_API_KEY environment variable.")
        return

    prompt = f"""
You are an expert short-form video editor.
Your job is to find {num_clips} viral moments inside a long-form transcript with timestamps.
Each chosen clip must be 10-30 seconds long.

Criteria for engaging moments:
- Emotional reactions (laughter, surprise, anger, excitement)
- Surprising facts or insights
- Strong or controversial opinions
- Clear questions with punchy answers
- Quotable lines that stand on their own

Instructions:
1. Read the following transcript carefully.
2. Select {num_clips} clips.
3. Each clip length must be between 10-30 seconds.
4. Output format must be ONLY, with each clip separated by '---':
[Start time] → [End time]
Reason: [Why this moment is engaging, max 2 sentences]
---
[Start time] → [End time]
Reason: [Why this moment is engaging, max 2 sentences]

Transcript:
{subtitle_content}
"""

    print(f"Asking Gemini AI to find {num_clips} viral moments...")
    try:
        response = model.generate_content(prompt)
        clip_info_text = response.text
        
        clips = clip_info_text.strip().split('---')
        
        clip_details = []
        for clip in clips:
            if not clip.strip():
                continue
            lines = clip.strip().split('\n')
            time_line = lines[0]
            reason_line = lines[1]
            
            start_time, end_time = [t.strip() for t in time_line.replace('[', '').replace(']', '').split('→')]
            reason = reason_line.replace('Reason:', '').strip()
            clip_details.append({'start': start_time, 'end': end_time, 'reason': reason})

    except Exception as e:
        print(f"Error getting response from Gemini AI: {e}")
        return

    with open("viral_clips.txt", "w", encoding="utf-8") as f:
        f.write(clip_info_text)
    print("Successfully created viral_clips.txt with content from Gemini AI:")
    print(clip_info_text)


    # --- STEP 4: Extract Clips with FFmpeg ---
    print(f"\n--- Step 4: Extracting {len(clip_details)} Clips with FFmpeg ---")
    
    for i, clip in enumerate(clip_details):
        output_filename = f"clip_{i+1}.mp4"
        print(f"\nExtracting clip {i+1} to {output_filename}...")
        ffmpeg_command = [
            'ffmpeg',
            '-ss', clip['start'],
            '-to', clip['end'],
            '-i', video_filename,
            '-c', 'copy',
            output_filename
        ]
        
        success, _ = run_command(ffmpeg_command)
        if not success:
            print(f"Failed to extract clip {i+1} with FFmpeg.")
        else:
            print(f"Successfully extracted clip {i+1}.")
        
    print(f"\nProcess complete! Your clips have been saved.")

if __name__ == "__main__":
    main()
