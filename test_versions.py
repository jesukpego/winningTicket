# test_versions.py
import django
import gunicorn
import whitenoise
import dotenv
import psycopg2
import dj_database_url

print(f"✅ Django: {django.__version__}")
print(f"✅ Gunicorn: {gunicorn.__version__}")
print(f"✅ WhiteNoise: {whitenoise.__version__}")
print(f"✅ python-dotenv: {dotenv.__version__}")
print(f"✅ psycopg2: {psycopg2.__version__}")
print(f"✅ dj-database-url: {dj_database_url.__version__}")