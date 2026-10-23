# AITU Collab

A full-stack web platform designed exclusively for Astana IT University students to form teams, post academic project ideas, and find partners for hackathons like GDG DevFest. 


## Project Overview
Finding the right teammates with the right skills can be the hardest part of any hackathon or group project. AITU Collab solves this by providing a centralized feed where students can post open positions, review applicant skills, and manage their project teams in a sleek, dark-mode environment.

## Core Features (CRUD Operations)
This project fully implements Create, Read, Update, and Delete logic with a relational database architecture.

* **Create:** Users can post new project ideas, specifying required skills, course names, and the number of partners needed.
* **Read:** A dynamic, filtering feed displays all open projects. Users can view detailed project pages and public profiles.
* **Update:** Users can customize their profiles, updating their major, course year, technical skills, and bio.
* **Delete / Manage:** Project authors receive requests in a dedicated Inbox, where they can review applicant skills and choose to Accept or Decline (modifying database states).

### Additional Features
* **User Authentication:** Secure login and registration using Werkzeug password hashing.
* **Peer Review System:** A 1-to-5 star rating system for users to review teammates after a project concludes.
* **Team Chat Hub:** Private chat rooms automatically generated for accepted team members.
* **Avatar Generation:** Dynamic profile picture generation based on user initials.

## Tech Stack
* **Backend:** Python, Flask
* **Database:** PostgreSQL (Cloud hosted on Railway), Flask-SQLAlchemy (ORM)
* **Frontend:** HTML5, CSS3 (Custom Dark Theme), Jinja2 Templating
* **Deployment:** Gunicorn, Railway

## Database Models
The relational database is built on four core models:
1. User: Stores authentication data, academic details, and skills.
2. Project: Stores project details and tracks the author (One-to-Many).
3. JoinRequest: A transactional table managing pending/accepted/declined states between Users and Projects.
4. Review: Tracks 5-star ratings given between users.

## How to Run Locally

1. **Clone the repository:**
   ```bash
   git clone [https://github.com/batyrkhankairatuly1-create/AITU-Collab.git](https://github.com/batyrkhankairatuly1-create/AITU-Collab.git)
   cd AITU-Collab