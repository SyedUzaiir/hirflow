import os

RESUMES = {
    "rahul_sharma.txt": """Name: Rahul Sharma
Skills: Python, FastAPI, PostgreSQL, Docker, Redis, AWS, Git, RESTful APIs
Experience:
- Senior Backend Engineer, TechCorp (2022 - Present): Designed and deployed high-performance APIs using Python and FastAPI. Optimized PostgreSQL queries, reducing latency by 30%. Configured Redis caching layers and deployed containerized services on AWS using Docker.
- Software Engineer, DevSolutions (2020 - 2022): Developed backend systems using Python, Django, and PostgreSQL. Worked on containerizing applications with Docker.
Education:
- B.Tech in Computer Science, IIT Bombay (2016 - 2020)
Projects:
- Microservices API Gateway: Built a custom API gateway using FastAPI, Docker, and Redis caching.
- DB Migration Tool: Created a utility for seamless PostgreSQL database migrations in Python.
""",

    "priya_patel.txt": """Name: Priya Patel
Skills: Python, Flask, Django, PostgreSQL, Docker, Git, HTML, CSS
Experience:
- Backend Engineer, WebSoft (2022 - Present): Maintained and upgraded backend APIs using Python and Flask. Designed database schemas in PostgreSQL. Managed local containerized environments using Docker.
- Junior Developer, CodeLab (2021 - 2022): Wrote Django scripts and helped manage PostgreSQL database backups.
Education:
- B.E. in Information Technology, Pune University (2017 - 2021)
Projects:
- E-commerce Backend: Created REST APIs for checkout and cart management using Flask and PostgreSQL.
- Blogging Platform: Deployed a blogging system using Django and Docker.
""",

    "john_doe.txt": """Name: John Doe
Skills: Go, PostgreSQL, Kubernetes, AWS, Docker, gRPC, Microservices
Experience:
- Senior Backend Engineer, CloudScale (2021 - Present): Built scalable microservices in Go. Orchestrated deployments with Kubernetes and managed AWS cloud infrastructure. Implemented gRPC communication protocols.
- Backend Developer, SystemsInc (2019 - 2021): Designed high-throughput data processing pipelines using Go and PostgreSQL.
Education:
- M.S. in Computer Science, Stanford University (2017 - 2019)
Projects:
- Distributed Queue: Developed a high-performance message queue in Go.
- K8s Deploy Bot: Automated Kubernetes container scaling on AWS.
""",

    "jane_smith.txt": """Name: Jane Smith
Skills: React, TypeScript, JavaScript, HTML, CSS, TailwindCSS, Jest, Front-End Design
Experience:
- Frontend Engineer, DesignStudio (2023 - Present): Engineered interactive user interfaces using React and TypeScript. Styled interfaces with TailwindCSS and wrote unit tests using Jest.
- UI Developer, PixelPerfect (2021 - 2023): Collaborated with UX designers to translate wireframes into clean HTML/CSS/JavaScript components.
Education:
- B.Sc. in Web Development, Boston University (2018 - 2021)
Projects:
- Portfolio Builder: React app allowing developers to customize portfolios.
- Dashboard UI: A premium, highly animated dashboard styled with TailwindCSS.
""",

    "amit_verma.txt": """Name: Amit Verma
Skills: Python, Flask, SQLite, HTML, CSS, JavaScript, Git
Experience:
- Junior Python Developer, AppCraft (2024 - Present): Developing minor script improvements and maintaining internal tools using Python and Flask.
- Internship, TechStart (2023 - 2024): Assisted in front-end styling and small Flask modifications.
Education:
- B.C.A, Delhi University (2020 - 2023)
Projects:
- Task Tracker: A simple Flask app with an SQLite database backend.
- Weather App: A Python CLI tool to fetch weather from public APIs.
""",

    "sarah_jenkins.txt": """Name: Sarah Jenkins
Skills: AWS, Docker, Kubernetes, Terraform, Python, Bash, CI/CD pipelines
Experience:
- DevOps Engineer, InfraOps (2020 - Present): Designed AWS cloud architecture. Maintained infrastructure-as-code using Terraform. Managed container deployments with Docker and Kubernetes. Wrote Python and Bash automation scripts.
- Linux System Administrator, HostGroup (2018 - 2020): Monitored server uptime, script execution, and user permissions.
Education:
- B.S. in Computer Engineering, UT Austin (2014 - 2018)
Projects:
- Auto-scaling Terraform: Deployed an auto-scaling group on AWS with custom CloudWatch alerts.
- Jenkins CI Pipeline: Automated build and testing phases for a Python backend.
""",

    "rohan_gupta.txt": """Name: Rohan Gupta
Skills: Python, FastAPI, Django, PostgreSQL, Redis, Docker, AWS, Microservices
Experience:
- Senior Backend Developer, ScaleTech (2021 - 2024): Architected microservices with FastAPI. Managed Redis cache databases and hosted PostgreSQL on AWS. Optimized container images using Docker.
- [GAP IN EMPLOYMENT] (May 2024 - June 2025): Personal sabbatical.
- Backend Engineer, CoreCorp (2018 - 2021): Built web backends with Django and PostgreSQL.
Education:
- B.Tech in CSE, BITS Pilani (2014 - 2018)
Projects:
- Real-time Chat: Socket-based chat server using FastAPI and Redis.
- Analytics Tool: Ingested large volumes of client request data into PostgreSQL.
""",

    "emily_chen.txt": """Name: Emily Chen
Skills: Python, FastAPI, PostgreSQL, Redis, Docker, AWS, GraphQL, MongoDB
Experience:
- Senior Backend Engineer, FinTech Solutions (2019 - Present): Developed secure transactional APIs using FastAPI. Implemented distributed caching via Redis. Automated deployments with Docker and managed AWS instances.
- Software Engineer, InfoSys (2017 - 2019): Maintained Java backend services and gradually transitioned scripts to Python.
Education:
- B.Sc. in Computer Science, UC Berkeley (2013 - 2017)
Projects:
- Payment Processing Engine: Highly secure Python service using FastAPI and PostgreSQL.
- API Performance Tuning: Reduced response times by caching heavy queries in Redis.
""",

    "michael_chang.txt": """Name: Michael Chang
Skills: Python, FastAPI, PostgreSQL, Git, JavaScript
Experience:
- Junior Backend Developer, QuickDev (2025 - Present): Writing REST APIs and performing minor updates using FastAPI and PostgreSQL.
Education:
- B.S. in Software Engineering, University of Washington (2021 - 2025)
Projects:
- Recipe Finder API: Simple backend in FastAPI to query recipe databases.
- Postgres Seeder: Python script to generate mock records for database testing.
""",

    "siddharth_mehta.txt": """Name: Siddharth Mehta
Skills: SQL, PostgreSQL, Database Tuning, Python, AWS, SQL Server, Oracle
Experience:
- Database Administrator & Dev, DBMasters (2021 - Present): Designed complex database schemas, implemented recovery protocols, and optimized indexes in PostgreSQL. Used Python for scripting database tasks.
- SQL Developer, DataCorp (2018 - 2021): Created database views, stored procedures, and triggers.
Education:
- B.Tech in IT, VIT Vellore (2014 - 2018)
Projects:
- Query Analyzer: A Python tool to parse and report slow PostgreSQL queries.
- Cloud DB Migration: Migrated local SQL databases to AWS RDS instances.
""",

    "jessica_taylor.txt": """Name: Jessica Taylor
Skills: Java, Spring Boot, PostgreSQL, Docker, AWS, Maven, Hibernate
Experience:
- Senior Backend Developer, EnterpriseSys (2021 - Present): Managed enterprise APIs built on Java and Spring Boot. Maintained PostgreSQL databases and orchestrated AWS deployments with Docker.
- Software Developer, JavaHub (2019 - 2021): Built Spring Boot microservices and configured CI/CD.
Education:
- B.S. in Computer Science, Georgia Tech (2015 - 2019)
Projects:
- Core banking module: Financial ledger service built using Spring Boot and PostgreSQL.
- Docker-Compose Orchestration: Bundled multiple Spring boot services into Docker containers.
""",

    "david_miller.txt": """Name: David Miller
Skills: Vue.js, Nuxt.js, Node.js, Express, JavaScript, CSS, HTML5, MongoDB
Experience:
- Full Stack UI Developer, DigitalWeb (2020 - Present): Designed responsive interfaces using Vue.js. Built lightweight APIs in Node.js/Express.
- Web Designer, AgencyCreative (2018 - 2020): Created web pages using HTML, CSS, and basic JavaScript.
Education:
- B.F.A in Graphic Design, NYU (2014 - 2018)
Projects:
- UI Theme Customizer: Interactive client portal built with Vue.js.
- Creative Agency Site: A beautiful responsive landing page featuring smooth page animations.
""",

    "anjali_rao.txt": """Name: Anjali Rao
Skills: Python, FastAPI, PostgreSQL, Docker, Redis, AWS, CI/CD, Git
Experience:
- Backend Engineer, InnovateHub (2021 - Present): Implemented core backend APIs using Python and FastAPI. Programmed Redis caching systems. Configured PostgreSQL queries and containerized workflows with Docker. Managed AWS architecture.
- Backend Associate, TechPioneers (2019 - 2021): Built python modules, executed script cleanups, and documented APIs.
Education:
- M.Tech in Software Systems, IIIT Bangalore (2017 - 2019)
Projects:
- Live Dashboard Backend: Scalable FastAPI and PostgreSQL backend with Redis.
- Automated Deployer: Git-triggered AWS runner using Docker.
""",

    "alex_mercer.txt": """Name: Alex Mercer
Skills: Python, FastAPI, PostgreSQL, Redis, Docker, Git, RESTful APIs
Experience:
- Software Engineer, DevLabs (2023 - Present): Formulated backend logic in Python and FastAPI. Handled Redis database key schemes. Conducted local setup using Docker.
- Junior Backend Engineer, WebLink (2022 - 2023): Created database queries in PostgreSQL and python utility scripts.
Education:
- B.S. in Computer Science, UT Dallas (2018 - 2022)
Projects:
- User Authentication API: Secure session state backend using FastAPI and Redis.
- Inventory System: Django app backed by PostgreSQL database.
""",

    "lisa_wang.txt": """Name: Lisa Wang
Skills: Python, R, Pandas, NumPy, Scikit-Learn, SQL, PyTorch, Data Visualization
Experience:
- Data Scientist, InsightData (2022 - Present): Generated machine learning models to classify user behavior. Wrote SQL queries to aggregate datasets.
- Data Analyst, MetricCorp (2020 - 2022): Prepared analytical reports and dashboards.
Education:
- M.S. in Data Science, Columbia University (2018 - 2020)
Projects:
- Churn Predictor: Machine learning algorithm predicting user churn using Python.
- SQL Sales Analysis: Complex query scripts summarizing global store metrics.
""",

    "vikram_singh.txt": """Name: Vikram Singh
Skills: Python, Django, PostgreSQL, Docker, AWS, Git, Nginx
Experience:
- Backend Engineer, CloudFlow (2021 - Present): Programmed Django REST services. Deployed Docker structures on AWS behind Nginx reverse proxies.
- Software Engineer, SystemsCare (2019 - 2021): Worked with Python, Django, and relational databases.
Education:
- B.Tech in CSE, Delhi Technological University (2015 - 2019)
Projects:
- Inventory API: Django-based tracking tool featuring AWS media upload integrations.
- Postgres Cluster Setup: Configured write-replicas for PostgreSQL backend.
"""
}

def setup():
    # Make directories
    os.makedirs("data/jd", exist_ok=True)
    os.makedirs("data/resumes", exist_ok=True)
    os.makedirs("utils", exist_ok=True)
    
    # Write resumes
    for filename, content in RESUMES.items():
        filepath = os.path.join("data/resumes", filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content.strip())
        print(f"Created resume: {filepath}")
    
    print("Resume setup complete.")

if __name__ == "__main__":
    setup()
