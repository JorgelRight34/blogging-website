# YourBlog
#### Video Demo:  <URL HERE>
#### Description: 
  YourBlog is a web application that allows users to make posts, comment those posts, see other posts, like posts, follow bloggers, and make posts about news

### Installation:
  To install the web application and have it up and running, firt we need to install the requeriments defined in requeriments.txt, it can be done typing in the terminal:
    "pip install -r requeriments.txt"
  It must be typed inside the directory of the web application, once the requeriments are installed we can start the server with the following command:
    "python flasky.py"

### Project structure:
  The project is structured in the following way:
  |-flasky
   |-app/
     |-templates/
       |-auth/
       |-blogs/
       home.html
     |-static/
     |-main/
       |-__init__.py
       |-errors.py
       |-views.py
      |-blogs/
       |-__init__.py
       |-views.py
   |-__init__.py
   |-models.py
 |-migrations/
 |-tests/
   |-__init__.py
 |-venv/
 |-requirements.txt
 |-config.py
 |-flasky.py

### app directory:
  The app directory contains the directories, templates, static, main and blogs.
  ## Templates:
  Templates contain all the html files that are used to display the GUI of the web app, 
  # base.html:
  Every other template inherits from base.html, this contains the meta data for the html files and also contains the navbar
  which all other templates inherit, in the base.html we have the following options:
  If user is logged in:
    New post +: This options allows the user if logged in to make a new post
    News: If clicked it shows posts with contents of news from the API 'News API', which returns top headlines news
  If user is not logged in:
    Log in: This option takes the user to the log in page
    Sign Up: This option takes the user to the register page
  Search form: In this form you can search for posts of users registered in the web app

  # home.html:
  The home.html in which pages
  of blogs posts are rendered, and in the sides we have widgets for extra information and functionality.
  

