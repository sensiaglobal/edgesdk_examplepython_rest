# Introduction 
This is a sample application written in Python that demonstrates basic functionality using the REST server.

# Getting Started

## First Time Running
#### **Install Python Version 13.1**
> **NOTE** The HCC2 Docker environment uses Python 3.13-Bullseye
- [Python 3.13.1 for Windows](https://www.python.org/downloads/windows/)
- [Python 3.13.1 for macOS](https://www.python.org/downloads/macos/)

#### **Install Dependencies**
```bash
cd path/to/this/folder
pip install -r "requirements.txt"
```

# Build and Test

## **Update Configuration Settings**
For the application to connect to your HCC2 you need to change the IP information to point to your device and PC.

Within *config/apiconfig.py*

Need to change:

```
api_url: str = ""
api_callback_url: str = ""
```
To:

```
api_url: str = "http://<HCC2 URL>:7071/api/v1"
api_callback_url: str = "http://<Local PC IP Address>:8100/webhook/v1"
```
	
Example:

```
api_url: str = "http://10.0.0.135:7071/api/v1"
api_callback_url: str = "http://10.0.0.105:8100/webhook/v1"
```

Note: For development you will need to make similar changes to *launch.json*.

## To Run
```bash
cd path/to/this/folder
python3 app.py
```
## To Use
Once the application is running, you will need to deploy it at least once for the application settings to be applied, and for the Operate page to display updated values from the application.

# Contribute
Clone locally and fork to contribute updates.

# References
- [Visual Studio Code](https://github.com/Microsoft/vscode)
- [HCC2 SDK Documentation](https://edgesdk.sensiadigital.net/)