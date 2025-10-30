import json
from decimal import Decimal

from flask import request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy import or_, func
from sqlalchemy.exc import IntegrityError
import logging
from sqlalchemy.orm import aliased

from Models.Medicine import Medicine
from Models.MedicineStock import MedicineStock
from Models.Orders import Orders
from Models.PurchaseOrder import PurchaseOrder
from Models.PurchaseSurgery import PurchaseSurgery
from Models.PurchaseTest import PurchaseTest
from Models.LabTest import LabTest
from Models.Prescriptions import Prescriptions
from Models.Surgery import Surgery
from Models.SurgeryType import SurgeryType
from Models.Billing import Billing
from Models.Users import User
from Models.PurchaseOrder import PurchaseOrder
from Serializers.OrdersSerializer import order_serializers, order_serializer
from new import with_tenant_session_and_user
from utils.logger import log_activity

logger = logging.getLogger(__name__)


class OrdersResource(Resource):
    method_decorators = [jwt_required()]

    # ✅ GET all orders
    @with_tenant_session_and_user
    def get(self, tenant_session, **kwargs):
        try:
            # 🔹 Pagination
            page = request.args.get("page", type=int)
            limit = request.args.get("limit", type=int)

            # 🔹 Type filter
            order_type = request.args.get("order_type")  # 'medicine' | 'lab_test' | 'surgery' | 'prescription'

            # 🔹 Base query
            query = tenant_session.query(Orders).distinct()
            query = query.join(User)
            totalOrders = 0
            todayOrders = 0
            total_items_purchased = 0

            # 🔹 Strict Type Filtering: include only one type, exclude others
            if order_type == 'medicine':
                query = query.join(PurchaseOrder, Orders.id==PurchaseOrder.order_id)
                query = query.join(Medicine, PurchaseOrder.medicine_id==Medicine.id)
                query = query.filter(
                    ~Orders.surgeries.any(),      # has surgeries
                    Orders.medicines.any(),     # no medicines
                    ~Orders.lab_tests.any(),
                    Orders.prescription_id == None     # no lab tests
                )
                totalOrders = query.count()
                todayOrders = query.filter(Orders.received_date == func.current_date()).count()
                total_items_purchased = (
                        tenant_session.query(func.coalesce(func.sum(PurchaseOrder.quantity), 0))
                        .join(Orders, Orders.id == PurchaseOrder.order_id)
                        .filter(Orders.prescription_id == None)
                        .scalar()
                    )
                q = request.args.get('q')
                if q:
                    query = query.filter(
                        or_(
                            User.email.ilike(f"%{q}%"),
                            Orders.taken_by.ilike(f"{q}"),
                            Orders.taken_by_phone_no.ilike(f"{q}"),
                            Orders.taken_by_phone_no.ilike(f"{q}"),
                            Medicine.name.ilike(f"{q}"),
                        )
                    )
            elif order_type == 'lab_test':
                query = query.join(PurchaseTest, Orders.id==PurchaseTest.order_id)
                query = query.join(LabTest, LabTest.id==PurchaseTest.test_id)
                query = query.filter(
                    ~Orders.surgeries.any(),      # has surgeries
                    ~Orders.medicines.any(),     # no medicines
                    Orders.lab_tests.any()      # no lab tests
                )
                q = request.args.get('q')
                if q:
                    query = query.filter(
                        or_(
                            User.email.ilike(f"%{q}%"),
                            Orders.taken_by.ilike(f"{q}"),
                            Orders.taken_by_phone_no.ilike(f"{q}"),
                            Orders.taken_by_phone_no.ilike(f"{q}"),
                            LabTest.name.ilike(f"{q}"),
                        )
                    )
            elif order_type == 'surgery':
                query = query.join(PurchaseSurgery, Orders.id==PurchaseSurgery.order_id)
                query = query.join(SurgeryType, SurgeryType.id==PurchaseSurgery.surgery_type_id)
                query = query.filter(
                    Orders.surgeries.any(),      # has surgeries
                    ~Orders.medicines.any(),     # no medicines
                    ~Orders.lab_tests.any()      # no lab tests
                )
                q = request.args.get('q')
                status = request.args.get('status')
                if status:
                    query = query.filter(
                        or_(
                            PurchaseSurgery.status == status
                        )
                    )
                if q:
                    query = query.filter(
                        or_(
                            User.email.ilike(f"%{q}%"),
                            Orders.taken_by.ilike(f"{q}"),
                            Orders.taken_by_phone_no.ilike(f"{q}"),
                            Orders.taken_by_phone_no.ilike(f"{q}"),
                            SurgeryType.name.ilike(f"{q}"),
                        )
                    )
            elif order_type == "prescription":
                query = query.join(Prescriptions, Prescriptions.id==Orders.prescription_id)
                Doctor = aliased(User)
                query = query.join(Doctor, Doctor.id==Prescriptions.doctor_id)
                q = request.args.get('q')
                if q:
                    query = query.filter(
                        or_(
                            User.email.ilike(f"%{q}%"),
                            Doctor.email.ilike(f"%{q}%"),
                            Doctor.name.ilike(f"%{q}%"),
                            Prescriptions.notes.ilike(f"%{q}%")
                        )
                    )

            elif order_type is not None:
                return {"error": "Invalid type. Must be one of: medicine, lab_test, surgery, prescription"}, 400


            total_records = query.count()

            # 🔹 Pagination
            if page is not None and limit is not None:
                page = max(page, 1)
                limit = max(limit, 1)
                query = query.offset((page - 1) * limit).limit(limit)
            else:
                page = 1
                limit = total_records

            # 🔹 Fetch and serialize results
            orders = query.all()
            result = order_serializers.dump(orders)

            # 🔹 Activity log
            log_activity("GET_ORDERS", details=json.dumps({
                "count": len(result),
                "page": page,
                "limit": limit,
                "type": order_type
            }))

            return {
                "page": page,
                "limit": limit,
                "todayOrders": todayOrders,
                "totalOrders": totalOrders,
                "total_items_purchased": int(total_items_purchased),
                "total_records": total_records,
                "total_pages": (total_records + limit - 1) // limit if limit else 1,
                "data": result
            }, 200

        except Exception as e:
            logger.exception("Error fetching orders")
            return {"error": "Internal error occurred"}, 500
        
    # ✅ POST create new order with items
    @with_tenant_session_and_user
    def post(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            user_id = json_data.get("user_id")
            received_date = json_data.get("received_date")
            taken_by = json_data.get("taken_by")
            taken_by_phone_no = json_data.get("taken_by_phone_no")
            medicines_data = json_data.get("medicines", [])
            lab_tests_data = json_data.get("lab_tests", [])
            surgeries_data = json_data.get("surgeries", [])
            doctor_id = json_data.get("doctor_id", None)
            notes = json_data.get("notes", None)

            if not (medicines_data or lab_tests_data or surgeries_data):
                return {"error": "No items provided (medicines, lab_tests, or surgeries)"}, 400
            
            prescription_id = None

            # ✅ STEP 1: Validate stock availability before creating order
            for item in medicines_data:
                medicine_id = item.get("medicine_id")
                quantity = int(item.get("quantity"))

                if not medicine_id or not quantity:
                    return {"error": "Each item must have medicine_id and quantity"}, 400

                medicine_stock = tenant_session.query(MedicineStock).filter_by(medicine_id=medicine_id).first()
                if not medicine_stock:
                    return {"error": f"No stock found for Medicine ID {medicine_id}"}, 404

                if int(medicine_stock.quantity) < int(quantity):
                    return {"error": f"Insufficient stock for Medicine ID {medicine_id}. Available: {int(medicine_stock.quantity)}, Requested: {quantity}"}, 400

            # ✅ Create the main order
            if doctor_id:
                Prescriptions.tenant_session = tenant_session
                prescription = Prescriptions(
                    doctor_id=doctor_id,
                    notes=notes
                )
                tenant_session.add(prescription)
                tenant_session.flush()
                prescription_id = prescription.id

            Orders.tenant_session = tenant_session
            order = Orders(
                user_id=user_id,
                received_date=received_date,
                taken_by=taken_by,
                prescription_id=prescription_id,
                taken_by_phone_no=taken_by_phone_no
            )
            tenant_session.add(order)
            tenant_session.flush()  # Get order.id before commit

            total_amount = 0

            # ✅ STEP 2: Add each item to PurchaseOrder AND decrement inventory
            for item in medicines_data:
                medicine_id = item.get("medicine_id")
                quantity = int(item.get("quantity"))

                medicine = tenant_session.query(Medicine).get(medicine_id)
                medicine_stock = tenant_session.query(MedicineStock).filter_by(medicine_id=medicine_id).first()

                price = (Decimal(medicine_stock.price) if medicine_stock.price else Decimal('0')) * int(quantity)
                total_amount += price

                # ✅ DECREMENT INVENTORY HERE
                previous_stock = int(medicine_stock.quantity)
                medicine_stock.quantity -= quantity
                
                if int(medicine_stock.quantity) < 0:
                    tenant_session.rollback()
                    return {"error": f"Stock went negative for Medicine ID {medicine_id}"}, 400
                
                tenant_session.add(medicine_stock)

                PurchaseOrder.tenant_session = tenant_session
                purchase_item = PurchaseOrder(
                    order_id=order.id,
                    medicine_id=medicine_id,
                    quantity=quantity,
                    # total_amount=price,
                )
                tenant_session.add(purchase_item)

            for item in lab_tests_data:
                test_id = item.get("test_id")
                status = item.get("status", "pending")

                if not test_id:
                    tenant_session.rollback()
                    return {"error": "Each lab_test item must have test_id"}, 400
                
                lab_test = tenant_session.query(LabTest).get(test_id)
                if not lab_test:
                    tenant_session.rollback()
                    return {"error": f"Lab Test ID {test_id} not found"}, 404

                price = Decimal(lab_test.price) if hasattr(lab_test, 'price') and lab_test.price else Decimal('0')
                total_amount += price

                PurchaseTest.tenant_session = tenant_session
                purchase_test = PurchaseTest(
                    order_id=order.id,
                    status=status,
                    test_id=test_id,
                )
                tenant_session.add(purchase_test)

            # Process surgeries
            for item in surgeries_data:
                surgery_type_id = item.get("surgery_type_id")
                price = item.get("price", 0)
                scheduled_date = item.get("scheduled_date")
                status = item.get("status")
                notes = item.get("notes")
                scheduled_start_time=item.get("scheduled_start_time")
                scheduled_end_time=item.get("scheduled_end_time")
                operation_theatre_id=item.get("operation_theatre_id")

                if not surgery_type_id:
                    tenant_session.rollback()
                    return {"error": "Each surgery item must have surgery_type_id"}, 400

                surgery = tenant_session.query(SurgeryType).get(surgery_type_id)
                if not surgery:
                    tenant_session.rollback()
                    return {"error": f"Surgery Type ID {surgery_type_id} not found"}, 404

                total_amount += price

                PurchaseSurgery.tenant_session = tenant_session
                purchase_surgery = PurchaseSurgery(
                    order_id=order.id,
                    surgery_type_id=surgery_type_id,
                    scheduled_date=scheduled_date,
                    scheduled_start_time = scheduled_start_time,
                    scheduled_end_time = scheduled_end_time,
                    status=status,
                    operation_theatre_id=operation_theatre_id,
                    notes=notes
                )
                tenant_session.add(purchase_surgery)

            Billing.tenant_session = tenant_session
            billing = Billing(
                total_amount=total_amount,
                order_id=order.id
            )
            tenant_session.add(billing)

            tenant_session.commit()
            
            # 🔹 Activity log for inventory update
            log_activity("ORDER_CREATED_WITH_INVENTORY_UPDATE", details=json.dumps({
                "order_id": order.id,
                "medicines_updated": len(medicines_data),
                "total_amount": float(total_amount)
            }))
            
            return order_serializer.dump(order), 201

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {ie.orig}"}, 400
        except Exception as e:
            tenant_session.rollback()
            logger.exception("Error creating order")
            return {"error": "Internal error occurred"}, 500

    # ✅ PUT update existing order
    @with_tenant_session_and_user
    def put(self, tenant_session, **kwargs):
        try:
            json_data = request.get_json(force=True)
            if not json_data:
                return {"error": "No input data provided"}, 400

            order_id = json_data.get("id")
            if not order_id:
                return {"error": "Order ID required"}, 400

            order = tenant_session.query(Orders).get(order_id)
            if not order:
                return {"error": "Order not found"}, 404

            # Update basic fields
            order.user_id = json_data.get("user_id", order.user_id)
            order.received_date = json_data.get("received_date", order.received_date)
            order.taken_by = json_data.get("taken_by", order.taken_by)
            order.taken_by_phone_no = json_data.get("taken_by_phone_no", order.taken_by_phone_no)

            total_amount = 0

            medicines_data = json_data.get("medicines", [])
            lab_tests_data = json_data.get("lab_tests", [])
            surgeries_data = json_data.get("surgeries", [])

            # Get existing items to determine which ones to update vs delete
            existing_medicines = {item.id: item for item in tenant_session.query(PurchaseOrder).filter_by(order_id=order.id).all()}
            existing_lab_tests = {item.id: item for item in tenant_session.query(PurchaseTest).filter_by(order_id=order.id).all()}
            existing_surgeries = {item.id: item for item in tenant_session.query(PurchaseSurgery).filter_by(order_id=order.id).all()}

            # ✅ STEP 1: Handle inventory adjustments for medicines
            medicine_ids_to_keep = set()
            
            # First, restore stock for medicines that are being removed
            for existing_id, existing_medicine in existing_medicines.items():
                # Check if this medicine is being kept in the update
                medicine_still_exists = any(
                    item.get("id") == existing_id for item in medicines_data
                )
                
                if not medicine_still_exists:
                    # Restore stock for removed medicine
                    medicine_stock = tenant_session.query(MedicineStock).filter_by(
                        medicine_id=existing_medicine.medicine_id
                    ).first()
                    if medicine_stock:
                        medicine_stock.quantity += existing_medicine.quantity
                        tenant_session.add(medicine_stock)

            # Now process the updated medicines
            for item_data in medicines_data:
                item_id = item_data.get("id")
                medicine_id = item_data.get("medicine_id")
                quantity = item_data.get("quantity")

                if not medicine_id or quantity is None:
                    tenant_session.rollback()
                    return {"error": "Each medicine item must have medicine_id and quantity"}, 400

                medicine = tenant_session.query(Medicine).get(medicine_id)
                if not medicine:
                    tenant_session.rollback()
                    return {"error": f"Medicine ID {medicine_id} not found"}, 404

                medicine_stock = tenant_session.query(MedicineStock).filter_by(medicine_id=medicine_id).first()
                if not medicine_stock:
                    tenant_session.rollback()
                    return {"error": f"No stock found for Medicine ID {medicine_id}"}, 404
                
                # Check stock availability for new quantity
                if item_id and item_id in existing_medicines:
                    # Updating existing medicine - calculate quantity difference
                    existing_quantity = existing_medicines[item_id].quantity
                    quantity_diff = quantity - existing_quantity
                    
                    if quantity_diff > 0 and int(medicine_stock.quantity) < quantity_diff:
                        tenant_session.rollback()
                        return {"error": f"Insufficient stock for Medicine ID {medicine_id}. Available: {int(medicine_stock.quantity)}, Needed: {quantity_diff}"}, 400
                    
                    # Update inventory based on quantity difference
                    if quantity_diff != 0:
                        medicine_stock.quantity -= quantity_diff
                        if int(medicine_stock.quantity) < 0:
                            tenant_session.rollback()
                            return {"error": f"Stock went negative for Medicine ID {medicine_id}"}, 400
                        tenant_session.add(medicine_stock)
                else:
                    # Adding new medicine - check stock
                    if int(medicine_stock.quantity) < quantity:
                        tenant_session.rollback()
                        return {"error": f"Insufficient stock for Medicine ID {medicine_id}. Available: {int(medicine_stock.quantity)}, Requested: {quantity}"}, 400
                    
                    # Decrement stock for new medicine
                    medicine_stock.quantity -= quantity
                    tenant_session.add(medicine_stock)

                total_amount += (Decimal(medicine_stock.price) if medicine_stock.price else Decimal('0')) * int(quantity)

                if item_id and item_id in existing_medicines:
                    # Update existing medicine item
                    medicine_item = existing_medicines[item_id]
                    medicine_item.medicine_id = medicine_id
                    medicine_item.quantity = quantity
                    medicine_ids_to_keep.add(item_id)
                else:
                    # Add new medicine item
                    PurchaseOrder.tenant_session = tenant_session
                    new_item = PurchaseOrder(
                        order_id=order.id,
                        medicine_id=medicine_id,
                        quantity=quantity,
                    )
                    tenant_session.add(new_item)

            # Delete medicine items that are not in the updated data
            for item_id, medicine_item in existing_medicines.items():
                if item_id not in medicine_ids_to_keep:
                    tenant_session.delete(medicine_item)

            # Process lab tests
            lab_test_ids_to_keep = set()
            for item_data in lab_tests_data:
                item_id = item_data.get("id")
                test_id = item_data.get("test_id")
                status = item_data.get("status", 'pending')

                if not test_id:
                    tenant_session.rollback()
                    return {"error": "Each lab_test item must have test_id"}, 400

                lab_test = tenant_session.query(LabTest).get(test_id)
                if not lab_test:
                    tenant_session.rollback()
                    return {"error": f"Lab Test ID {test_id} not found"}, 404
                
                price = Decimal(lab_test.price) if hasattr(lab_test, 'price') and lab_test.price else Decimal('0')
                total_amount += price

                if item_id and item_id in existing_lab_tests:
                    # Update existing lab test
                    lab_test = existing_lab_tests[item_id]
                    lab_test.test_id = test_id
                    lab_test.status = status
                    lab_test_ids_to_keep.add(item_id)
                else:
                    # Add new lab test
                    PurchaseTest.tenant_session = tenant_session
                    new_test = PurchaseTest(
                        order_id=order.id,
                        test_id=test_id,
                        status=status
                    )
                    tenant_session.add(new_test)

            # Delete lab test items that are not in the updated data
            for item_id, lab_test in existing_lab_tests.items():
                if item_id not in lab_test_ids_to_keep:
                    tenant_session.delete(lab_test)

            # Process surgeries
            surgery_ids_to_keep = set()
            for item_data in surgeries_data:
                item_id = item_data.get("id")
                surgery_type_id = item_data.get("surgery_type_id")
                price = item_data.get("price", 0)
                scheduled_date = item_data.get("scheduled_date")
                scheduled_start_time = item_data.get("scheduled_start_time")
                scheduled_end_time = item_data.get("scheduled_end_time")
                status = item_data.get("status", "SCHEDULED")
                notes = item_data.get("notes")
                operation_theatre_id=item_data.get("operation_theatre_id")

                if not surgery_type_id:
                    tenant_session.rollback()
                    return {"error": "Each surgery item must have surgery_type_id"}, 400

                surgery_type = tenant_session.query(SurgeryType).get(surgery_type_id)
                if not surgery_type:
                    tenant_session.rollback()
                    return {"error": f"Surgery Type ID {surgery_type_id} not found"}, 404

                if item_id and item_id in existing_surgeries:
                    # Update existing surgery
                    surgery = existing_surgeries[item_id]
                    surgery.surgery_type_id = surgery_type_id
                    surgery.price = price
                    surgery.scheduled_date = scheduled_date
                    surgery.status = status
                    surgery.notes = notes
                    surgery.scheduled_start_time = scheduled_start_time
                    surgery.scheduled_end_time = scheduled_end_time
                    surgery.operation_theatre_id = operation_theatre_id
                    surgery_ids_to_keep.add(item_id)
                else:
                    # Add new surgery
                    PurchaseSurgery.tenant_session = tenant_session
                    purchase_surgery = PurchaseSurgery(
                        order_id=order.id,
                        operation_theatre_id=operation_theatre_id,
                        surgery_type_id=surgery_type_id,
                        price=price,
                        scheduled_date=scheduled_date,
                        status=status,
                        scheduled_start_time = scheduled_start_time,
                        scheduled_end_time = scheduled_end_time,
                        notes=notes
                    )
                    tenant_session.add(purchase_surgery)

                total_amount += price

            # Delete surgery items that are not in the updated data
            for item_id, surgery in existing_surgeries.items():
                if item_id not in surgery_ids_to_keep:
                    tenant_session.delete(surgery)

            Billing.tenant_session = tenant_session
            billing = tenant_session.query(Billing).filter_by(order_id=order.id).first()
            if billing:
                billing.total_amount = total_amount
            else:
                Billing.tenant_session = tenant_session
                billing = Billing(
                    total_amount=total_amount,
                    order_id=order.id
                )
                tenant_session.add(billing)

            tenant_session.commit()
            
            # 🔹 Activity log for inventory update
            log_activity("ORDER_UPDATED_WITH_INVENTORY_ADJUSTMENT", details=json.dumps({
                "order_id": order.id,
                "medicines_updated": len(medicines_data),
                "total_amount": float(total_amount)
            }))
            
            return order_serializer.dump(order), 200

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {ie.orig}"}, 400
        except Exception as e:
            tenant_session.rollback()
            logger.exception("Error updating order")
            return {"error": "Internal error occurred"}, 500
        
    # ✅ DELETE order (and its items)
    @with_tenant_session_and_user
    def delete(self, tenant_session, **kwargs):
        try:
            order_id = request.args.get("id")
            if not order_id:
                return {"error": "Order ID required"}, 400

            order = tenant_session.query(Orders).get(order_id)
            if not order:
                return {"error": "Order not found"}, 404

            # ✅ RESTORE INVENTORY before deleting order
            for medicine_item in order.medicines:
                medicine_stock = tenant_session.query(MedicineStock).filter_by(
                    medicine_id=medicine_item.medicine_id
                ).first()
                if medicine_stock:
                    medicine_stock.quantity += medicine_item.quantity
                    tenant_session.add(medicine_stock)

            tenant_session.query(PurchaseOrder).filter_by(order_id=order.id).delete()
            tenant_session.delete(order)
            tenant_session.commit()

            # 🔹 Activity log for inventory restoration
            log_activity("ORDER_DELETED_WITH_INVENTORY_RESTORED", details=json.dumps({
                "order_id": order_id,
                "medicines_restored": len(order.medicines)
            }))

            return {"message": "Order and its items deleted successfully, inventory restored"}, 200

        except IntegrityError as ie:
            tenant_session.rollback()
            return {"error": f"Database integrity error: {ie.orig}"}, 400
        except Exception as e:
            tenant_session.rollback()
            logger.exception("Error deleting order")
            return {"error": "Internal error occurred"}, 500