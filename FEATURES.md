# Future Feature Ideas for `chop.py`

This document lists potential features to enhance the functionality and user experience of the video clipping tool.

## Core Improvements

### 1. Command-Line Arguments
- **Description:** Replace the interactive `input()` prompts with command-line arguments for a non-interactive workflow.
- **Example:** `python chop.py --url "<youtube_url>" --clips <num_clips>`
- **Benefits:**
    - Enables automation and scripting.
    - Faster for repeated use.
    - Foundation for other advanced features.
- **Implementation:** Use Python's `argparse` library.

## Advanced Features

### 2. Batch Processing from a File
- **Description:** Add an argument to accept a text file containing multiple YouTube URLs, with one URL per line. The script would process all of them in a single run.
- **Example:** `python chop.py --input-file urls.txt`
- **Benefits:**
    - Highly efficient for processing large numbers of videos.
    - Allows users to queue up work.

### 3. Custom AI Prompt
- **Description:** Allow the user to provide their own prompt for the AI to find specific types of moments (e.g., funny, educational, controversial). This could be done via a command-line string or by pointing to a prompt file.
- **Example:**
    - `python chop.py --url "..." --prompt "Find the three most technically detailed moments."`
    - `python chop.py --url "..." --prompt-file my_prompt.txt`
- **Benefits:**
    - Gives the user full creative control over the content curation.
    - Makes the tool adaptable to different content needs.

### 4. "Dry Run" Mode
- **Description:** Add a `--dry-run` flag that will execute the script without downloading the video or cutting the clips. It will only fetch the subtitles, query the AI, and print the proposed timestamps and reasons.
- **Example:** `python chop.py --url "..." --dry-run`
- **Benefits:**
    - Saves significant time and bandwidth.
    - Allows for a quick preview of the AI's suggestions before committing to the full process.

### 5. AI Virality Scoring
- **Description:** After identifying potential clips, use a second AI prompt to score each clip's "virality potential" on a scale of 1-10. The script could then automatically select the highest-scoring clips or present the scores to the user for a final decision.
- **Example Argument:** `python chop.py --url "..." --score-clips`

### 6. Interactive Clip Selection Mode
- **Description:** After the AI suggests clips (similar to a `--dry-run`), present them in a numbered list and allow the user to interactively select which ones to render into final video files.
- **Example Argument:** `python chop.py --url "..." --interactive`
