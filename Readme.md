# Question Paper Uploader

This is a local web application built with Python and Flask. It allows you to upload question papers (PDFs or images) and tag them with metadata like subject, year, and exam type. Everything is stored locally on your machine using SQLite.

## Overview

The goal of this project is to organize scattered question paper files into one searchable digital library. You upload a file, tag it, and it gets saved to a folder while the details go into a database. You can then search and filter to find specific papers later.

## Features

* File Upload: Supports PDF and image uploads.

* Metadata: Tag papers with Subject, Exam Type, and Year.

* Search: Filter existing papers by their tags.

* Local Storage: Files are saved in a local uploads directory.

* Database: Uses SQLite to keep track of file details. No internet needed.

* Unique Filenames: Automatically renames files to prevent overwriting old ones.

## Technologies Used

* Python 3

* Flask (Web Framework)

* SQLite (Database)

* HTML/CSS

## Steps to install & run the project

Download the code
* Clone this repository or download the folder to your computer.

* Install Dependencies
Open your terminal in the project folder and run:
```
pip install -r requirements.txt
```

Run the App
* Start the server:
```
python main.py
```

Open in Browser
Go to: http://127.0.0.1:5000





# Instructions for testing

* To Upload:

Click "Upload a Paper" on the home screen.

Select the Subject, Exam Type, and Year.

Choose a file from your computer.

Click Upload.

 * To Search:

Click "Search for a Paper" on the home screen.

Select the filters you want (e.g., "Maths" and "2024").

Click Search.

Click the filename in the results to open or download the file.

## Screenshots

![Home Page](./screenshots/img.png)
![Upload Page](./screenshots/img_1.png)
![Search Page](./screenshots/img_2.png)
![Terminal view](./screenshots/img_3.png)





