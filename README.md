For my capstone project, I created a web application to allow students on campus to barter items with each other, or put them up for auction. 
This project utilized a full tech stack consisting of Python and Flask, HTML and CSS, SQLite, and Pandas. 
It also utilized some cybersecurity concepts such as RSA encryption for protecting user’s login and transaction information.

To simmulate real users, I was given an excel spreadsheet with a user's full name, login information, and payment information.
I converted this spreadhseet to a CSV trhough Pandas, which was then RSA encrypted and stored on an SQLite server for the application to access.
The application also includes functionality to create a new user by providing a full name, login information, and payment information.
Users can then login and either browse current listings or post a new listing of their own.
Listing information was also stored on the SQLite server for the application to access.

This project taught me about relational database design and implementation, efficient SQL querying, enctryption, and what full stack development looks like.
