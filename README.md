#Build For Bharat Backend Project

 - Step 1: Download whole code.
 - Step 2: Create python virtual env (python >= 3.10)
     command:- python -m venv project-env
 - Step 3: Now navigate to the directory where you get requirements.txt file.
 - Step 4: Install all required modules.
     command:- python -m install requirements.txt
 - Step 5: Setup Database: Create DB in MySQL "bharat_backend_db".
 - Step 6: update all database root user credentials in settings.py file.
 - Step 7: Make migrations of all the model
     command:- python manage.py makemigrations
 - Step 8: Now migrate all the table in database
     command:- python manage.py migrate

