--- STEPS FOR NEWLY CREATE LOCAL REPOSITORY ---
Step 1: Create a root directory in your local folder.
Step 2: Open cmd and cd to the root directory.
Step 3: Install virtualenv using these lines "virtualenv --python C:\Users\Administrator\AppData\Local\Programs\Python\Python310\python.exe ."
		Note: python version=3.10.3
Step 4: Activate the virtual environment from the root directory using cmd. To activate: enter Scripts\activate
Step 5: Clone the source codes from remote repository to the root directory using git command:
		git clone <repo_link>
Step 6: copy and paste the requirements.txt from the project directory to the root directory.
Step 7: Using cmd, enter pip install -r requirements.txt
Step 8: Open the source code using vs code.
Step 9: Open your pgadmin4.
Step 10: Return to the cmd, from the root directory where the virtualenv is installed, enter the following lines (make sure that the project is already connected to the database):
		python manage.py makemigrations
		python manage.py migrate

Step 11: Enter cls.
Step 12: Using cmd, enter python manage.py createsuperuser
					and follow the next prompt.
Step 13: Using cmd, cd to the project directory.
Step 14: Then enter, python manage.py runserver
Step 15: To stop, click ctrl + c
Step 16: To deactivate the virtualenv, using cmd, enter deactivate



--- STEPS TO SAVE YOUR CHANGES FROM YOUR LOCAL REPOSITORY TO THE REMOTE REPOSITORY ---
Step 1: Click the source control on the left side of your screen.
		Note: Make sure that the selected branch is your assigned branch.
		To confirm, navigate to the menu and click "View". Hover to appearance and click Status Bar.
		The status bar is located on the lower part of your vs code display.

		If the selected branch is not your assigned branch. Click it and check if your assigned branch will show.
		If not, then publish a branch using the assigned branch name to you. To do this:
		Click the source control, click the "views and more actions", hover to "branch", and click the "Create branch" option.
		Enter the exact branch name assigned to you, then click Enter.
		Return to the source control, from the source control, enter a message (it is required), under the Changes dropdown, click the + button (stage all changes).
		Click commit, then click sync changes. If "Publish branch" button appears, then click it.

	If the selected branch is your assigned branch, proceed to step 2:
Step 2: Under the SOURCE CONTROL, enter a message (it is required).
Step 3: Under the Changes dropdown, click the + button (stage all changes). Then click commit and sync changes.

Note: To undo last commit, under the source control. 
		Click the "Views and More Actions" and hover to the commit part.
		Click "undo last commit"


--- STEPS TO SYNC CHANGES FROM REMOTE REPOSITORY TO YOUR LOCAL REPOSITORY ---
Step 1: Under the source control, click the "View and More Actions".
Step 2: Hover to the "Pull/Push" and click "Sync".

--- REQUIRED STEPS AFTER A SUCCESSFUL BRANCH MERGE IN THE REMOTE REPOSITORY ---
Step 1: Under the source control, click the "View and More Actions".
Step 2: Hover to the "Pull/Push" and click "Sync".



--- POSTGRES unaccent CONFIG Steps ---
For reference: https://stackoverflow.com/questions/31382675/how-can-i-activate-the-unaccent-extension-on-an-already-existing-model
Step 0: Open the settings.py, inside the INSTALLED_APPS, add django.contrib.postgres
Step 1: Open the SQL SHELL(psql)
Step 2: Follow the authentication process in sql shell.
Step 3: Then enter, CREATE EXTENSION unaccent;
Step 4: Open the vs code terminal window, and enter the following commands to create an empty migration file:
		python manage.py makemigrations appname --empty

Step 5: Navigate to the appname.migrations folder and open the latest migration file.
Step 6: On the selected migration file, type from django.contrib.postgres.operations import UnaccentExtension on line 1 or 2.
Step 7: Under the class Migration, enter UnaccentExtension() inside the operations variable.
Step 8: Return to the vs code terminal window, now enter python manage.py migrate


--- STEPS BEFORE MERGE ---
Step 1: Delete the _pycache folder on all subfolders.
		List of folders with _pycache inside: adminportal, studentportal, studentportal_4ng1, teachersportal, all migration folders, all templatetags folders

Step 2: Delete all migrations files on all migration folders. Do not delete the migration folder and the __init__.py file inside it.
Step 3: In settings.py from the studentportal_4ng1, inside DATABASES, remove the password and left it empty.
Step 4: Empty the EMAIL_HOST_USER  and  EMAIL_HOST_PASSWORD in settings.py


--- STEPS AFTER MERGE ---
Step 1: Sync the changes from our remote repository to your local machine.
Step 2: In settings.py from the studentportal_4ng1, inside DATABASES, enter the superuser password of your postgres.
Step 3: Delete/drop the db4ng1 in your pgadmin4.
Step 4: Create new database and name it db4ng1.
Step 5: Using cmd, activate the environment, and makemigrations, then migrate.
Step 6: Create a superuser using:
		python manage.py createsuperuser and follow the next prompts. (admin@gmail.com  admin)

Step 7: open the terminal from vs code
Step 8: Enter this:
		python manage.py shell
		from adminportal.models import *
		from adminportal.tests import *

		make_sy()

		make_enrollment_setup()

		make_scn()

		make_scemail()

		make_shs_track()

		make_students()

Step 9: Using cmd, use the runserver and open the localhost.
Step 10: Login using admin account.
Step 11: Add strand to any available tracks.
Step 12: Return to vs code terminal, and enter make_admissions()
Step 13: Report any errors