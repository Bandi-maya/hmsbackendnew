from flask import Flask
from flask_restful import Api
from flask_cors import CORS

from Resources.LabReportsResource import LabReportsResource
from Resources.LabRequestsResource import LabRequestsResource
from Resources.LabTestsResource import LabTestsResource
from Resources.MedicineResource import MedicineResource
from Resources.DepartmentsResource import DepartmentsResource
from Resources.MedicalRecordsResource import MedicalRecordsResource
from Resources.MedicineStockResource import MedicineStockResource
from Resources.OrdersResource import OrdersResource
from Resources.PurchaseOrdersResource import PurchaseOrdersResource
from Resources.UserFieldsResource import UserFieldsResource
from Resources.UserTypesResource import UserTypesResource
from Resources.UsersResource import UsersResource
from Resources.WardsResource import WardsResource
from Resources.AppointmentsResource import AppointmentsResource
from Resources.TokensResource import TokenResource
from Resources.PrescriptionResource import PrescriptionResource
from Resources.BillingResource import BillingResource
from app_utils import db, ma

app = Flask(__name__)
cors = CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:Vignesh@localhost:5432/hms1'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
ma.init_app(app)
api = Api(app)

api.add_resource(DepartmentsResource, '/departments')
api.add_resource(UsersResource, '/users')
api.add_resource(UserTypesResource, '/user-types')
api.add_resource(UserFieldsResource, '/user-fields')
api.add_resource(MedicalRecordsResource, '/medical-records')
api.add_resource(MedicineResource, '/medicines')
api.add_resource(MedicineStockResource, '/medicine-stock')
api.add_resource(OrdersResource, '/orders')
api.add_resource(PurchaseOrdersResource, '/purchase-orders')
api.add_resource(LabTestsResource, '/lab-tests')
api.add_resource(LabRequestsResource, '/lab-requests')
api.add_resource(LabReportsResource, '/lab-reports')
api.add_resource(WardsResource, '/wards')
api.add_resource(AppointmentsResource, '/appointment')
api.add_resource(TokenResource, '/tokens')
api.add_resource(PrescriptionResource, '/prescriptions')
api.add_resource(BillingResource, '/billing')