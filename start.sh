#!/bin/bash
cd backend
gunicorn run:app --workers=4 --bind=0.0.0.0:${PORT:-5000}
