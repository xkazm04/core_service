# Agentic workflow

# Goal
Need a mechanism to 
- Evaluate data about the story, characters, progress
- Generate valid ideas based on the evaluation

## Use cases | Data store | Tools

### A. Ideas for beats | DB | RAG vs Context window
1. Inputs - Compose information for chat completion
- Story description from DB 
- Beats from DB
- Prompt instruction

2. Process via chat completion (context window)
- Benefit of memory
- Downside of llama model usage - precision

3. Formatted output

### B. Act script
### C. Critique script

## Co dál ?
1. Langchain - Postgres - Longterm memory
- FastAPI - Initiation automatically
- SSE - Push notification
- Postgres - Store notifivations
