# EasyWS
Edit Worksheets Without Messing Up The Formatting

## Tech
Uses QT With The PySide6 Wrapper For The GUI. 
The Google Docs API Is Used For Connecting To The Document.
The Project Is Written In Python.

## Features

- Recreate A Google Doc Within A Python GUI
- Text Is Split Into Chunks Allowing Editing Only Of Fields That Need It
- A Submit Button That Will Upload Your Changes Straight To The Google Doc
- Underscores Will Be Removed So That Formatting Stays Consistent When Changes Are Made

## WIP Features

- Choose A Color To Upload Your Changes As
- Detect Underlines Spaces As Inputs
- Detect Multiple Newlines As Inputs
- More Formatting Improvements
- Input Texts Will Change Size If They Overflow The Text Box
- Save Where Inputs Were, So They Can Be Edited On Reload

## Usage
*Prerequisite: Python 3.10+ And A Python Environment (Virtual Recommended) Setup*
1. Download The Files And Place Them In The Environment
2. Install PySide6: `pip install PySide6`
3. Follow The Instructions [Here](https://developers.google.com/workspace/guides/create-project) To Create A Google Project
4. Than [Enable The Docs API](https://developers.google.com/docs/api/quickstart/python#enable_the_api) And [Set Permissions For Desktop Use](https://developers.google.com/docs/api/quickstart/python#authorize_credentials_for_a_desktop_application)
5. Ensure That `credentials.json` Is in the same directory as the other files.
6. Go To The Google Doc That You Want To Edit And Copy The ID
    The ID Is In The Link
    `https://docs.google.com/document/d/THE_ID_IS_A_STRING_OF_RANDOM_CHARECTERS_HERE/edit`
7. At The Top Of `main.py` Paste The ID Into The `DOCUMENT_ID` variable. It Should Look Like This `DOCUMENT_ID = "YOUR ID HERE"`. **The `"` Are Needed**
8. In The Terminal Run `python main.py`. You Will Be Given A Link In The Terminal
9. After Navigating To The Link You Will Be Prompted To Login To Your Google Account. 
10. If A Screen Pops Up That Has 2 Buttons, "Back To Safety" And "Advanced", Click "Advanced" Than Click "Continue"
11. The Program Will Now Run And Inputs Will Be Converted Into Editable Text Boxes. When The Text Boxes Are Filled The User Can Click Submit And The Google Doc Will Be Updated.
