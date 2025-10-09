from flask import request, g, send_from_directory
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity

from Models.Users import User
from Resources.AccountInfoResource import AccountInfoResource
from Resources.ActivityLogsResource import ActivityLogsResource
from Resources.AuthResource import AuthResource
from Resources.BillingPaymentResource import BillingPaymentResource
from Resources.LabReportsResource import LabReportsResource
from Resources.LabRequestsResource import LabRequestsResource
from Resources.LabTestsResource import LabTestsResource
from Resources.MedicineResource import MedicineResource
from Resources.DepartmentsResource import DepartmentsResource
from Resources.MedicalRecordsResource import MedicalRecordsResource
from Resources.MedicineStockResource import MedicineStockResource
from Resources.OperationTheatreResource import OperationTheatreResource
from Resources.OrdersResource import OrdersResource
from Resources.PurchaseOrdersResource import PurchaseOrdersResource
from Resources.SurgeryDoctorResource import SurgeryDoctorResource
from Resources.SurgeryResource import SurgeryResource
from Resources.SurgeryTypeResource import SurgeryTypeResource
from Resources.UserFieldsResource import UserFieldsResource
from Resources.UserTypesResource import UserTypesResource
from Resources.UsersResource import UsersResource
from Resources.WardBedsResource import WardBedsResource
from Resources.WardsResource import WardsResource
from Resources.AppointmentsResource import AppointmentsResource
from Resources.TokensResource import TokenResource
from Resources.PrescriptionResource import PrescriptionResource
from Resources.BillingResource import BillingResource
from Serializers.UserSerializers import user_serializer
from app_utils import api, app, jwt


@app.before_request
def load_logged_in_user():
    print(request.url)
    if request.method == 'OPTIONS' or request.url.endswith('/login') or request.url.__contains__('uploads'):
        # Allow preflight request without authentication
        return
    g.user = None
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
        if user_id:
            from Models.Users import User
            user = User.query.filter_by(username=user_id).first()
            if user:
                g.user = user_serializer.dump(user)
                return
        return {"msg": "Token has expired"}, 400  # Stop processing here
    except Exception:
        return {"msg": "Token has expired"}, 400
    # except Exception as e:
    #     g.user = None


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory('uploads', filename)

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
api.add_resource(WardBedsResource, '/ward-beds')
api.add_resource(AppointmentsResource, '/appointment')
api.add_resource(TokenResource, '/tokens')
api.add_resource(PrescriptionResource, '/prescriptions')
api.add_resource(BillingResource, '/billing')
api.add_resource(AuthResource, '/login')
api.add_resource(OperationTheatreResource, '/operation-theatre')
api.add_resource(SurgeryResource, '/surgery')
api.add_resource(SurgeryTypeResource, '/surgery-type')
api.add_resource(BillingPaymentResource, '/billing/<int:billing_id>/payments', '/payment')
api.add_resource(SurgeryDoctorResource, '/surgery-doctor')
api.add_resource(ActivityLogsResource, '/activity-logs')
api.add_resource(AccountInfoResource, '/account-info')