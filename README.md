
# Quick Start
    bash
# Clone the repository
git clone https://github.com/hemarastylepeke/pantrychef.git

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver

# Collect static files
python manage.py collectstatic

# Set up production database
python manage.py migrate

# Start production server
gunicorn pantrychef.wsgi:application
Docker Deployment
dockerfile

Cook Smarter, Waste Less, Live Better with PantryChef!

