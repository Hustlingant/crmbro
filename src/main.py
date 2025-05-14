import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, jsonify, render_template, request, redirect, url_for # Added render_template, request, redirect, url_for
from src.models.models import db, Campaign # Import Campaign model
from src.routes.user import user_bp 
from src.routes.ai_services_routes import ai_bp
from src.routes.campaign_routes import campaign_bp

app = Flask(__name__, 
            template_folder=os.path.join(os.path.dirname(__file__), 'templates'), 
            static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'a_very_secret_key_that_should_be_in_env_for_production')

# Register blueprints
app.register_blueprint(user_bp, url_prefix='/api/v1/auth') 
app.register_blueprint(ai_bp) 
app.register_blueprint(campaign_bp)

# Database Configuration
db_username = os.getenv('DB_USERNAME', 'root')
db_password = os.getenv('DB_PASSWORD', 'password')
db_host = os.getenv('DB_HOST', '127.0.0.1') # Changed to 127.0.0.1 for local dev consistency
db_port = os.getenv('DB_PORT', '3306')
db_name = os.getenv('DB_NAME', 'hyperlocal_smb_platform_db') # Specific DB name

app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{db_username}:{db_password}@{db_host}:{db_port}/{db_name}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    # Create the database if it doesn't exist (for local dev)
    from sqlalchemy import create_engine
    from sqlalchemy_utils import database_exists, create_database
    engine = create_engine(f"mysql+pymysql://{db_username}:{db_password}@{db_host}:{db_port}")
    if not database_exists(f"{engine.url}/{db_name}"):
        create_database(f"{engine.url}/{db_name}")
        print(f"Database {db_name} created.")
    else:
        print(f"Database {db_name} already exists.")
    db.create_all()
    print("Database tables created/verified.")

# Frontend Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    # Add logic to fetch dashboard data if needed
    return render_template('dashboard.html')

@app.route('/campaigns')
def campaigns():
    # This would typically list campaigns, for now, it redirects to create or shows a placeholder
    # For the prototype, let's assume it's a page that links to create campaign
    return redirect(url_for('create_campaign'))

@app.route('/create-campaign', methods=['GET'])
def create_campaign():
    return render_template('create_campaign.html')

@app.route('/create-campaign', methods=['POST'])
def create_campaign_submit():
    try:
        campaign_name = request.form.get('campaign_name')
        marketing_goal = request.form.get('marketing_goal')
        total_budget = request.form.get('total_budget')
        start_date_str = request.form.get('start_date')
        end_date_str = request.form.get('end_date')
        location = request.form.get('location')
        radius = request.form.get('radius')
        interests = request.form.get('interests')
        ad_headline = request.form.get('ad_headline')
        # selected_channels = request.form.getlist('selected_channels') # This will be a list

        # Basic validation (can be more extensive)
        if not all([campaign_name, marketing_goal, total_budget, start_date_str, end_date_str, location, radius]):
            return jsonify({"error": "Missing required campaign fields"}), 400
        
        from datetime import datetime
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        new_campaign = Campaign(
            name=campaign_name,
            goal=marketing_goal,
            budget=float(total_budget),
            start_date=start_date,
            end_date=end_date,
            status='Draft' # Default status
            # Add other fields like user_id if you have user authentication implemented
        )
        db.session.add(new_campaign)
        db.session.commit()
        # We would also save audience, channels, creatives related to this campaign_id
        # For prototype, just saving the campaign basics.
        return redirect(url_for('dashboard')) # Redirect to dashboard after creation
    except Exception as e:
        db.session.rollback()
        print(f"Error creating campaign: {e}")
        return jsonify({"error": str(e)}), 500

# Serve static files like index.html if no other route matches (for SPA-like behavior or direct access)
# This is a simplified catch-all, ensure your static files are in the 'static' folder
# and templates in 'templates'. The default Flask static serving is usually sufficient for /static/...

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

