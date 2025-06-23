# Mossie - Mental Health Companion App

A comprehensive mental health application featuring mood tracking, journaling, virtual pet companion, and user authentication with PostgreSQL.

## Features

- User authentication with salted passwords and UUID-based identification
- PostgreSQL database integration
- Interactive virtual pet companion with accessories and play mode
- Mood tracking with visualization
- Personal journal for recording thoughts and feelings
- User settings customization
- Modern, responsive UI with consistent design
- CLI tools for database management

## Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- pip (Python package manager)

## Setup Instructions

### 1. Clone the Repository

First, clone the repository to your local machine:

```bash
git clone https://github.com/yourusername/mossie.git
cd mossie
```

If you received the code as a zip file, extract it to a folder of your choice.

### 2. Install PostgreSQL

If you don't have PostgreSQL installed, follow the installation instructions for your operating system:
- macOS: `brew install postgresql`
- Linux: `sudo apt-get install postgresql`
- Windows: Download from the [official PostgreSQL website](https://www.postgresql.org/download/windows/)

Start the PostgreSQL service:
- macOS: `brew services start postgresql`
- Linux: `sudo service postgresql start`
- Windows: PostgreSQL should run as a service automatically after installation

### 2. Create the Database

```bash
# Log in to PostgreSQL as postgres user
psql -U postgres

# Create the database
CREATE DATABASE mossie;

# Exit PostgreSQL
\q
```

### 3. Set Up a Virtual Environment (Recommended)

Create and activate a virtual environment:

```bash
# Install virtualenv if you don't have it
pip install virtualenv

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

### 4. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 5. Initialize the Database

Create a PostgreSQL database:

```bash
# Log in to PostgreSQL as postgres user
psql -U postgres

# Create the database
CREATE DATABASE mossie;

# Exit PostgreSQL
\q
```

Then initialize the database schema:

Option 1: Using the schema file
```bash
flask --app temp.app init-db-schema schema.sql
```

Option 2: Using the built-in initialization
```bash
flask --app temp.app init-db
```

### 6. Create a User

```bash
flask --app temp.app create-user your_username your_password
```

Replace `your_username` and `your_password` with your desired credentials.

### 7. Run the Application

```bash
flask --app temp.app --debug run
```

The application will be available at http://127.0.0.1:5000

## Environment Variables

You can customize the application settings using the following environment variables:

- `SECRET_KEY`: Flask secret key for session encryption (default: 'dev_key_only_for_development')
- `DATABASE_FILENAME`: Database filename for SQLite (default: 'mossie.db')
- `DATABASE_URL`: PostgreSQL connection string (if using PostgreSQL instead of SQLite)

## Database Schema

The database contains the following tables:

### Users Table
- `user_id`: UUID primary key
- `username`: Unique username (VARCHAR)
- `password_hash`: SHA-256 hash of password with salt (VARCHAR) 
- `password_salt`: Unique salt for password hashing (VARCHAR)
- `created_at`: Account creation timestamp
- `last_login`: Last login timestamp

## Deployment Options

### Local Deployment (Recommended)

Local deployment is the simplest and recommended way to run the Mossie application:

1. **Ensure PostgreSQL is running**:
   ```bash
   # Check PostgreSQL status
   pg_isready
   
   # If not running, start it
   # On macOS:
   brew services start postgresql
   # On Linux:
   sudo service postgresql start
   ```

2. **Run the Flask application**:
   ```bash
   # From the project directory
   flask --app temp.app --debug run
   ```

The application will be available at http://127.0.0.1:5000

### AWS Deployment

To deploy the application to AWS Elastic Beanstalk:

1. **Install Required Tools**

```bash
pip install awscli awsebcli
```

2. **Configure AWS Credentials**

```bash
aws configure
```

You'll need to enter:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., us-east-1)
- Default output format (json)

3. **Initialize Elastic Beanstalk Application**

```bash
cd /path/to/mossie/temp
eb init -p python-3.9 mossie-app --region us-east-1
```

4. **Create an Elastic Beanstalk Environment**

```bash
eb create mossie-env
```

5. **Set Environment Variables**

```bash
eb setenv SECRET_KEY=your_secure_secret_key FLASK_ENV=production
```

6. **Open Your Application**

```bash
eb open
```

### Docker Deployment

1. **Install Docker**

Download and install Docker from the [official Docker website](https://www.docker.com/get-started).

2. **Create a Dockerfile**

Create a file named `Dockerfile` in the project root with the following content:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "temp.app:app"]
```

3. **Build and Run the Docker Container**

```bash
# Build the Docker image
docker build -t mossie-app .

# Run the container
docker run -p 5000:5000 -e SECRET_KEY=your_secure_key mossie-app
```

The application will be available at http://localhost:5000

## Troubleshooting

### Database Connection Issues

- Verify PostgreSQL is running with `pg_isready` command
- Check database credentials and connection string
- Ensure the database exists and has been initialized
- If you see errors about PostgreSQL connection, make sure:
  - PostgreSQL service is running
  - The database 'mossie' exists
  - Your connection string is correct in the environment variables
  - Try setting the DATABASE_URL environment variable explicitly:
    ```bash
    export DATABASE_URL="postgresql://postgres:postgres@localhost:5432/mossie"
    ```

### Application Startup Issues

- Verify all dependencies are installed with `pip list`
- Check for any error messages in the console output
- Ensure the correct Flask application is specified (`temp.app`)

### Authentication Issues

- Make sure a user has been created with the `create-user` command
- Check for correct username and password
- Verify session configuration and SECRET_KEY

### Pet Table
- `pet_id`: Integer primary key
- `user_id`: Foreign key to users table
- `name`: Pet name
- `happiness`: Integer value representing pet happiness
- `last_interaction`: Timestamp of last interaction

### Accessories Table
- `accessory_id`: Integer primary key
- `name`: Accessory name
- `type`: Accessory type (hat, glasses, etc.)
- `image_path`: Path to accessory image

### User_Accessories Table
- `user_id`: Foreign key to users table
- `accessory_id`: Foreign key to accessories table
- `equipped`: Boolean indicating if accessory is equipped

### Mood_Entries Table
- `entry_id`: Integer primary key
- `user_id`: Foreign key to users table
- `mood_value`: Integer representing mood (1-10)
- `notes`: Text notes about mood
- `created_at`: Entry timestamp

### Journal_Entries Table
- `entry_id`: Integer primary key
- `user_id`: Foreign key to users table
- `title`: Journal entry title
- `content`: Journal entry content
- `created_at`: Entry timestamp
- `updated_at`: Last update timestamp
