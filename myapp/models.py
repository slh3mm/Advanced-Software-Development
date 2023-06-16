from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.auth.models import AbstractUser

# Create your models here.
class Course(models.Model):
    course_id = models.CharField(max_length=255)
    course_section = models.CharField(max_length=255)
    course_catalog_nbr = models.CharField(max_length=255)

    course_subject = models.CharField(max_length=255)
    course_mnemonic = models.CharField(max_length=255)
    course_credits = models.CharField(max_length=255, default="")
    course_type = models.CharField(max_length=255, default="")

    course_instructor = models.CharField(max_length=255)
    course_location = models.CharField(max_length=255)

    course_size = models.CharField(max_length=255)
    course_enrollment_total = models.CharField(max_length=255)
    course_enrollment_availability = models.CharField(max_length=255)
    course_waitlist_total = models.CharField(max_length=255)
    course_waitlist_cap = models.CharField(max_length=255)

    course_days_of_week = models.CharField(max_length=255)
    course_start_time = models.CharField(max_length=255)
    course_end_time = models.CharField(max_length=255)

    course_added_to_cart = models.ManyToManyField(User, related_name="courses")
    course_added_to_schedule = models.ManyToManyField(User, related_name="courses_in_schedule")

class Schedule(models.Model):
    #https://stackoverflow.com/questions/34305805/foreignkey-user-in-models
    #https://www.geeksforgeeks.org/datefield-django-models/
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,)
    submitted_time = models.DateTimeField(auto_now_add=True)
    courses = models.ManyToManyField(Course)
    status = models.BooleanField(default=False)
    isRejected = models.BooleanField(default=False)


