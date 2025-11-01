import io
import csv
import pandas as pd
import logging
from flask import Response, send_file, request
from flask_jwt_extended import jwt_required
from flask_restful import Resource
from sqlalchemy import func, or_

from Models.Department import Department
from Models.Users import User
from Models.UserType import UserType
from Serializers.DepartmentSerializers import department_serializers
from Serializers.UserSerializers import user_serializers
from new import with_tenant_session_and_user
from utils.logger import log_activity

logger = logging.getLogger(__name__)


class ExportResource(Resource):
    method_decorators = [jwt_required()]

    @with_tenant_session_and_user
    def get(self, tenant_session, **kwargs):
        """
        Export data from a table.
        Example:
            /api/export?type=departments&format=csv
            /api/export?type=departments&format=excel
        """
        try:
            table = request.args.get("type", "").lower()
            export_format = request.args.get("format", "csv").lower()

            if table == "departments":
                # 🔹 Fetch departments
                departments = (
                    tenant_session.query(Department)
                    .filter_by(is_deleted=False)
                    .order_by(Department.id)
                    .all()
                )
                result = department_serializers.dump(departments)

                if not result:
                    return {"message": "No departments found to export."}, 404

                # 🔹 Export as CSV
                if export_format == "csv":
                    output = io.StringIO()
                    writer = csv.DictWriter(output, fieldnames=result[0].keys())
                    writer.writeheader()
                    writer.writerows(result)
                    output.seek(0)

                    log_activity("EXPORT_DEPARTMENTS_CSV", details={"count": len(result)})

                    return Response(
                        output,
                        mimetype="text/csv",
                        headers={
                            "Content-Disposition": "attachment; filename=departments.csv"
                        },
                    )

                # 🔹 Export as Excel
                elif export_format == "excel":
                    output = io.BytesIO()
                    df = pd.DataFrame(result)
                    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                        df.to_excel(writer, index=False, sheet_name="Departments")
                    output.seek(0)

                    log_activity("EXPORT_DEPARTMENTS_EXCEL", details={"count": len(result)})

                    return send_file(
                        output,
                        as_attachment=True,
                        download_name="departments.xlsx",
                        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )

                else:
                    return {"message": "Invalid format. Use 'csv' or 'excel'."}, 400
            if table == "users":
                user_type = request.args.get("user_type", "").lower()
                # 🔹 Fetch departments
                users_query = tenant_session.query(User)
                users_query = users_query.join(UserType)
                if (user_type):
                    users_query = users_query.filter(func.lower(UserType.type) == user_type)
                users_query = (users_query
                    .filter_by(is_deleted=False)
                    .order_by(User.id)
                    .all()
                )
                result = user_serializers.dump(users_query)

                if not result:
                    return {"message": "No users found to export."}, 404

                # 🔹 Export as CSV
                if export_format == "csv":
                    output = io.StringIO()
                    writer = csv.DictWriter(output, fieldnames=result[0].keys())
                    writer.writeheader()
                    writer.writerows(result)
                    output.seek(0)

                    log_activity(f"EXPORT_{user_type}_CSV", details={"count": len(result)})

                    return Response(
                        output,
                        mimetype="text/csv",
                        headers={
                            f"Content-Disposition": "attachment; filename={user_type}.csv"
                        },
                    )

                # 🔹 Export as Excel
                elif export_format == "excel":
                    output = io.BytesIO()
                    df = pd.DataFrame(result)
                    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
                        df.to_excel(writer, index=False, sheet_name="Departments")
                    output.seek(0)

                    log_activity(f"EXPORT_{user_type}_EXCEL", details={"count": len(result)})

                    return send_file(
                        output,
                        as_attachment=True,
                        download_name=f"{user_type}.xlsx",
                        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )

                else:
                    return {"message": "Invalid format. Use 'csv' or 'excel'."}, 400
                    

            else:
                return {"message": "Invalid type or type not supported."}, 400

        except Exception as e:
            logger.exception("Error exporting data")
            return {"message": "Internal error occurred"}, 500
