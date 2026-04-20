# E2E tests using dogtail

## Prerequisites
Before you begin, ensure you have the following installed:
- **Operating system:** Ubuntu 22 (only)
- **Wayland must be disabled** (Ensure your session is running on **X11**)
- **Python 3.12**
- **Poetry** (Python dependency management tool)
- **Docker** (required for running the regtest environment)
- **Meson** (required for `pycairo` package)
  ```bash
  sudo apt install meson
  ```
- **Python development package** (ensure you have `python3.12-dev` installed)
- **libgirepository1.0-dev** (required for `pygobject` package)
  ```bash
  sudo apt install libgirepository1.0-dev
  ```
- **libfuse2** (required for building the application)
  ```bash
  sudo apt install libfuse2
  ```
- **xclip** (required for the `pyperclip` package)
  ```bash
  sudo apt install xclip
  ```
- **wmctrl** (required to maximize the application window)
  ```bash
  sudo apt install wmctrl
  ```
- **Java (JRE & JDK)** (required for Allure report generation)
  ```bash
  sudo apt install default-jre default-jre-headless openjdk-11-jdk
  ```
- **Biscuit CLI**: Required for generating authentication tokens for multisig tests (version 0.6.0+).
  1. Download the binary from the [Biscuit Releases](https://github.com/biscuit-auth/biscuit-rust/releases).
  2. Extract and move the `biscuit` binary to `/usr/local/bin/`:
     ```bash
     sudo mv biscuit /usr/local/bin/
     sudo chmod +x /usr/local/bin/biscuit
     ```
- **Allure**: (for detailed test reporting)
   1. Download the `.tgz` file from the [Allure Releases](https://github.com/allure-framework/allure2/releases).
   2. Extract the file:
      ```bash
      tar -xvzf allure-2.x.x.tgz
      ```
   3. Move the extracted folder to `/opt` and create a symbolic link:
      ```bash
      sudo mv allure-2.x.x /opt/allure
      sudo ln -s /opt/allure/bin/allure /usr/local/bin/allure
      ```

## Steps

1. **Clone the repository**
      ```bash
      git clone https://github.com/RGB-Tools/iris-wallet-vault.git
      cd iris-wallet-vault
      ```

2. **Create a `.env` file**
   Create a `.env` file in the **root directory** and add the following values:
   ```dotenv
   BACKUP_EMAIL_ID=<EMAIL_ID>
   BACKUP_EMAIL_PASSWORD=<PASSWORD>
   GOOGLE_AUTHENTICATOR=<GOOGLE_2FA_SETUP_KEY>
   NATIVE_AUTHENTICATION_PASSWORD=<NATIVE_AUTHENTICATION_PASSWORD>
   ```
   **Note:** These credentials will be used in the following tests:
   - `test_backup_and_restore`
   - `test_ask_auth_for_imp_operations`
   - `test_login_app_auth`

    Provide the `GOOGLE_AUTHENTICATOR` **without spaces**.
    Use **single quotes** around `<PASSWORD>`, and avoid passwords containing single quotes.

3. **Install poetry**<br>
   Install poetry using pip:
   ```bash
   pip install poetry
   ```

4. **Install dependencies**<br>
   Run the following command to install all required dependencies:
   ```bash
   poetry install
   ```

5. **Run the regtest services**<br>
   Start the regtest environment:
   ```bash
   poetry run regtest-start
   ```

6. **Configure the Multisig Hub** (Optional, for multisig tests)<br>
   The Multisig Hub requires a `config.toml` file in `e2e_tests/hub/`.
   ```bash
   mkdir -p e2e_tests/hub
   cat <<EOF > e2e_tests/hub/config.toml
   cosigner_xpubs = [
       "PLACEHOLDER_COLORED_XPUB_1",
       "PLACEHOLDER_COLORED_XPUB_2",
   ]
   threshold_colored = 2
   threshold_vanilla = 2
   root_public_key = "PLACEHOLDER_ROOT_KEY"
   rgb_lib_version = "0.3"
   EOF
   ```

7. **Run test cases**<br>
   Run test cases with the following options:
   ```bash
   # Run all tests
   poetry run e2e-test all

   # Run a specific test
   poetry run single-test <TEST_NAME>

   # Force the build process during test execution
   poetry run e2e-test all force-build
   poetry run single-test <TEST_NAME> force-build

   # Run a specific test with a specific wallet variant
   poetry run single-test <TEST_NAME> --wallet-variant <WALLET_VARIANT>

   ```
   **Note:** `force-build` flags are optional.

8. **List test cases**<br>
   ```bash
   poetry run list-tests
   ```

## Check test results
```bash
# For results
poetry run allure-result
```
