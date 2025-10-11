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

def configure_routes(api):
    base_path = '/tenant/<string:account_uid>'
    api.add_resource(DepartmentsResource, f'{base_path}/departments')
    api.add_resource(UsersResource, f'{base_path}/users')
    api.add_resource(UserTypesResource, f'{base_path}/user-types')
    api.add_resource(UserFieldsResource, f'{base_path}/user-fields')
    api.add_resource(MedicalRecordsResource, f'{base_path}/medical-records')
    api.add_resource(MedicineResource, f'{base_path}/medicines')
    api.add_resource(MedicineStockResource, f'{base_path}/medicine-stock')
    api.add_resource(OrdersResource, f'{base_path}/orders')
    api.add_resource(PurchaseOrdersResource, f'{base_path}/purchase-orders')
    api.add_resource(LabTestsResource, f'{base_path}/lab-tests')
    api.add_resource(LabRequestsResource, f'{base_path}/lab-requests')
    api.add_resource(LabReportsResource, f'{base_path}/lab-reports')
    api.add_resource(WardsResource, f'{base_path}/wards')
    api.add_resource(WardBedsResource, f'{base_path}/ward-beds')
    api.add_resource(AppointmentsResource, f'{base_path}/appointment')
    api.add_resource(TokenResource, f'{base_path}/tokens')
    api.add_resource(PrescriptionResource, f'{base_path}/prescriptions')
    api.add_resource(BillingResource, f'{base_path}/billing')
    api.add_resource(AuthResource, f'{base_path}/login')
    api.add_resource(OperationTheatreResource, f'{base_path}/operation-theatre')
    api.add_resource(SurgeryResource, f'{base_path}/surgery')
    api.add_resource(SurgeryTypeResource, f'{base_path}/surgery-type')
    api.add_resource(BillingPaymentResource, f'{base_path}/billing/<int:billing_id>/payments', '/payment')
    api.add_resource(SurgeryDoctorResource, f'{base_path}/surgery-doctor')
    api.add_resource(ActivityLogsResource, f'{base_path}/activity-logs')
    api.add_resource(AccountInfoResource, '/account-info')

