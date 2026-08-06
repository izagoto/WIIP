from backend.models.user import UserRole

READ_ROLES = (UserRole.ADMIN.value, UserRole.INVESTIGATOR.value, UserRole.VIEWER.value)
WRITE_ROLES = (UserRole.ADMIN.value, UserRole.INVESTIGATOR.value)
ADMIN_ROLES = (UserRole.ADMIN.value,)
