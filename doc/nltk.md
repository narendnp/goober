You need to install additional the `punk_tab` model for Opus-MT manually.

1. Inside the virtual environment, enter the python interpreter:
    ```bash
    python
    ```
2. Inside the interpreter, enter:
    ```bash
    >>> import nltk
    >>> nltk.download
    ```
3. A new window should open, showing the NLTK Downloader. Click on the File menu and select Change Download Directory. For central installation, set this to:
    ```bash
    C:\nltk_data  # Windows
    /usr/share/nltk_data  # Unix
    /usr/local/share/nltk_data  # Mac
    ```
4. Now go to models, on the left column, find and select `punkt_tab`. Then press Download. 
    > [!NOTE]  
    > The selection is a bit buggy so you need to double-check and make sure it has downloaded it.
5. If it has been downloaded, you can simply close the window, then exit the python interpreter:
    ```bash
    >>> exit()
    ```