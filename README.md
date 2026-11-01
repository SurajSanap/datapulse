# datapulse
Data pipeline starter monorepo for ingestion, backend, dbt, frontend, and infrastructure.

# System architecture
<img width="722" height="731" alt="image" src="https://github.com/user-attachments/assets/e36bd943-9d33-4278-9744-a607ca0c8a63" />

# Technology stack — our decisions
<img width="725" height="527" alt="image" src="https://github.com/user-attachments/assets/3f2f9480-5b3e-4ed3-a3d6-516153766867" />

# Repo
'''
datapulse/
│
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── main.py
│   ├── tests/
│   └── requirements.txt
│
├── ingestion/
│   ├── sources/
│   │   ├── weather.py
│   │   └── air_quality.py
│   ├── pipelines/
│   ├── storage/
│   └── main.py
│
├── orchestration/
│   └── flows/
│
├── dbt/
│   ├── models/
│   │   ├── staging/
│   │   └── marts/
│   ├── tests/
│   └── dbt_project.yml
│
├── frontend/
│   └── src/
│       ├── components/
│       ├── pages/
│       └── services/
│
├── data/
│   └── bronze/
│
├── infrastructure/
│   └── docker/
│
├── docs/
│
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md

'''
