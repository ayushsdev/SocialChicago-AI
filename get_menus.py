import firebase_admin
from firebase_admin import credentials, firestore, storage
import os

# Initialize Firebase (make sure to replace path with your credentials file)
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': 'socialchicago-bf1a5.appspot.com'
})

# Initialize Firestore and Storage
db = firestore.client()
bucket = storage.bucket()

def download_menus():
    # Get all bars from Firestore
    bars_ref = db.collection('bars')
    bars = bars_ref.stream()

    for bar in bars:
        bar_data = bar.to_dict()
        bar_name = bar_data['name']
        
        # Create directory for bar if it doesn't exist
        if not os.path.exists("menus/" + bar_name):
            os.makedirs("menus/" + bar_name)
        
        # Get happy hours for this bar
        happy_hours = bar_data.get('happyHours', [])
        
        for happy_hour in happy_hours:
            happy_hour_id = happy_hour['id']
            
            # Construct the path in Firebase Storage
            storage_path = f'happyHourMenu/{happy_hour_id}.pdf'
            local_path = f'menus/{bar_name}/{happy_hour_id}.pdf'
            
            try:
                # Download the PDF
                blob = bucket.blob(storage_path)
                blob.download_to_filename(local_path)
                print(f"Downloaded menu for {bar_name} - Happy Hour ID: {happy_hour_id}")
            except Exception as e:
                print(f"Error downloading {storage_path}: {str(e)}")

if __name__ == "__main__":
    download_menus()
