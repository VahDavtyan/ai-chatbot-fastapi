# AI Chatbot (FastAPI + OpenAI + Web UI)

A production-style Generative AI chatbot built with Python, FastAPI, and OpenAI API.

This project demonstrates:

- Backend API development with FastAPI
- Integration with modern LLM APIs (OpenAI)
- Session-based chat memory
- Interactive browser-based UI

Built as a portfolio project for AI / Python Engineering roles.

---

## Features

- FastAPI backend with REST endpoints
- OpenAI GPT model integration
- Session-based chat history
- Interactive web interface
- Reset chat per session
- Health check endpoint (`/health`)
- Automatic API docs (`/docs`)

---

## Tech Stack

- Python
- FastAPI
- Uvicorn
- OpenAI API
- python-dotenv
- HTML / CSS / JavaScript

---

## Project Structure


ai-chatbot-fastapi/
│
├── app.py
├── requirements.txt
├── .env
├── .gitignore
└── README.md


---

## Setup & Run

### 1. Clone repository


git clone https://github.com/VahDavtyan/ai-chatbot-fastapi.git

cd ai-chatbot-fastapi

---

### 2. Install dependencies


py -m pip install -r requirements.txt


or


python -m pip install -r requirements.txt


---

### 3. Create `.env` file

Create a file named `.env` in the project folder:


OPENAI_API_KEY=your_api_key_here
MODEL=gpt-4o-mini


Get API key from:

https://platform.openai.com/api-keys

---

### 4. Run server


py -m uvicorn app:app --reload

Server will run at:

http://127.0.0.1:8000


---

## Usage

### Web Interface

Open in browser:


http://127.0.0.1:8000


Chat with the AI using the web interface.

---

### API Documentation


http://127.0.0.1:8000/docs


Interactive Swagger API docs.

---

### Health Check


http://127.0.0.1:8000/health


Returns:


{
"status": "ok",
"model": "gpt-4o-mini"
}


---

## Example API Request

POST `/chat`


{
"session_id": "test-session",
"message": "Hi",
"max_history": 10
}


---

## What this project demonstrates

- FastAPI backend development
- OpenAI API integration
- Generative AI application development
- Session-based state management
- Clean project structure

---

## Author

Vahag