from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

class UserManager(BaseUserManager):
    use_in_migrations=True

    def create_user(self,email,password=None,**extra):
        if not email:
            raise ValueError("Email is required")
        user=self.model(email=self.normalize_email(email),**extra)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self,email,password=None,**extra):
        extra.setfault("is_staff", True)
        extra.setfault("is_superuser", True)
        extra.setfault("role", User.Role.ADMIN)
        return self.create_User(email,password,**extra)

class User(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER="customer", "Customer"
        STAFF ="staff", "Staff"
        ADMIN ="admin", "Admin"

    Username=None
    email=models.EmailField(unique=True)
    phone=models.CharField(max_length=20, blank=True)
    role=models.CharField(max_length=10,choices=Role.choices,default=Role.CUSTOMER)

    USERNAME_FIELD="email"
    REQUIRED_FIELDS=[]

    objects=UserManager()



