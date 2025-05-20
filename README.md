# Iris Wallet desktop

Iris Wallet manages RGB assets from issuance to spending and receiving,
wrapping all functionality in a familiar-looking wallet application and
abstracting away as many technical details as possible.

The RGB functionality is provided by [rgb-lib-python].

[rgb-lib-python]: https://github.com/RGB-Tools/rgb-lib-python

## Prerequisites
Before you begin, ensure you have the following installed:
- **Python 3.12**
- **Poetry** (Python dependency management tool)
- **Docker** (required for running the regtest environment)

---

## Installation Steps

### 1. Clone the Repository
Open your terminal and clone the Iris Wallet Vault repository:
```bash
git clone https://github.com/RGB-Tools/iris-wallet-vault.git
```
This creates a directory named `iris-wallet-vault`.

### 2. Navigate to the Directory
Change into the cloned directory:
```bash
cd iris-wallet-desktop
```

### 3. Install Poetry
Install Poetry using pip:
```bash
pip install poetry
```

### 4. Install Dependencies
Run the following command to install all required dependencies:
```bash
poetry install
```

### 5. Compile Resources
Compile the resources with PySide6:
```bash
poetry run pyside6-rcc src/resources.qrc -o src/resources_rc.py
```

### 6. Create Configuration File

#### 6.1 Create `config.py`
Create a `config.py` file in the `iris-wallet-desktop` directory and add the following configuration. Replace placeholders with your actual credentials:
```python
# Config file for Google Drive access
client_config = {
    'installed': {
        'client_id': 'your_client_id_from_google_drive',
        'project_id': 'your_project_id',
        'auth_uri': 'https://accounts.google.com/o/oauth2/auth',
        'token_uri': 'https://oauth2.googleapis.com/token',
        'auth_provider_x509_cert_url': 'https://www.googleapis.com/oauth2/v1/certs',
        'client_secret': 'your_client_secret',
    },
}
```

#### 6.2 Create Google Drive Credentials

1. **Log In:**
   - Access the Google Developer Console.
   - Sign in with the Google account for which you want to create credentials.

2. **Create a New Project:**
   - Click on **Select a Project** in the top right corner.
   - Click on **New Project**, enter a name for your project, and click **Create**.

3. **Enable Google Drive API:**
   - Once logged in, use the search bar to find and enable **Google Drive API**.

4. **Create Credentials:**
   - After enabling the API, click on **Create Credentials**.
   - Provide the required information. When setting up the OAuth consent screen, select the **Desktop app**.

5. **Download the JSON File:**
   - Once the credentials are created, download the JSON file. It will look something like this:
     ```json
     {
         "installed": {
             "client_id": "your_client_id",
             "project_id": "your_project_id",
             "auth_uri": "https://accounts.google.com/o/oauth2/auth",
             "token_uri": "https://oauth2.googleapis.com/token",
             "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
             "client_secret": "client_secret",
             "redirect_uris": ["redirect_uris"]
         }
     }
     ```
   - **Important:** Remove the `"redirect_uris"` field from the JSON file.

6. **Update Your Configuration:**
   - Save the modified JSON file and add it to your `config.py` file.

### 7. Start the Application
You can now start the Iris Wallet application using:
```bash
poetry run iris-wallet --network=<NETWORK>
```
Replace `<NETWORK>` with either `regtest` or `testnet`:

- **For Testnet:**
  ```bash
  poetry run iris-wallet --network=testnet
  ```

- **For Regtest:**
     ```bash
     poetry run iris-wallet --network=regtest
     ```

### 8. Build the Application
To build the application, ensure you have completed all previous steps:

#### 8.1 Build for Linux
```bash
poetry run build-iris-wallet --network=<NETWORK> --distribution=<DISTRIBUTION>
```
- `<DISTRIBUTION>`: `{appimage,deb}`

### 9. Run unit tests:

```bash
poetry run pytest
```

#### 9.1 Run single unit test:

```bash
poetry run pytest unit_tests/tests<TEST_FILE.py>
```
