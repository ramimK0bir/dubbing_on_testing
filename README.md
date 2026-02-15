- It's a simple video dubbing tool.
- Use whisper to transcribe.
- Use pydub and ffmpeg for video processing.
- Use deep deep_translator to translate.
- Use gTTS genarate voice from text.
  

# Requirements
- python 3.12 or older.
- ffmpeg

# Installation


1. **Clone the repo**
```bash
git clone https://github.com/ramimK0bir/dubbing.git
```

2.**GO to the directory**
```bash
cd dubbing
```

3.**Install requirements**
```bash
pip install -r requirements.txt
```

4.**Run main.py**
```bash
python main.py --input ./test.mp4 --lang hi --output output.mp4
```

# Google Colab Recommendation

Use [Google Colab](https://colab.research.google.com/github/ramimK0bir/dubbing/blob/main/Dubbing.ipynb) for a better coding experience:  
- Faster execution with free GPU/TPU resources  
- Easy access to Python and machine learning libraries  
- Seamless cloud-based workflow with no local setup required  
- Simple sharing and collaboration via links  

*(Replace the link above with your own Colab, GitHub, or notebook link.)*



# Arguments
When running main.py, you can pass the following arguments:

| Argument | Type   | Required | Description |
|----------|--------|----------|-------------|
| --input  | string | yes      | Filepath of input file |
| --output | string | yes      | Filepath of output file |
| --lang   | string | yes      | Target language short code (e.g., es, hi, bn, ru) |

Example usage:
python main.py --input data.txt --output out.txt --lang es



