from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template import loader
from django.views import generic
from django.shortcuts import redirect
from django.http import HttpResponseRedirect
from myapp.models import Course, Schedule
from django.urls import reverse
from django.contrib import messages
import requests
from datetime import datetime
from django.core import serializers
import re
import json

def download_classes():
    print("Starting!")
    url = 'https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_ClassSearchOptions?institution=UVA01&term=1232'
    categories = requests.get(url).json()
    subs = categories.get("subjects")
    orgs = categories.get("acad_orgs")
    i = 0
    subjects = Course.objects.values_list('course_mnemonic', flat=True).distinct()
    for info in subs:
        subject = info['subject']
        print(subject+" "+str(i))
        i += 1
        if subject in subjects:
            continue
        for page_num in range(1,6):
            class_url = 'https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.' \
            'IScript_ClassSearch?institution=UVA01&term=1232&subject=%s&page=%s' % (subject,str(page_num))
            print(class_url)
            classes = requests.get(class_url).json()
            if len(classes) == 0:
                continue
            for course in classes:
                if len(course.get("meetings")) == 0:
                    continue
                start = course.get("meetings")[0]['start_time']
                if (start != ""):
                    start = datetime.strptime(course.get("meetings")[0]['start_time'], '%H.%M.%S.%f%z').strftime('%I:%M %p')
                end = course.get("meetings")[0]['end_time']
                if (end != ""):
                    end = datetime.strptime(course.get("meetings")[0]['end_time'], '%H.%M.%S.%f%z').strftime('%I:%M %p')
                course_model_instance = Course(
                    course_id=course.get('crse_id'),
                    course_section=course.get('class_section'),
                    course_catalog_nbr=course.get('catalog_nbr'),

                    course_subject=course.get('descr'),
                    course_mnemonic=course.get('subject'),
                    course_credits=course.get('units'),
                    course_type=course.get('section_type'),

                    course_instructor=course.get("instructors")[0]['name'],
                    course_location=course.get("meetings")[0]['facility_descr'],

                    course_size=course.get('class_capacity'),
                    course_enrollment_total=course.get('enrollment_total'),
                    course_enrollment_availability = course.get('enrollment_available'),
                    course_waitlist_total=course.get('wait_tot'),
                    course_waitlist_cap=course.get('wait_cap'),

                    course_days_of_week=course.get("meetings")[0]['days'],
                    course_start_time=start,
                    course_end_time=end,
                )
                if (course_model_instance not in Course.objects.all()):
                    course_model_instance.save()
                    course_model_instance.course_added_to_cart.set([])
                    course_model_instance.save()
    # print()
    # url = 'https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.IScript_ClassSearchOptions?institution=UVA01&term=1232'
    # categories = requests.get(url).json()
    # respons = categories.get("subjects")
    # i = 0
    # for info in respons:
    #     subject = info['subject']
    #     print(subject+" "+str(i))
    #     i += 1
class IndexView(generic.ListView):
    #download_classes()
    template_name='myapp/index.html'
    def get_queryset(self):
        return

def courseforum_view(request):
    return redirect('https://thecourseforum.com/')

def profile(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            schedules = Schedule.objects.all().filter(isRejected=False, status = False)
            template = loader.get_template('myapp/adminHome.html')
            return HttpResponse(template.render({'schedules':schedules}, request))
        
        usersSchedule = None
        if(Schedule.objects.filter(author = request.user).exists()):
            usersSchedule = Schedule.objects.get(author = request.user)
        # print(usersSchedule)  
        template = loader.get_template('myapp/profile.html')
        return HttpResponse(template.render({'usersSchedule' : usersSchedule}, request))
    else:
        response = redirect('/accounts/login')
        return response
    
class CourseView(generic.ListView):
    template_name='myapp/courses.html'
    def get_queryset(self):
        return

    
def createAdmin(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_superuser = True
            user.save()
            return redirect('login/?')
    else:
        form = UserCreationForm()
    return render(request, "myapp/createAdmin.html", {'form': form})

class CalendarObj():
    def __init__(self, course):
        self.course_mnemonic = course.course_mnemonic
        self.course_catalog_nbr = course.course_catalog_nbr
        self.course_id = self.course_mnemonic + " " + self.course_catalog_nbr
        self.course_days_of_week = course.course_days_of_week
        self.course_subject = course.course_subject
        self.course_instructor = course.course_instructor
        self.course_location = course.course_location
        self.course_start_time = course.course_start_time
        self.course_end_time = course.course_end_time
        self.course_added_to_schedule = course.course_added_to_schedule
        self.course_added_to_cart = course.course_added_to_cart
        self.coursenum = ""
        self.conflict = False
        self.start_tag, self.end_tag = self.populate_tags() 
        self.short_class = self.populate_time()
    
    def populate_tags(self):
        start_tag = str(self.course_start_time)[0:2] + "_" + str(self.course_start_time)[3:5]
        end_tag = str(self.course_end_time)[0:2] + "_" + str(self.course_end_time)[3:5]
        if start_tag[0] == '0':
            start_tag = start_tag[1:]
        if end_tag[0] == '0':
            end_tag = end_tag[1:]
        
        return start_tag, end_tag
    
    def populate_time(self):
        if self.course_start_time == "":
            return True
        start = datetime.strptime(self.course_start_time, "%I:%M %p")
        end = datetime.strptime(self.course_end_time, "%I:%M %p")
        diff = end-start
        mins = int(diff.total_seconds()/ 60)
        # print(self.course_subject)
        # print(mins)
        if mins <= 50:
            return True
        else:
            return False

# def api_data(request):
#     class_dept = request.GET.get("classes")
#     url = 'https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.' \
#             'IScript_ClassSearch?institution=UVA01&term=1232&subject=%s&page=1' % class_dept
#     classes = requests.get(url).json()
#     if request.method == 'GET':
#         #return HttpResponse(url)
#         #courses_in_calendar = Course.objects.filter(course_added_to_schedule = request.user)
#         class_objects = []
#         if(len(classes) > 0):
#             for course in classes:
#                 if(not Course.objects.filter(course_id= course.get("crse_id"), course_section= course.get("class_section"), course_catalog_nbr=course.get("catalog_nbr"), course_instructor = course.get("instructors")[0]['name']).exists()):
#                     start = course.get("meetings")[0]['start_time']
#                     if (start != ""):
#                         start = datetime.datetime.strptime(course.get("meetings")[0]['start_time'], '%H.%M.%S.%f%z').strftime('%I:%M %p')
#                     end = course.get("meetings")[0]['end_time']
#                     if (end != ""):
#                         end = datetime.datetime.strptime(course.get("meetings")[0]['end_time'], '%H.%M.%S.%f%z').strftime('%I:%M %p')
#                     course_model_instance = Course(
#                         course_id = course.get('crse_id'),
#                         course_section = course.get('class_section'),
#                         course_catalog_nbr = course.get('catalog_nbr'),

#                         course_subject = course.get('descr'),
#                         course_mnemonic = course.get('subject'),

#                         course_instructor = course.get("instructors")[0]['name'],
#                         course_location = course.get("meetings")[0]['facility_descr'],

#                         course_size = course.get('class_capacity'),
#                         course_enrollment_total = course.get('enrollment_total'),
#                         course_enrollment_availability = course.get('enrollment_available'),
#                         course_waitlist_total = course.get('wait_tot'),
#                         course_waitlist_cap = course.get('wait_cap'),

#                         course_days_of_week = course.get("meetings")[0]['days'],
#                         course_start_time = start,
#                         course_end_time = end,

#                     )
#                     course_model_instance.save()
#                     course_model_instance.course_added_to_cart.set([])
#                     course_model_instance.save()
#                 #For updating info if users join / get off waitlist and as enrollment size changes
#                 specific_course = Course.objects.get(course_id= course.get("crse_id"), course_section= course.get("class_section"), course_catalog_nbr=course.get("catalog_nbr"), course_instructor = course.get("instructors")[0]['name'])    
#                 if(specific_course.course_enrollment_total != course.get('enrollment_total') or 
#                    specific_course.course_enrollment_availability != course.get('enrollment_available') or
#                    specific_course.course_waitlist_total != course.get('wait_tot') or 
#                    specific_course.course_waitlist_cap != course.get('wait_cap')):
#                         specific_course.course_enrollment_total = course.get('enrollment_total'),
#                         specific_course.course_enrollment_availability = course.get('enrollment_available') ,
#                         specific_course.course_waitlist_total = course.get('wait_tot'),
#                         specific_course.course_waitlist_cap = course.get('wait_cap'),
#                         specific_course.save()
#                 class_objects.append(specific_course)
#         #primary_keys = [instance.pk for instance in class_objects]
#         classes_json = json.dumps(classes)
#         # print(classes)
#         finalList = zip(class_objects, classes)
#         context = {'content': finalList, 'classes_json': classes_json}
#         return render(request, 'myapp/courses.html', context)
#         #return render(request, 'myapp/courses.html', {'classes' : classes, 'primary_keys' : primary_keys})
#     else:
#         classes_json = json.dumps(classes)
#         context = {'classes_json': classes_json}
#         # print(classes_json)
#         return render(request, 'myapp/courses.html', context)


def api_data_search(request):
    # print("api_data_search was called")
    class_dept = request.GET.get("classes")
    query = request.GET.get("query")
    courses = []
    if query:
        searched = False
        mnemonics = Course.objects.values_list('course_mnemonic',flat=True).distinct()
        #Search by mnemonic and course number
        if query.split()[0].upper() in mnemonics and len(query.split()) == 2 and not searched:
            mnemonic = query.split()[0].upper()
            number = query.split()[1]
            courses = Course.objects.filter(course_mnemonic=mnemonic, course_catalog_nbr=number)
            searched = True
            print("Mnemonic and Course Number")
        #Search by mnemonic
        if query.split()[0].upper() in mnemonics and len(query.split()) == 1 and not searched:
            mnemonic = query.split()[0].upper()
            courses = Course.objects.filter(course_mnemonic=mnemonic)
            # for course in courses:
            #     print(course.course_subject)
            searched = True
            print("Mnemonic")
        #Search by course number
        nums = Course.objects.values_list('course_catalog_nbr',flat=True).distinct()
        if query.split()[0] in nums and len(query.split()) == 1 and not searched:
            number = query.split()[0]
            courses = Course.objects.filter(course_catalog_nbr=number)
            searched = True
            print("Course Number")
        #Search by course id
        ids = Course.objects.values_list('course_id',flat=True).distinct()
        if query.split()[0] in ids and len(query.split()) == 1 and not searched:
            id = query.split()[0]
            courses = Course.objects.filter(course_id=str(id))
            searched = True
            print("Course ID")
        #Search by Professor
        professors = Course.objects.values_list('course_instructor',flat=True).distinct()
        professors_lower = {}
        for professor in professors:
            professors_lower[professor.lower()] = professor
        if query.lower() in professors_lower and not searched:
            courses = Course.objects.filter(course_instructor=professors_lower[query.lower()])
            searched = True
            print("Professor")
        #Search by description
        if not searched:
            courses = Course.objects.filter(course_subject = query)
            print("Description")
    else:
        url = 'https://sisuva.admin.virginia.edu/psc/ihprd/UVSS/SA/s/WEBLIB_HCX_CM.H_CLASS_SEARCH.FieldFormula.' \
            'IScript_ClassSearch?institution=UVA01&term=1232&subject=%s&page=1' % class_dept
        classes = requests.get(url).json()
    if request.method == 'GET':
        enrollment_dict = {}
        courses = sorted(courses, key=lambda obj: obj.course_catalog_nbr)
        # courses_json = serializers.serialize('json', courses)
        for course in courses:
            if(course.course_enrollment_availability == ''):
                enrollment_dict[course] = 0
            else:
                if(re.sub("[^0-9]", "", course.course_enrollment_availability) == ''):
                    enrollment_dict[course] = 0
                else:
                    enrollment_dict[course] = int(re.sub("[^0-9]", "", course.course_enrollment_availability))
        print(courses)
        context = {'courses': courses, 'dict' : enrollment_dict}

        return render(request, 'myapp/courses.html', context)
    else:
        classes_json = json.dumps(classes)
        context = {'classes_json': classes_json}
        return render(request, 'myapp/courses.html', context)
    

def shoppingCart(request):
    if(request.user.is_authenticated):  
        current_user = request.user
        all_courses = Course.objects.all()
        courses_in_cart = []
        courses_in_cart = Course.objects.filter(course_added_to_cart = current_user)
        courses_in_calendar = Course.objects.filter(course_added_to_schedule = current_user)
        courseVar = 'course'
        for cart_course in courses_in_cart:
            for cal_course in courses_in_calendar:
                if (cart_course not in courses_in_calendar):
                    if dtime_conflict(cart_course, cal_course) and (cart_course != cal_course):
                        #cart_course.color = "#ff7770"
                        print(cart_course.course_subject+" "+cal_course.course_subject)
                        cart_course.conflict = True
                    #else:
                        #cart_course.conflict = False
                        #cart_course.color = "#42d67b"
        enrollment_dict = {}
        for course in courses_in_cart:
            enrollment_dict[course] = int(re.sub("[^0-9]", "", course.course_enrollment_availability))
        return render(request, 'myapp/shoppingCart.html', {'courses_in_cart': courses_in_cart, 'courses_in_calendar': courses_in_calendar, 'courseVar': courseVar, 'dict': enrollment_dict})
    else:
        response = redirect('/accounts/login')
        return response

def addToCart(request, pk):
    if(request.user.is_authenticated):  
        #https://www.youtube.com/watch?v=PXqRPqDjDgc
        course = get_object_or_404(Course, pk = pk)
        course.course_added_to_cart.add(request.user)
        # course.course_enrollment_total += 1
        course.save()
        messages.success(request,"Successfully added "+course.course_mnemonic+" "+course.course_catalog_nbr+" to your cart!")
        return shoppingCart(request)
    else:
        response = redirect('/accounts/login')
        return response

def removeFromCart(request, pk):
    #Get user from route and then remove the associated course and save
    course = get_object_or_404(Course, pk = pk)
    course.course_added_to_cart.remove(request.user)
    # course.course_enrollment_total -= 1
    course.save()
    messages.success(request,"Successfully removed "+course.course_mnemonic+" "+course.course_catalog_nbr+" from your cart!")
    return shoppingCart(request)

def addToSchedule(request, pk):
    if(request.user.is_authenticated):
        course = get_object_or_404(Course, pk = pk)
        courses_in_calendar = Course.objects.filter(course_added_to_schedule = request.user)
        conflict = False
        conflict_course = course
        # dummy = courses_in_calendar[2]
        # print(course.course_days_of_week+' '+course.course_start_time+' - '+course.course_end_time)
        # print(dummy.course_start_time+' - '+dummy.course_end_time)
        # print(course.course_start_time <= dummy.course_end_time)
        # print(dummy.course_start_time <= course.course_end_time)
        # print(type(course.course_start_time))
        # print(dtime_conflict(course,dummy))
        for cal_course in courses_in_calendar:
            # print(cal_course.course_subject)
            if dtime_conflict(course, cal_course):
                conflict = True
                # print(cal_course.course_subject)
                conflict_course = cal_course
                break
        if not conflict:
            messages.success(request,"Successfully added "+course.course_mnemonic+" "+course.course_catalog_nbr+" to your schedule!")
            course.course_added_to_schedule.add(request.user)
            course.save()
            return calendar(request)
        else:
            messages.error(request, "Could not add "+course.course_mnemonic+" "+course.course_catalog_nbr+" due to time conflict with "+
                           conflict_course.course_mnemonic+" "+conflict_course.course_catalog_nbr+".")
            #return HttpResponseRedirect('accounts/profile/shopping_cart')
            #return render(request, 'myapp/shoppingCart.html')
            #return redirect('.')
            #return HttpResponseRedirect(request.path_info)
            return HttpResponseRedirect(request.META.get('HTTP_REFERER'))
    else:
        response = redirect('/accounts/login')
        return response

def removeFromSchedule(request, pk):
    if(request.user.is_authenticated):
        course = get_object_or_404(Course, pk = pk)
        course.course_added_to_schedule.remove(request.user)
        course.save()
        messages.success(request,"Successfully removed "+course.course_mnemonic+" "+course.course_catalog_nbr+" from your schedule!")
        return shoppingCart(request)
    else:
        response = redirect('/accounts/login')
        return response
    
def createSchedule(request, pk):
    if(request.method == 'POST'):

        #https://docs.djangoproject.com/en/4.2/topics/db/queries/
        #https://stackoverflow.com/questions/24963761/django-filtering-a-model-that-contains-a-field-that-stores-regex 

        if(Schedule.objects.filter(author = request.user).exists()):
            Schedule.objects.filter(author = request.user).delete() 

        current_schedule = Schedule.objects.create(author = request.user)

        #https://stackoverflow.com/questions/5481890/django-does-the-orm-support-the-sql-in-operator 
        courses_in_schedule_to_add = Course.objects.filter(course_added_to_schedule__in= [request.user.id])
        for curr_course in courses_in_schedule_to_add:
            current_schedule.courses.add(curr_course)
        current_schedule.save()    
        
        return calendar(request)


    else: 
        #Not trying to submit a course, should not go to this url
        response = redirect('/accounts/login')
        return response



def approveSchedule(request):
    #https://stackoverflow.com/questions/1746377/checking-for-content-in-django-request-post
    #https://docs.djangoproject.com/en/4.2/ref/request-response/
    if(request.user.is_authenticated and request.method == 'POST'): 
        if('approved' in request.POST):
            theSchedule = request.POST.get('scheduleID')
            mySchedule = get_object_or_404(Schedule, id=theSchedule)
            mySchedule.status = True 
            mySchedule.save()
        else:
            #The approve button was not pressed so therefor it must have been rejected
            theSchedule = request.POST.get('scheduleID')
            mySchedule = get_object_or_404(Schedule, id=theSchedule)
            mySchedule.isRejected = True
            mySchedule.save()

        schedules = Schedule.objects.all().filter(isRejected=False, status = False)
        template = loader.get_template('myapp/adminHome.html')
        return HttpResponse(template.render({'schedules':schedules}, request))

    else:
        response = redirect('/accounts/login')
        return response



def calendar(request):
    if(request.user.is_authenticated):  
        current_user = request.user
        courses_in_calendar = Course.objects.filter(course_added_to_schedule = current_user)
        calendar_courses = []
        seen_classes = set()
        for i in range(len(courses_in_calendar)):
            course = courses_in_calendar[i]
            calendar_course = (CalendarObj(course))
            if calendar_course.course_id not in seen_classes:
                seen_classes.add(calendar_course.course_id)
                calendar_course.coursenum = i
            calendar_courses.append(calendar_course)
        mon,tue,wed,thu,fri=[],[],[],[],[]
        error_messages = set()
        for course in calendar_courses:
            if "Mo" in course.course_days_of_week:
                if len(mon) != 0:
                    count = 0
                    for otherCourse in mon:
                        if (not time_conflict(course, otherCourse)):
                            count+= 1
                    if(count == len(mon)):
                        mon.append(course)
                    else:
                        course.course_added_to_schedule.remove(request.user)
                        courses_in_calendar = Course.objects.filter(course_added_to_schedule = current_user)
                else:
                    mon.append(course)
            if "Tu" in course.course_days_of_week:
                if len(tue) != 0:
                    count = 0
                    for otherCourse in tue:
                        if (not time_conflict(course, otherCourse)):
                            count+= 1
                    if(count == len(tue)):
                        tue.append(course)
                    else:
                        course.course_added_to_schedule.remove(request.user)
                        courses_in_calendar = Course.objects.filter(course_added_to_schedule = current_user)
                else:
                    tue.append(course)
            if "We" in course.course_days_of_week:
                if len(wed) != 0:
                    count = 0
                    for otherCourse in wed:
                        if (not time_conflict(course, otherCourse)):
                            count+= 1
                    if(count == len(wed)):
                        wed.append(course)
                    else:
                        course.course_added_to_schedule.remove(request.user)
                        courses_in_calendar = Course.objects.filter(course_added_to_schedule = current_user)
                else:
                    wed.append(course)
            if "Th" in course.course_days_of_week:
                if len(thu) != 0:
                    count = 0
                    for otherCourse in thu:
                        if (not time_conflict(course, otherCourse)):
                            count+= 1
                    if(count == len(thu)):
                        thu.append(course)
                    else:
                        course.course_added_to_schedule.remove(request.user)
                        courses_in_calendar = Course.objects.filter(course_added_to_schedule = current_user)
                else:
                    thu.append(course)
            if "Fr" in course.course_days_of_week:
                if len(fri) != 0:
                    count = 0
                    for otherCourse in fri:
                        if (not time_conflict(course, otherCourse)):
                            count+= 1
                    if(count == len(fri)):
                        fri.append(course)
                    else:
                        # message = "Could not add "+course.course_mnemonic+" "+course.course_catalog_nbr+" due to time conflict with "+otherCourse.course_mnemonic+" "+otherCourse.course_catalog_nbr+"."
                        # if message not in error_messages:
                        #     error_messages.add(message)
                        course.course_added_to_schedule.remove(request.user)
                        #course.course_added_to_cart.remove(request.user)
                        courses_in_calendar = Course.objects.filter(course_added_to_schedule = current_user)
                else:
                    fri.append(course)
        week = [mon, tue, wed, thu, fri]
        for i in range(len(week)):
            week[i] = sorted(week[i], key=lambda obj: obj.start_tag)
        week_dict = {"MON" : week[0], "TUE" : week[1], "WED" : week[2], "THU" : week[3], "FRI" : week[4]} 
        #Logic for passing the schedule object thorugh
        usersSchedule = None
        if(Schedule.objects.filter(author = request.user).exists()):
            usersSchedule = Schedule.objects.get(author = request.user)
        courseVar = 'course'
        return render(request, 'myapp/calendar.html', {'week' : week_dict, 'schedule' : week, 'courses_in_calendar': courses_in_calendar, 'usersSchedule' : usersSchedule, 'courseVar': courseVar})

    else:
        response = redirect('/accounts/login')
        return response

def time_conflict(course1, course2):
        # if (course1.course_start_time != course2.course_start_time and course1.course_end_time != course2.course_end_time 
        #     and not(course1.course_start_time > course2.course_start_time and course1.course_start_time < course2.course_end_time) and  
        #     not(course1.course_end_time > course2.course_start_time and course1.course_end_time < course2.course_end_time)):
        #     return False
        # else:
        #     return True
        if (course1.course_start_time == "" or course1.course_end_time == "" or course2.course_start_time == "" or course2.course_end_time == ""):
            return False
        c1_start = datetime.strptime(course1.course_start_time, "%I:%M %p")
        c1_end = datetime.strptime(course1.course_end_time, "%I:%M %p")
        c2_start = datetime.strptime(course2.course_start_time, "%I:%M %p")
        c2_end = datetime.strptime(course2.course_end_time, "%I:%M %p")
        if (c1_start == c2_start):
            return True
        if (c1_end == c2_end):
            return True
        if (c1_start <= c2_end and c2_start <= c1_end):
            return True
        return False

def dtime_conflict(course1, course2):
    days = ["Mo", "Tu", "We", "Th", "Fr"]
    print(course1)
    for day in days:
        if day in course1.course_days_of_week and day in course2.course_days_of_week and time_conflict(course1, course2):
            return True
    return False

    # if "Mo" in course1.course_days_of_week and "Mo" in course2.course_days_of_week:
    #     if time_conflict(course1, course2):
    #         return True
    # if "Tu" in course1.course_days_of_week and "Tu" in course2.course_days_of_week:
    #     if time_conflict(course1, course2):
    #         return True
    # if "We" in course1.course_days_of_week and "We" in course2.course_days_of_week:
    #     if time_conflict(course1, course2):
    #         return True
    # if "Th" in course1.course_days_of_week and "Th" in course2.course_days_of_week:
    #     if time_conflict(course1, course2):
    #         return True
    # if "Fr" in course1.course_days_of_week and "Fr" in course2.course_days_of_week:
    #     if time_conflict(course1, course2):
    #         return True
    # return False