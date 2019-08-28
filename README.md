At the beginning you should configure app with correct access credentials to the PostgreSQL database and with correct hashing/seeding source by setting correct environmental variables:
	
	$ export DBPASSWORD="yourpassword"
	$ export SECRETKEY="your_secret_key"

You can also do it in various other ways like placing these commands in /etc/profile, /etc/environment systemd definition file (production).
Examples of systemd configuration file for automatic management are in "config" directory.
You should place systemd configuration file in /lib/systemd/system/ directory in your Linux system (Ubuntu).

Next you should install database engines:
	
	$ apt install postgresql-11
	$ apt install redis-server

After installing database engines you should configure PostgreSQL database according to the Django app settings in settings.py:

	create database solar;
	create user solar with password 'yourpassword';
	grant all privileges on database solar to solar;

To run this project create your main app directory and virtual environment. You should do it in this way:
	
	$ mkdir <your_app_path> && cd <your_app_path>
	$ virtualenv -p /usr/bin/python3 env

Enter virtual environment:
	
	$ source env/bin/activate
 
Then install dependencies: Django, Daphne (ASGI server), Redis, psycopg2 (module for PostgreSQL database), channels library, channels_redis (library for interfacing channels with Redis), w1thermsensor (package for reading temperature from sensors)
	
	$ pip3 install -U Django Daphne Redis psycopg2 channels channels_redis w1thermsensor RPi.GPIO

Copy source code of application from this repository to <your_app_path>

Now run necessary software for GPIO:

	$ systemctl enable pigpiod.service
	$ systemctl start pigpiod.service

Finally you can run development server:

	$ python3 manage.py runserver

PRODUCTION:
To run in production mode use Daphne ASGI server and remember to set Debug in mirrors/settings.py to False.
Then enable systemd service:

	$ systemctl enable daphne.service
	$ systemctl start daphne.service

