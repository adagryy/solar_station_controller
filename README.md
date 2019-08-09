At the beginning you should configure app with correct access credentials to the PostgreSQL database by setting correct environmental variable:
	$ export DBPASSWORD="yourpassword"

First you should install database engines:
	$ apt install postgresql-11
	$ apt install redis-server

To run this project I recommend do it using virtual environment. You should install it this way:
	$ virtualenv -p /usr/bin/python3 env

Enter virtual environment:
	$ source env/bin/activate
 
Then install dependencies:
	1. Django
	2. Daphne (ASGI server)
	3. Redis
	4. psycopg2 (module for PostgreSQL database)
	
	$ pip3 install Django Daphne Redis psycopg2

Finally you can run development server:
	$ python3 manage.py runserver

To run in production mode use Daphne ASGI server and remember to set Debug in mirrors/settings.py to False

