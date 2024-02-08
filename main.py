import os
import uuid

import openai
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from google.cloud import storage
from flask_migrate import Migrate
import json

app = Flask(__name__)
CORS(app)

# Set your OpenAI API key here
openai.api_key = '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'

# Configure this environment variable via your operating system
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'D:/Oulu Stuff/Other/univibe-412217-7868ca0bbc73.json'

# Database configuration: Update with your MySQL credentials and database name
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:%40Password123%23@localhost:3306/univibe'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Initialize the storage client
storage_client = storage.Client()
bucket_name = "univibe_photo_bucket"  # replace with your bucket name
bucket = storage_client.bucket(bucket_name)

# Directory to save uploaded files
# Set the directory to save uploaded files, relative to the current script location
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Define the Photo model which represents the 'photos' table in the database
class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)  # Auto-incrementing primary key
    uuid = db.Column(db.String(100), unique=True)  # UUID field to store unique identifier
    file_path = db.Column(db.String(255))  # Field to store the file path
    unique_id = db.Column(db.String(100))
    nature_of_work = db.Column(db.String(100))
    workspace_composition = db.Column(db.String(100))
    collaboration_dynamics = db.Column(db.String(100))
    workspace_suitability = db.Column(db.Integer)
    person_environment_fit = db.Column(db.Integer)
    overall_satisfaction = db.Column(db.Integer)
    inspiration = db.Column(db.Integer)
    lighting = db.Column(db.Integer)
    noise_level = db.Column(db.Integer)
    location_latitude = db.Column(db.Float)
    location_longitude = db.Column(db.Float)
    social_activities_facilitation = db.Column(db.Integer)
    cooperation_facilitation = db.Column(db.Integer)
    concentration_facilitation = db.Column(db.Integer)
    recovery_facilitation = db.Column(db.Integer)
    calmness = db.Column(db.Integer)
    views_and_natural_elements = db.Column(db.Boolean)
    emotional_connection = db.Column(db.Text)
    additional_comments = db.Column(db.Text)


@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'


@app.route('/health', methods=['GET'])
def health_check():
    try:
        # Attempt to retrieve the engine list as a simple health check
        engine_list = openai.Engine.list()
        return jsonify({'status': 'API key is valid', 'engines': engine_list})
    except Exception as e:
        return jsonify({'error': f'API key is invalid or there is an issue: {str(e)}'}), 500


@app.route('/generate_description', methods=['POST'])
def generate_description():
    # Check if the request contains a file
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']

    # Process the file (you may need to save it temporarily, depending on your requirements)
    # Here, we assume 'process_image' is a function to handle image processing
    image_description = process_image(file)

    # Use GPT-4 to generate a description based on the image
    try:
        response = openai.Completion.create(
            engine="text-davinci-002",  # Use the appropriate GPT-4 engine
            prompt=f"Describe the following image: {image_description}",
            max_tokens=50  # Adjust the maximum number of tokens as needed
        )
        generated_description = response.choices[0].text.strip()
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    return jsonify({'description': generated_description})


# @app.route('/upload_image', methods=['POST'])
# def upload_image():
#     # Check if the request has the file part
#     if 'photo' not in request.files:
#         return jsonify({'error': 'No photo part'}), 400
#
#     file = request.files['photo']
#
#     # Additional data fields
#     unique_id = request.form.get('uniqueId')
#     nature_of_work = request.form.get('natureOfWork')
#
#
#
#
#     # ... include other fields as necessary
#
#     # If the user does not select a file, the browser submits an
#     # empty file without a filename.
#     if file.filename == '':
#         return jsonify({'error': 'No selected file'}), 400
#
#     if file and allowed_file(file.filename):
#         # Generate a unique filename using uuid
#         ext = file.filename.rsplit('.', 1)[1].lower()
#         unique_filename = f"{uuid.uuid4()}.{ext}"
#
#         # Create a blob in the bucket
#         blob = bucket.blob(unique_filename)
#
#         # Upload the file to Google Cloud Storage
#         blob.upload_from_string(
#             file.read(),
#             content_type=file.content_type
#         )
#
#         # The public URL can be used to directly access the file via HTTP.
#         public_url = blob.public_url
#
#         # Assuming 'Photo' is your model and 'photos' is your table name
#         # Modify this part to match your model's constructor and database schema
#         new_photo = Photo(
#             uuid=unique_filename,
#             file_path=public_url,
#             unique_id=unique_id,
#             nature_of_work=nature_of_work,
#
#             # ... include other fields as necessary
#         )
#         db.session.add(new_photo)  # Add the new record to the database session
#         db.session.commit()  # Commit the session to save the record to the database
#
#         return jsonify({'message': 'File uploaded successfully', 'public_url': public_url}), 200
#
#     return jsonify({'error': 'File type not allowed'}), 400

@app.route('/upload_image', methods=['POST'])
def upload_image():
    # Check if there's a photo part in the request
    file = request.files.get('photo')

    # Extract location data if it exists
    location_data = request.form.get('location')
    location_latitude = None
    location_longitude = None
    if location_data:
        location = json.loads(location_data)
        location_latitude = location.get('latitude')
        location_longitude = location.get('longitude')

    # Create a new Photo instance with all other form data
    new_photo = Photo(
        unique_id=request.form.get('uniqueId'),
        nature_of_work=request.form.get('natureOfWork'),
        workspace_composition=request.form.get('workspaceComposition'),
        collaboration_dynamics=request.form.get('collaborationDynamics'),
        workspace_suitability=request.form.get('workspaceSuitability', type=int),
        person_environment_fit=request.form.get('personEnvironmentFit', type=int),
        overall_satisfaction=request.form.get('overallSatisfaction', type=int),
        inspiration=request.form.get('inspiration', type=int),
        lighting=request.form.get('lighting', type=int),
        noise_level=request.form.get('noiseLevel', type=int),
        location_latitude=location_latitude,
        location_longitude=location_longitude,
        social_activities_facilitation=request.form.get('socialActivitiesFacilitation', type=int),
        cooperation_facilitation=request.form.get('cooperationFacilitation', type=int),
        concentration_facilitation=request.form.get('concentrationFacilitation', type=int),
        recovery_facilitation=request.form.get('recoveryFacilitation', type=int),
        calmness=request.form.get('calmness', type=int),
        views_and_natural_elements=request.form.get('viewsAndNaturalElements') == 'true',
        emotional_connection=request.form.get('emotionalConnection'),
        additional_comments=request.form.get('additionalComments')
    )

    # Upload the file if it exists and is allowed
    if file and allowed_file(file.filename):
        # Generate a unique filename
        ext = file.filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}.{ext}"

        # Upload file to Google Cloud Storage
        blob = bucket.blob(unique_filename)
        blob.upload_from_string(file.read(), content_type=file.content_type)
        new_photo.file_path = blob.public_url
        new_photo.uuid = unique_filename

    # Add and commit the new record to the database
    db.session.add(new_photo)
    db.session.commit()

    return jsonify({'message': 'Data uploaded successfully', 'public_url': new_photo.file_path if file else None}), 200


@app.route('/photos', methods=['GET'])
def get_photos():
    photos = Photo.query.all()  # Or use Photo.query.limit(100).all() to limit the results
    photos_list = [{'id': photo.id, 'uuid': photo.uuid, 'file_path': photo.file_path} for photo in photos]
    return jsonify(photos_list)


def process_image(file):
    # Placeholder for image processing logic
    # You may need to use an image recognition tool or library for this step
    # Return a string representing the processed image description
    return 'a processed image description'


if __name__ == '__main__':
    db.create_all()  # This line creates all the tables based on the models defined (only needed once)
    # app.run(debug=True)
    app.run(host="0.0.0.0", port=5000, debug=True)
