# DevRef : Learn while you fix
DevRef is an AI-powered assistant for pull requests that helps developers learn while fixing review comments.   It integrates with multiple knowledge sources, processes reviewer feedback using NLP, and recommends the most relevant articles, documentation, or tutorials - directly inside the PR.

This project consists of two main parts:
1.  **Frontend**: A single HTML file with embedded JavaScript and CSS that provides the user interface for viewing pull requests, adding comments, and configuring recommendation settings.
2.  **Backend**: A Flask application that receives comments and settings from the frontend, processes them, and returns relevant learning resources.


## How to Run the Project

This project requires two separate servers to run simultaneously: one for the backend and a simple HTTP server to serve the frontend file.

### Step 1: Set up the Python Backend

1.  **Install Dependencies**: Open your terminal or command prompt, navigate to your project directory, and install all the required Python packages using the `requirements.txt` file.

    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the Server**: In your first terminal window, execute the following command to start the backend server:

    ```bash
    flask run
    ```

    You should see a message confirming that the server is running, likely at `http://127.0.0.1:5000`. Keep this terminal window open.

### Step 2: Serve the Frontend

1.  **Open a second terminal window.** Navigate to the same project directory.

2.  **Run a simple HTTP server** to serve your `index.html` file.

    ```bash
    python -m http.server
    ```

    This will start a web server, likely at **`http://127.0.0.1:8000`**. Keep this terminal window open as well.

### Step 3: Access the Application

1.  Open your web browser and go to the URL of your frontend server: **`http://127.0.0.1:8000/src`**.

2.  You will now see the pull request UI. Add a comment and press `Enter` to see the bot's recommendations.

---

### API Keys and Data Sources

The project includes a **Settings** dialog that allows you to configure API keys for external search providers like **Google** and **YouTube**. This enables the bot to fetch real-world data from these sources.

The project also uses a local mock dataset, `data/internal_dataset.yaml`, which can be replaced with your own data to test the system with custom recommendations. This file is used by the `InternalProvider` to return a canned set of responses without needing an external API.

You can edit this file to provide different mock data, or if you prefer, remove the `InternalProvider` from the settings to use only the external sources.

