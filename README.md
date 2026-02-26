# 🧠 Spotter — ML based AI Ad Detection Extension

Spotter is a full-stack project that detects whether selected text contains promotional or advertisement-like content.
It combines a Chrome Extension UI, a FastAPI backend, and a dedicated ML inference server powered by a PyTorch model.

The system is designed to be **fast, modular, and continuously improving** through user feedback and periodic model training.

## Warning : it only works with Korean review/text

# Examples
For example, Spotter was tested on the following dining review website (https://www.diningcode.com/profile.php?rid=hAebbrQ1gHyi)

Popup view after pressing 'Analyze' button:
![Popup analysis](assets/screenshots/Screenshot%202026-02-26%20at%2012.12.03.png)

Feedback homepage:
![Progress and summary](assets/screenshots/Screenshot%202026-02-26%20at%2012.12.42.png)

Feedback page (User can rate the text):
![Progress and summary](assets/screenshots/Screenshot%202026-02-26%20at%2012.12.50.png)

---

# 🚀 Features

* Detect advertisement probability from highlighted text
* Lightweight API server with caching support
* Dedicated ML server for efficient inference
* Feedback-based training pipeline
* Automatic loading of the latest model version

---

# 🧩 Architecture Overview

```
Chrome Extension
        ↓
API Server (FastAPI)
        ↓
ML Server (PyTorch Inference)
        ↓
Model Weights
```

### Why separate API and ML servers?

* API server stays lightweight and responsive
* ML model loads only once inside the ML server
* Training can run independently without stopping the API

---

# 📁 Project Structure

```
Spotter/
│
├── api-server/          # FastAPI backend
│   ├── routes/
│   ├── services/
│   ├── ml_client.py
│   └── main.py
│
├── ml-server/           # Model inference server
│   ├── inference.py
│   ├── model.py
│   ├── preprocess.py
│   └── models/
│        ├── model_v1.pth
│        ├── model_v2.pth
│        └── cc.ko.300.bin
│
├── trainer/             # Training pipeline (runs separately)
│   ├── train.py
│   └── build_dataset.py
│
├── extension/           # Chrome extension UI
│
└── docker-compose.yml
```

---

# ⚙️ Tech Stack

**Backend**

* FastAPI
* PostgreSQL (feedback storage)
* Redis or in-memory cache

**Machine Learning**

* PyTorch
* LSTM + Attention model
* FastText embeddings

**Frontend**

* Chrome Extension (Vanilla JS)

---

# 🧪 How It Works

## 1️⃣ User selects text

The extension sends:

```
POST /detect-ad
```

---

## 2️⃣ API Server

The API server:

* Creates a cache key
* Checks Redis or local cache
* Calls ML server if result is not cached

```
prob = request_inference(text)
```

---

## 3️⃣ ML Server

The ML server:

* Loads the latest model in `models/`
* Preprocesses the text
* Converts tokens into embedding matrices
* Runs PyTorch inference

Output:

```
prob_ad = sigmoid(logit)
```

---

# 🔄 Training Pipeline (Trainer)

Spotter improves over time using feedback collected from users.

The **trainer is not always running** — it is executed manually or periodically when enough new feedback has been collected.

Typical workflow:

```
User Feedback → Database
        ↓
trainer/build_dataset.py
        ↓
trainer/train.py
        ↓
New model_vX.pth generated
```

### 🟡 When does the trainer run?

The trainer is usually executed when:

* A certain number of new feedback samples exist in the database
* You want to refresh the model with new data
* During scheduled training (cron job / manual run)

Example:

```
cd trainer
python -m train
```

After training:

* A new `model_vX.pth` file is saved
* The ML server automatically detects and uses the newest model

No API restart is required.

---

# ⚡ Setup Guide

## 1. Clone Repository

```
git clone https://github.com/yourname/spotter.git
cd spotter
```

---

## 2. Start API Server

```
cd api-server
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --port 8000
```

---

## 3. Start ML Server

```
cd ml-server
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --port 8001
```

---

## 4. Redis (Optional)

```
brew install redis
redis-server
```

Environment variables:

```
REDIS_HOST=localhost
REDIS_PORT=6379
```

If Redis is unavailable, Spotter falls back to an in-memory cache.

---

# 🧩 API Endpoint

## Detect Advertisement

```
POST /detect-ad
```

Request:

```
{
  "text": "example review text"
}
```

Response:

```
{
  "prob_ad": 82.3,
  "is_ad": true,
  "cached": false
}
```

---

# 🔄 Model Versioning

Models are stored as:

```
models/model_v1.pth
models/model_v2.pth
...
```

The ML server automatically loads the newest version based on filename.

---

# 🌍 Deployment Notes

Recommended setup:

* API Server → GCP VM
* ML Server → Same VM or separate instance
* Redis → Local Redis or Memorystore

---

# 👨‍💻 Author

Jihun Park
Computer Science & Communication Engineering
Waseda University

---

# ⭐ Motivation

Spotter explores how real user interaction and feedback can be integrated into a practical AI pipeline, combining lightweight backend engineering with an evolving machine learning model.
