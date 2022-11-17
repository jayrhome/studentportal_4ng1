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
