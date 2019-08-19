At the beginning you should configure app with correct access credentials to the PostgreSQL database and with correct hashing/seeding source by setting correct environmental variables:
	
	$ export DBPASSWORD="yourpassword"
	$ export SECRETKEY="your_secret_key"

You can also do it in various other ways like placing these commands in /etc/profile, /etc/environment systemd definition file (production).
Below is the example of systemd configuration for automatic management (especially start on system boot) of Daphne server:

	[Unit]
	Description=Daphne ASGI Server
	After=network.target

	[Service]
	PIDFile=/run/daphne/pid
	Type=simple
	User=root
	Group=root
	WorkingDirectory=/<you_app_path>/mirrorcontroller/mirrors/
	ExecStart=/<your_app_path>/mirrorcontroller/env/bin/python3 /<your_app_path>/mirrorcontroller/env/bin/daphne mirrors.asgi:application
	ExecStop=/bin/kill -s TERM $MAINPID
	Restart=on-abort
	PrivateTmp=true
	EnvironmentFile=/<your_app_path>/mirrorcontroller/credentials	

	[Install]
	WantedBy=multi-user.target

Next you should install database engines:
	
	$ apt install postgresql-11
	$ apt install redis-server

After installing database engines you should configure PostgreSQL database according to the Django app settings:

	create database solar;
	create user solar with password 'yourpassword';
	grant all privileges on database solar to solar;

To run this project create your main app directory and virtual environment. You should do it in this way:
	
	$ mkdir <your_app_path> && cd <your_app_path>
	$ virtualenv -p /usr/bin/python3 env

Enter virtual environment:
	
	$ source env/bin/activate
 
Then install dependencies: Django, Daphne (ASGI server), Redis, psycopg2 (module for PostgreSQL database), channels library, channels_redis (library for interfacing channels with Redis)
	
	$ pip3 install Django Daphne Redis psycopg2 channels channels_redis

Copy source code of application from this repository to <your_app_path>

Finally you can run development server:

	$ python3 manage.py runserver

PRODUCTION:
To run in production mode use Daphne ASGI server and remember to set Debug in mirrors/settings.py to False.
Then enable systemd service:

	$ systemctl enable daphne.service
	$ systemctl start daphne.service

