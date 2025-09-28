from flask_migrate import Migrate

from app import app
from app_utils import db
from Models.UserType import UserType
from Models.UserField import  UserField
from Models.Users import User
from Models.MedicalRecords import MedicalRecords
from Models.Medicine import Medicine
from Models.MedicineStock import MedicineStock
from Models.LabTest import LabTest
from Models.LabRequest import LabRequest
from Models.LabReport import LabReport
from Models.Wards import Ward

migrate = Migrate(app, db)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
