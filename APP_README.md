# Chop - Automatic Viral Video Clipper

`chop.py` is a Python script that automates the process of finding and clipping viral moments from YouTube videos. It uses AI to identify engaging segments and then extracts them into short, shareable clips.

## How it Works

The script performs the following steps:

1.  **Download Video**: It takes a YouTube URL as input and downloads the corresponding video using `youtube-dl.exe`.

2.  **Download Subtitles**: It then downloads the English subtitles for the video using `yt-dlp`.

3.  **Find Viral Moment with Gemini AI**: The core of the application lies in its use of the Gemini AI. It sends the video's subtitles to the Gemini API and asks it to find a "viral moment". The script provides the following criteria to the AI for what constitutes an engaging moment:
    *   Emotional reactions (laughter, surprise, anger, excitement)
    *   Surprising facts or insights
    *   Strong or controversial opinions
    *   Clear questions with punchy answers
    *   Quotable lines that stand on their own

    The AI is instructed to find a single clip that is 10-30 seconds long.

4.  **Save Clip Information**: The start time, end time, and a brief reason for why the moment is engaging (as determined by the AI) are saved into a file named `viral_clip.txt`.

5.  **Extract Clip**: Finally, the script uses `ffmpeg` to cut the identified segment from the original video file. The resulting clip is saved as `clip.mp4`.

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

The script will prompt you to enter a YouTube URL. After you provide the URL, it will execute the steps outlined above and, if successful, you will find a `clip.mp4` file in the same directory.
