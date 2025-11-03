# 🧩 FastAPI JIRA Insights Service

This project is a **FastAPI-based microservice** that integrates with **JIRA** to fetch, process, and serve insights such as work estimates, work logs, and sprint-level analytics. It is fully containerized using Docker and can be deployed easily in any environment supporting containers.

---

## 📁 Project Structure

```
.
├── Dockerfile
├── requirements.txt
└── main.py
```

---

## 🚀 Features

- Connects securely to **JIRA Cloud or Server** using API tokens.
- Provides REST APIs for:
  - Fetching JIRA issue details.
  - Calculating work estimates and logged efforts.
  - Generating sprint-level insights.
- Lightweight and production-ready using **FastAPI** + **Uvicorn**.
- Configurable through environment variables.

---

## ⚙️ Prerequisites

- **Python 3.12+**
- **Docker** installed locally
- A valid **JIRA account** and **API token**

---

## 🧠 Environment Variables

Before running the app, set the following environment variables:

| Variable | Description |
|-----------|-------------|
| `JIRA_SERVER` | JIRA server URL (e.g. `https://yourcompany.atlassian.net`) |
| `JIRA_EMAIL` | Your JIRA user email |
| `JIRA_API_TOKEN` | API token generated from your Atlassian account |

Example:
```bash
export JIRA_SERVER="https://yourcompany.atlassian.net"
export JIRA_EMAIL="user@example.com"
export JIRA_API_TOKEN="your_api_token_here"
```

---

## 🐍 Running Locally (Without Docker)

```bash
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

Then open [http://localhost:8080/docs](http://localhost:8080/docs) to view the interactive Swagger UI.

---

## 🐳 Running with Docker

### 1️⃣ Build the image
```bash
docker build -t fastapi-jira-insights .
```

### 2️⃣ Run the container
```bash
docker run -d   -p 8080:8080   -e JIRA_SERVER="https://yourcompany.atlassian.net"   -e JIRA_EMAIL="user@example.com"   -e JIRA_API_TOKEN="your_api_token_here"   fastapi-jira-insights
```

The API will be available at:
👉 **http://localhost:8080**

Swagger UI:
👉 **http://localhost:8080/docs**

---

## 📘 Example Endpoints

- `GET /jira/work/estimates` — Returns work estimates by issue.
- `GET /jira/work/logs` — Returns work log summaries.
- `GET /jira/insights/sprint/{sprint_id}` — Returns sprint insights.

*(Actual endpoints may vary based on your implementation in `main.py`.)*

---

## 🧾 Dependencies

See [`requirements.txt`](./requirements.txt):
```
fastapi
uvicorn
requests
python-dotenv
pydantic
```

---

## 🧰 Tech Stack

- **FastAPI** – modern async web framework for Python.
- **Uvicorn** – lightning-fast ASGI server.
- **Docker** – containerization for portability.
- **Pydantic** – for data validation and response models.
- **JIRA Python SDK** – for integration with JIRA REST APIs.

---

## 🧩 License

This project is licensed under the [MIT License](LICENSE).

---

## 🤝 Contributing

1. Fork the repository  
2. Create your feature branch (`git checkout -b feature/new-feature`)  
3. Commit your changes (`git commit -m 'Add new feature'`)  
4. Push to the branch (`git push origin feature/new-feature`)  
5. Open a Pull Request  

---

## 📬 Contact

For questions or feedback, please reach out via the repository’s **Issues** or **Discussions** tab.

---
