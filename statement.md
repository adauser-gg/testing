## Problem Statement
Students and teachers often struggle to find, organize, and access past question papers. These essential study materials are frequently scattered across various devices, messaging app like whatsapp groups leaving student confused about the right study resources.
This disorganization leads to wasted study time and frustration, especially during exam preparation.

## Scope of project 
The Question Paper Uploader aims to solve this problem by providing a centralized, digital repository for exam papers. The scope includes developing a local web application that allows users to upload question paper files (PDFs or images) and tag them with key metadata such as subject, exam type, and year. 

## Target users

* Students: Who need a reliable way to archive and access past exam papers for revision and practice.

* Teachers: Who want to maintain a digital library of question papers for reference and to share with students.

* Educational Institutions: Looking for a simple, internal tool to manage academic resources.

# High-level features

* File Upload Interface: A user-friendly form to upload PDF and image files.

* Metadata Tagging: Mandatory fields for Subject, Exam Type (e.g., Midterm, Endterm), and Year to categorize each upload effectively.

* Search and Filtering: A robust search interface allowing users to filter papers by subject, exam type, and year to find specific documents quickly.

* Local File Storage: Secure storage of uploaded files within a structured directory on the local machine.

* Database Management: Automated storage of file metadata in a local SQLite database for persistent record-keeping.

* Duplicate Prevention: Usage of unique identifiers (UUIDs) for filenames to prevent accidental overwrites of files with the same name.

* Simple Navigation: An intuitive UI with clear navigation between the Home, Upload, and Search pages.





















