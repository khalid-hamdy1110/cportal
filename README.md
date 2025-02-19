# CPortal
#### Video Demo:  https://youtu.be/7QzH9hN-BNM
## What is CPortal?
CPortal is an all-in-one student portal. Here students can access materials and assignments uploaded by their teachers, they can also have contact with their teachers through messaging and all important school announcements/messages in one place!

## Components used to making CPortal:
- HTML
- CSS
- Python
- JavaScript
- Bootstrap 5
- Flask

## 1. attatchments
This folder contains any attatchments uploaded by any user from any assignment or submission.

## 2. material_uploads
This folder contains any materials uploaded by teachers to the materials tab for students to view.

## 3. static
This folder contains all static files like the icons and images used on the website as well as the css file and js file.

- #### styles.css
    - This file contains the styles for some parts of the page like the nav bar, p tag, body tag, buttons and dark styles for the page such as dark-cards, dark-body, dark-accordion and finally a custom scroll bar.

- #### darkMode.js
    - This JavaScript file contains the function and tools to toggle between dark mode and light mode. This file contains the code that waits for the DOM to be loaded then gets all the components of the websites using querySelector or querySelectorAll then goes over them one by one to toggle the dark version of each component.

## 4. templates
This folder contains all the html files that are being displayed and rendered for each page on the website.

- #### layout.html
    - This file contains the layout that is being extended to all the other html files to reduce redundancy using jinja, the layout includes the navigation bar, and using jinja variations of the navigation bar is shown and then finally there is a footer to appear at every page the says "Made by COOLEX for CS50".

- #### login.html
    - This file is used to log the user in by using a form for the user to enter their username and password.

- #### dashboard.html
    - There are different versions of dashboard each adjusted to display different options for admins, teachers and students. They all get to see and overview of their account info. Admins get buttons which lead to both teacher and student databases, there is also the counts of how many students and teachers are there, then being able to view the classes available. Teachers get to view their latest posted materials and assignments as well as the students who are enrolled in their subject. Students can see the assignments that they haven't submitted and their marked assignments as well as the subjects they are enrolled in. Finally all admins, teachers and students can see their latest received messages.

- #### materials.html
    - This file contains the contents of the materials tab which is where teachers uploads important materials for students to view, there is a jinja for loop that shows each class the student/teachers are enrolled in then there is another for loop that loops through the materials that belong to that class.

- #### assignments.html
    - This file contains the contents of the assignments that has been made by the teachers where a jinja loop is used to render all the classes that the student/teacher are enrolled in to and then another loop is there to show all the assignments in each of the classes, there are also options like adding/removing an assignment and adding attachments to the assignments available to teachers, submitting an assignment is available to students which requires adding an attachment for the submission.

- #### submissions.html
    - This file is available only to teachers to be able to view their student's submission. It uses a jinja for loop to render the classes that the teachers belong to then uses another for loop to render the assignments that belong to that class then another for loop to show the submissions of each assignment. The teachers have the option of correcting the submission, mark it and comment on it.

- #### noclasses.html
    - This file is rendered in the materials, assignments and submissions page if the student/teacher aren't enrolled into any of the classes available.

- #### messages.html
    - This file renders the messages that were received/sent to/from the user, this is available to students, teachers and admins. Students are only limited to messaging their teachers and admins have the feature of group messaging where they can message all Admins or all Teachers or All Students.

- #### databaseS.html & databaseT.html
    - These files are rendered for only admins to view the student and teacher database, an admin can add/remove students/teachers they can also search their databases by id or username or name. There is also a feature to add enrollments to students.

- #### settings.html
    - This file contains all the settings that a user could need including an overview of the account info, changing the user's password, changing their contact info, showing the login history and finally a preferences area where the user could switch from the default light mode to dark mode.

## 5. app.py
This file is the backend of the website where all the forms get processed and entered/removed into/from the database and it is how the templates get rendered and necessary information is sent into the template for it to be used using jinja format inside of the html file to help with the rendering of the file according to the data sent.

## 6. helpers.py
This file contains a function that makes sure that the user is logged in before accessing a webpage on the website from the app.py file.

## 7. requirements.txt
This file contains packages needed to be able to run the website.

## 8. portal.db
This is the database that contains the user info, the admins, students, teachers in database, it also contains materials, assignments, submissions, messages, enrollment and login history and all the data needed to run the website.