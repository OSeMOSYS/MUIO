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

## Configuration

MUIO is configured entirely through environment variables. This makes it easy to adapt the
application to different environments (local development, staging, production) without touching
source code.

### Using a `.env` file for local development

A `.env.template` file is included in the repository as a reference. To get started locally:

```bash
# 1. Copy the template
cp .env.template .env

# 2. Edit .env with your values (see table below)
# 3. Run the server — it will pick up .env automatically
python API/app.py
```

> **Important:** Never commit your `.env` file.  
> It is already listed in `.gitignore` to prevent accidental exposure of credentials.

### Environment variable reference

| Variable | Default | Description |
|---|---|---|
| `PORT` | `5002` | TCP port the server listens on. |
| `S3_BUCKET` | *(empty)* | Name of the AWS S3 bucket used for case-file sync. |
| `S3_KEY` | *(empty)* | AWS IAM access key ID (required when `AWS_SYNC=1`). |
| `S3_SECRET` | *(empty)* | AWS IAM secret access key (required when `AWS_SYNC=1`). |
| `AWS_SYNC` | `0` | Set to `1` to enable S3 ↔ local synchronisation on startup. |
| `HEROKU_DEPLOY` | `0` | Set to `1` when deploying to Heroku (changes CORS origin and server binding). |

### Precedence

```
Shell environment variables  >  .env file  >  built-in defaults
```

Real environment variables (e.g. those set in Heroku Config Vars or a CI/CD pipeline)
always override any value defined in a local `.env` file.

### Example minimal `.env` for local development

```
PORT=5002
AWS_SYNC=0
HEROKU_DEPLOY=0
```

---

## Questions and Issues

For troubleshooting model-related issues and discussions, please visit the [Energy Modelling Community Discussion Forum](https://forum.u4ria.org/). 

If you encounter bugs or have new feature ideas, please submit them to the repository's issue tracker. We encourage contributions and discussions to further develop MUIO.
