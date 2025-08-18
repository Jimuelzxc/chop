# Chop - Automatic Viral Video Clipper

`chop.py` is a Python script that automates the process of finding and clipping viral moments from YouTube videos. It uses AI to identify engaging segments and then extracts them into short, shareable clips.

## How it Works

The script performs the following steps:

1.  **User Input**: It prompts the user for a YouTube URL and the desired number of clips to generate.

2.  **Download Video**: It takes the YouTube URL as input and downloads the corresponding video using `youtube-dl.exe`.

3.  **Download Subtitles**: It then downloads the English subtitles for the video in SRT format using `yt-dlp`.

4.  **Find Viral Moments with Gemini AI**: The core of the application lies in its use of the Gemini AI. It sends the video's subtitles to the Gemini API and asks it to find a specified number of "viral moments". The script provides the following criteria to the AI for what constitutes an engaging moment:
    *   Emotional reactions (laughter, surprise, anger, excitement)
    *   Surprising facts or insights
    *   Strong or controversial opinions
    *   Clear questions with punchy answers
    *   Quotable lines that stand on their own

    The AI is instructed to find clips that are 10-30 seconds long.

5.  **Save Clip Information**: The start times, end times, and brief reasons for why each moment is engaging (as determined by the AI) are saved into a file named `viral_clips.txt`.

6.  **Extract Clips**: Finally, the script uses `ffmpeg` to cut the identified segments from the original video file. The resulting clips are saved as `clip_1.mp4`, `clip_2.mp4`, and so on.

## Dependencies

The script relies on the following external tools and libraries:

*   `youtube-dl.exe`
*   `yt-dlp`
*   `ffmpeg`
*   `google-generativeai` (Python library)
*   `python-dotenv` (Python library)

## Usage

To run the script, you need to have Python installed, along with the necessary dependencies. You will also need to set up a `GEMINI_API_KEY` environment variable with your API key for the Gemini AI service.

Then, you can run the script from your terminal:

```bash
python chop.py
```

The script will prompt you to enter a YouTube URL and how many clips you want. After you provide the information, it will execute the steps outlined above. If successful, it will create a directory named after the video's title in the 'output' folder. Inside this directory, you will find a separate folder for each clip (e.g., `clip_1`, `clip_2`), each containing the video clip and its corresponding SRT subtitle file.
