# Ollama setup — quick guide

This project does not use an OpenAI API key.

## 1. Install Ollama

Download Ollama from the official website and install it.

## 2. Open a NEW terminal

Run:

```bash
ollama --version
```

## 3. Download the model

```bash
ollama pull llama3.2:3b
```

The model is stored locally on your computer.

## 4. Check that Ollama can see it

```bash
ollama list
```

You should see `llama3.2:3b`.

## 5. Start the model manually once (optional test)

```bash
ollama run llama3.2:3b
```

Type:

```text
Say hello in one sentence.
```

If it responds, press Ctrl+C to exit.

## 6. Run the Meeting Summarizer

In the project terminal:

```bash
venv\Scripts\activate
uvicorn app.main:app --reload
```

Then open:

```text
http://127.0.0.1:8000
```

The first transcription can take longer because Faster-Whisper downloads its model. After that, processing should be faster.
