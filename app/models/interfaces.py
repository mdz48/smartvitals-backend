import enum

class userRole(enum.Enum):
    ADMIN = "admin"
    DOCTOR = "doctor"
    PATIENT = "patient"
    
class userGender(enum.Enum):
    MALE = 'male'
    FEMALE = 'female'
    OTHER = 'other'
