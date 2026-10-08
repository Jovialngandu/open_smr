from rest_framework.exceptions import APIException

class EmailServiceError(APIException):
    status_code = 400
    default_detail = "Error lors des l'envoie"
    default_code = "email_service_error"
    