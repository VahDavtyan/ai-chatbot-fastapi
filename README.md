# AI Chatbot (FastAPI + UI + Chat History)

A simple AI chatbot built with Python, FastAPI, and OpenAI API.  
Includes a web UI and per-session chat history.

## Features
- FastAPI backend with `/chat` endpoint
- In-memory chat history per `session_id`
- Web UI served at `/`
- Reset history with `/reset`

## Tech Stack
- Python
- FastAPI + Uvicorn
- OpenAI API
- dotenv

## Setup
1) Install dependencies:
```bash
pip install -r requirements.txt