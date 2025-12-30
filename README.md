#  Quote Comparison Chatbot

A Python-based intelligent chatbot that helps users compare and analyze different quotes (e.g., insurance, product prices, or service offers) and respond with relevant, conversational answers.

This project showcases a simple yet powerful chatbot built using Python, utility modules for processing queries, and a backend logic for comparing quote data.

##  Features

-  Interactive chatbot interface (CLI or web-based via Flask)
-  Compare quotes from multiple sources
-  Smart logic for identifying best value offers
-  Modular Python architecture for easy extension
-  Ready for future NLP or AI-based upgrades

##  Project Structure
├── app.py # Main application entry point

├── core/ # Core chatbot logic and processing

├── data/ # Dataset or example quotes

├── utils/ # Utility functions and helpers

├── requirements.txt # Python dependencies

└── README.md # Project documentation


##  Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/siddhijaiswal08/Quote-Comparison-Chatbot.git
cd Quote-Comparison-Chatbot
```

##  Setup & Installation

### 2. Create a Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows PowerShell
```

### 3. Install Dependencies

```bash 
pip install -r requirements.txt
```

## Run the Chatbot

### From Command Line 
```bash
python app.py
```

### If using Flask
```bash
export FLASK_APP=app.py
flask run
```
Then open your browser at http://localhost:5000

### How It Works
1. Input Handling — User enters a query asking for quote comparisons.

2. Processing — The chatbot logic reads quote data and applies comparison logic.

3. Response — A friendly answer is shown based on quote attributes.

### Dependencies
All required packages are listed in requirements.txt. To install them:
```bash
pip install -r requirements.txt
```
### License
This project is open-source and free to use and modify.


