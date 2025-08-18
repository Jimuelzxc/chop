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
Your job is to find a single viral moment inside a long-form transcript with timestamps.
The chosen clip must be 10-30 seconds long.

Criteria for engaging moments:
- Emotional reactions (laughter, surprise, anger, excitement)
- Surprising facts or insights
- Strong or controversial opinions
- Clear questions with punchy answers
- Quotable lines that stand on their own

Instructions:
1. Read the following transcript carefully.
2. Select only ONE clip.
3. Clip length must be between 10-30 seconds.
4. Output format must be ONLY:
[Start time] → [End time]
Reason: [Why this moment is engaging, max 2 sentences]

Transcript:
{subtitle_content}
"""

    print("Asking Gemini AI to find a viral moment...")
    try:
        response = model.generate_content(prompt)
        clip_info = response.text
        
        # Parse start_time, end_time, and reason from the response
        lines = clip_info.strip().split('\n')
        time_line = lines[0]
        reason_line = lines[1]
        
        start_time, end_time = [t.strip() for t in time_line.replace('[', '').replace(']', '').split('→')]
        reason = reason_line.replace('Reason:', '').strip()

    except Exception as e:
        print(f"Error getting response from Gemini AI: {e}")
        return

    with open("viral_clip.txt", "w", encoding="utf-8") as f:
        f.write(clip_info)
    print("Successfully created viral_clip.txt with content from Gemini AI:")
    print(clip_info)


    # --- STEP 4: Extract Clip with FFmpeg ---
    print("\n--- Step 4: Extracting Clip with FFmpeg ---")
    output_filename = "clip.mp4"
    ffmpeg_command = [
        'ffmpeg',
        '-ss', start_time,
        '-to', end_time,
        '-i', video_filename,
        '-c', 'copy',
        output_filename
    ]
    
    success, _ = run_command(ffmpeg_command)
    if not success:
        print("Failed to extract clip with FFmpeg.")
        return
        
    print(f"\nProcess complete! Your clip has been saved as '{output_filename}'")

if __name__ == "__main__":
    main()
