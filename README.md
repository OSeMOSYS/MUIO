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

## Developer Setup & Testing

If you are developing or running the project locally from source:

1. Clone the repository to your local machine.
2. Create a virtual environment and install the dependencies.
3. To run the automated tests, ensure you have the development dependencies installed:
   ```bash
   pip install pytest pytest-flask
   ```
4. Execute the test suite from the root directory by running:
   ```bash
   # Set the python path to API so imports resolve correctly
   $env:PYTHONPATH="API"
   python -m pytest tests/
   ```

## Questions and Issues

For troubleshooting model-related issues and discussions, please visit the [Energy Modelling Community Discussion Forum](https://forum.u4ria.org/). 

If you encounter bugs or have new feature ideas, please submit them to the repository's issue tracker. We encourage contributions and discussions to further develop MUIO.
