import subprocess
import os
import glob
import re
import argparse
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

def find_latest_file(directory, extension):
    """Finds the most recently created file with a given extension."""
    list_of_files = glob.glob(os.path.join(directory, f'*.{extension}'))
    if not list_of_files:
        return None
    latest_file = max(list_of_files, key=os.path.getctime)
    return latest_file

def convert_srt_time_to_ffmpeg(srt_time):
    """Converts SRT timestamp format (00:00:00,000) to FFmpeg format (00:00:00.000)."""
    return srt_time.replace(',', '.')

def sanitize_filename(filename):
    """Removes invalid characters from a filename."""
    return re.sub(r'[\\/*?:",<>|]', "", filename)

def srt_time_to_seconds(time_str):
    """Converts SRT time string HH:MM:SS,ms or HH:MM:SS.ms to seconds."""
    parts = time_str.replace(',', '.').split(':')
    if len(parts) == 3:
        try:
            seconds = float(parts[2])
            minutes = int(parts[1])
            hours = int(parts[0])
            return hours * 3600 + minutes * 60 + seconds
        except ValueError:
            return 0.0
    return 0.0

def seconds_to_srt_time(seconds):
    """Converts seconds to SRT time string HH:MM:SS,ms."""
    if seconds < 0:
        seconds = 0
    hours = int(seconds // 3600)
    seconds %= 3600
    minutes = int(seconds // 60)
    seconds %= 60
    milliseconds = int((seconds - int(seconds)) * 1000)
    seconds = int(seconds)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

def parse_srt(srt_content):
    """Parses SRT content and returns a list of subtitle blocks."""
    subtitle_blocks = srt_content.strip().split('\n\n')
    subtitles = []
    for block in subtitle_blocks:
        lines = block.split('\n')
        if len(lines) >= 3:
            try:
                index = int(lines[0])
                time_line = lines[1]
                start_str, end_str = [t.strip() for t in time_line.split('-->')]
                text = '\n'.join(lines[2:])
                subtitles.append({
                    'index': index,
                    'start': start_str,
                    'end': end_str,
                    'text': text
                })
            except (ValueError, IndexError):
                # Skip malformed blocks
                print(f"Skipping malformed SRT block: {block}")
                continue
    return subtitles

def main():
    """Main function to run the video clipping process."""
    parser = argparse.ArgumentParser(description="Automatically find viral moments in a YouTube video and clip them.")
    parser.add_argument('--url', required=True, help="The URL of the YouTube video.")
    parser.add_argument('--clips', required=True, type=int, help="The number of clips to generate.")
    
    args = parser.parse_args()
    
    youtube_url = args.url
    num_clips = args.clips

    if num_clips <= 0:
        print("Error: The number of clips must be a positive integer.")
        return

    # --- Get Video Title ---
    print("\n--- Getting Video Title ---")
    title_command = ['yt-dlp', '--get-title', youtube_url]
    success, video_title = run_command(title_command)
    if not success:
        print("Failed to get video title. Exiting.")
        return
    video_title = video_title.strip()
    sanitized_title = sanitize_filename(video_title)
    
    # --- Create output directory ---
    output_dir = os.path.join('output', sanitized_title)
    os.makedirs(output_dir, exist_ok=True)
    print(f"Created output directory: {output_dir}")
    
    # --- STEP 1: Download Video ---
    print("\n--- Step 1: Downloading Video ---")
    video_path = os.path.join(output_dir, f"{sanitized_title}.mp4")
    video_command = [
        'yt-dlp',
        '-f', 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        '-o', video_path,
        youtube_url
    ]
    success, _ = run_command(video_command)
    if not success:
        print("Failed to download video. Exiting.")
        return
    print(f"Found video file: {video_path}")

    # --- STEP 2: Download Subtitles ---
    print("\n--- Step 2: Downloading Subtitles ---")
    subtitle_command = [
        'yt-dlp',
        '--write-auto-subs',
        '--sub-lang', 'en',
        '--sub-format', 'srt',
        '--skip-download',
        '-o', os.path.join(output_dir, f"{sanitized_title}.%(ext)s"),
        youtube_url
    ]
    success, _ = run_command(subtitle_command)
    if not success:
        print("Failed to download subtitles. Exiting.")
        return

    subtitle_file = find_latest_file(output_dir, 'en.srt')
    if not subtitle_file:
        print("Could not find the downloaded subtitle file (.srt). Exiting.")
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
            if len(lines) < 2:
                print(f"Skipping invalid clip chunk: {clip}")
                continue
            time_line = lines[0]
            reason_line = lines[1]
            
            try:
                start_time, end_time = [t.strip() for t in time_line.replace('[', '').replace(']', '').split('→')]
                reason = reason_line.replace('Reason:', '').strip()

                start_time_ffmpeg = convert_srt_time_to_ffmpeg(start_time)
                end_time_ffmpeg = convert_srt_time_to_ffmpeg(end_time)

                clip_details.append({'start': start_time_ffmpeg, 'end': end_time_ffmpeg, 'reason': reason})
            except ValueError:
                print(f"Could not parse time from line: {time_line}")
                continue

    except Exception as e:
        print(f"Error getting response from Gemini AI: {e}")
        return

    with open(os.path.join(output_dir, "viral_clips.txt"), "w", encoding="utf-8") as f:
        f.write(clip_info_text)
    print("Successfully created viral_clips.txt with content from Gemini AI:")
    print(clip_info_text)


    # --- STEP 4: Extract Clips and Generate Individual SRTs ---
    print(f"\n--- Step 4: Extracting {len(clip_details)} Clips with FFmpeg and Generating SRTs ---")

    all_subtitles = parse_srt(subtitle_content)

    for i, clip in enumerate(clip_details):
        clip_num = i + 1
        clip_start_seconds = srt_time_to_seconds(clip['start'])
        clip_end_seconds = srt_time_to_seconds(clip['end'])

        # Create a directory for each clip
        clip_dir = os.path.join(output_dir, f"clip_{clip_num}")
        os.makedirs(clip_dir, exist_ok=True)

        output_video_path = os.path.join(clip_dir, f"clip_{clip_num}.mp4")
        output_srt_path = os.path.join(clip_dir, f"clip_{clip_num}.srt")

        print(f"\nExtracting clip {clip_num} to {output_video_path}...")
        ffmpeg_command = [
            'ffmpeg',
            '-ss', clip['start'],
            '-to', clip['end'],
            '-i', video_path,
            '-c', 'copy',
            output_video_path
        ]

        success, _ = run_command(ffmpeg_command)
        if not success:
            print(f"Failed to extract clip {clip_num} with FFmpeg.")
            continue # Move to the next clip
        else:
            print(f"Successfully extracted clip {clip_num}.")

        # --- Generate individual SRT for the clip ---
        print(f"Generating SRT file for clip {clip_num}...")
        clip_subtitles = []
        for sub in all_subtitles:
            sub_start_seconds = srt_time_to_seconds(sub['start'])
            sub_end_seconds = srt_time_to_seconds(sub['end'])

            # Check if the subtitle is within the clip's time range
            if sub_start_seconds >= clip_start_seconds and sub_end_seconds <= clip_end_seconds:
                # Adjust timestamps to be relative to the clip's start time
                new_start_seconds = sub_start_seconds - clip_start_seconds
                new_end_seconds = sub_end_seconds - clip_start_seconds

                clip_subtitles.append({
                    'start': seconds_to_srt_time(new_start_seconds),
                    'end': seconds_to_srt_time(new_end_seconds),
                    'text': sub['text']
                })

        # Write the new SRT file
        with open(output_srt_path, 'w', encoding='utf-8') as f:
            for j, sub in enumerate(clip_subtitles):
                f.write(f"{j+1}\n")
                f.write(f"{sub['start']} --> {sub['end']}\n")
                f.write(f"{sub['text']}\n\n")

        print(f"Successfully created SRT file: {output_srt_path}")

    # --- Clean up temporary files ---
    print("\n--- Cleaning up temporary files ---")
    try:
        os.remove(subtitle_file)
        print(f"Removed temporary subtitle file: {subtitle_file}")
        viral_clips_path = os.path.join(output_dir, "viral_clips.txt")
        os.remove(viral_clips_path)
        print(f"Removed temporary clips info file: {viral_clips_path}")
    except OSError as e:
        print(f"Error during cleanup: {e}")

    print(f"\nProcess complete! Your clips and subtitles have been saved in '{output_dir}'")

if __name__ == "__main__":
    main()
