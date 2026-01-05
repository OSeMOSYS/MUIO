# Modelling User Interface for OSeMOSYS (MUIO)

![License](https://img.shields.io/github/license/OSeMOSYS/MUIO)
![Version](https://img.shields.io/github/v/release/OSeMOSYS/MUIO)
![GitHub all releases](https://img.shields.io/github/downloads/OSeMOSYS/MUIO/total)

This repository contains the user interface for the Open Source Energy Modelling System (OSeMOSYS). OSeMOSYS is a linear optimization energy system model designed to minimize total system costs while ensuring energy demands are met within specified constraints. It facilitates optimal allocation of energy resources, technologies, and investments over time, supporting long-term energy planning and policy analysis.

1.	Download the latest version of the user interface from [here](https://forms.office.com/Pages/ResponsePage.aspx?id=wE8mz7iun0SQVILORFQISwwn5YyR7ONHs-3JdG3f5AFUODlJOEQwWTBXMlRRNFUwNEpUTUZYQ1RXOS4u). 
2.	Move the .exe file from your download folder to a folder where you have administrator privileges. This may be for instance inside the folder: users>>name_of_the_user or any other folder you prefer. 
3.	Right-click on MUIO.exe and click ‘Run as administrator’. This will start the installation of the MUIO. The installation may take several minutes. Once it is complete, the installation window will simply disappear. 
4.	The App will open automatically once the installation is complete. If not, search on the Windows Taskbar for ‘’MUIO’’ and open the App. 
5.	You will see the MUIO in a new window. 

## Installation Guide for MacOS and Linux 
1. Clone the repository. 
    ```
   git clone https://github.com/junohBede/MUIO.git
   ```
2. Create conda environment with using the command below. If you do not have conda installed in your machine, refer to this [link.](www.anaconda.com/docs/getting-started/miniconda/install)
3. Activate conda environment with the command below.
   ```
   conda activate muio
   ```
4. Replace folder “MUIO/WebAPP/SOLVERs/COIN-OR/Cbc” contents from [here.](https://github.com/coin-or/Cbc/releases/tag/releases%2F2.10.12)
5. Run `python API/app.py` in terminal. (Make sure that your current working directory is not MUIO, before running the command.)
6. Open web browser to open web app [http://127.0.0.1:5002/#/](http://127.0.0.1:5002/#/)

## Installation Guide using Docker
**Docker** is an open platform that allows developers to automate the deployment of application inside containers. You can find more information within this [link.](https://docs.docker.com/get-started/docker-overview/) 
1. Clone the repository. 
    ```
   git clone https://github.com/junohBede/MUIO.git
   ```
2. Build Docker image using Dockerfile of the repository.
   ```
   docker build -t muio .        
   ```
3. Run Docker container, with opening ports for web app.
   ```
    docker run -dt -p 5002:5002 --name muio muio
   ```
4. Open web browser to open web app [http://127.0.0.1:5002/#/](http://127.0.0.1:5002/#/)

## Questions and Issues

For troubleshooting model-related issues and discussions, please visit the [Energy Modelling Community Discussion Forum](https://forum.u4ria.org/). 

If you encounter bugs or have new feature ideas, please submit them to the repository's issue tracker. We encourage contributions and discussions to further develop MUIO.