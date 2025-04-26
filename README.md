# Iris Wallet desktop

Iris Wallet manages RGB assets from issuance to spending and receiving,
wrapping all functionality in a familiar-looking wallet application and
abstracting away as many technical details as possible.

The RGB functionality is provided by [rgb-lightning-node].

[rgb-lightning-node]: https://github.com/RGB-Tools/rgb-lightning-node

## Prerequisites
Before you begin, ensure you have the following installed:
- **Python 3.12**
- **Poetry** (Python dependency management tool)
- **Rust** (latest version for compiling the Lightning Node binary)
- **Docker** (required for running the regtest environment)

---

## Installation Steps

### 1. Clone the Repository
Open your terminal and clone the Iris Wallet Desktop repository:
```bash
git clone https://github.com/RGB-Tools/iris-wallet-desktop.git
```
This creates a directory named `iris-wallet-desktop`.

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
poetry shell
pyside6-rcc src/resources.qrc -o src/resources_rc.py
```

### 6. Create Lightning Node Binary

#### 6.1 Create a Directory for the Binary
Create a directory for the Lightning Node binary in the `iris-wallet-desktop` root directory:
```bash
mkdir ln_node_binary
```

#### 6.2 Clone the RGB Lightning Node
In a different location, clone the RGB Lightning Node repository:
```bash
git clone https://github.com/RGB-Tools/rgb-lightning-node --recurse-submodules --shallow-submodules
```

#### 6.3 Install the Lightning Node
Navigate to the root folder of the cloned RGB Lightning Node project:
```bash
cd rgb-lightning-node
cargo install --debug --path . --locked
```

### 7. Add the Lightning Node Binary
Locate the `rgb-lightning-node` binary in the `target/debug` directory and copy it to the `ln_node_binary` folder in the `iris-wallet-desktop` directory.

### 8. Create Configuration File

#### 8.1 Create `config.py`
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

#### 8.2 Create Google Drive Credentials

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
             "client_secret": "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",
             "redirect_uris": ["redirect_uris"]
         }
     }
     ```
   - **Important:** Remove the `"redirect_uris"` field from the JSON file.

6. **Update Your Configuration:**
   - Save the modified JSON file and add it to your `config.py` file.

### 9. Start the Application
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
  1. First, run the `regtest.sh` script in the `rgb-lightning-node` directory:
     ```bash
     ./regtest.sh
     ```
  2. Then, start the application:
     ```bash
     poetry run iris-wallet --network=regtest
     ```

### 10. Build the Application
To build the application, ensure you have completed all previous steps and enter the Poetry shell:
```bash
poetry shell
```

#### 10.1 Build for Linux
```bash
build-iris-wallet --network=<NETWORK> --distribution=<DISTRIBUTION> --ldk-port=<port> [optional]
```
- `<DISTRIBUTION>`: `{appimage,deb}`
- If you want the application to run on a specific port, use the `--ldk-port` argument. This is optional and can be ignored if no specific port is required.

### 11. Run unit tests:

```bash
poetry run pytest
```

#### 11.1 Run single unit test:

```bash
poetry run pytest unit_tests/tests<TEST_FILE.py>
```
