from django.test import TestCase, Client
from django.urls import reverse
from myapp.models import Course
from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from myapp.models import Course
from myapp.views import shoppingCart, addToCart
from datetime import time
from django.test import TestCase, RequestFactory
from myapp.views import shoppingCart
from datetime import datetime

        
#class TestViewRenders(TestCase):
#    def setUp(self):
#       self.client = Client()
#
#    def test_profile_render(self):
#        response = self.client.get(reverse("api_data"))
#        self.assertTemplateUsed(response, 'myapp/courses.html')
        
    #def test_shoppingCart_render(self):
        #response = self.client.get(reverse('shoppingCart'))
        #self.assertTemplateUsed(response, 'myapp/shoppingCart.html')
        
#class Test404Error(TestCase):
#    def setUp(self):
#        self.client = Client()
#    def test404(self):
#        url = "129861yhuf.com"
#        response = self.client.get(url)
#        self.assertEqual(response.status_code, 404)
        
class Test200Response(TestCase):
    def setup(self):
        self.client = Client()
    def test200(self):
        url = reverse('api_data_search')
        response = self.client.get(url)
        self.assertEqual(response.status_code,200)
            
"""
class testShoppingCart(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='user', password='pass')
        self.course1 = Course.objects.create()
        self.course1.course_added_to_cart.add(self.user)
        self.course2 = Course.objects.create()
        self.course2.course_added_to_schedule.add(self.user)
        self.url = reverse('shoppingCart')
        
    def testusercourses(self):
        self.client.login(username='user', password='pass')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'myapp/shoppingCart.html')
        self.assertContains(response, 'Cart')
#       self.assertQuerysetEqual(response.context['courses_in_cart'], [repr(self.course1)])
        #self.assertQuerysetEqual(response.context['courses_in_calendar'], [repr(self.course2)])
"""


class ShoppingCartViewTest(TestCase):

    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='testpassword'
        )

        self.course1 = Course.objects.create(
            course_subject='CS101',
            course_mnemonic='CS',
            course_catalog_nbr='101',
            course_enrollment_availability='20',
            #course_added_to_cart=self.user,
            #course_added_to_schedule=self.user,
            #start_time=datetime.now(),
            #end_time=datetime.now()
        )
        self.course1.course_added_to_cart.add(self.user)
        self.course1.course_added_to_schedule.add(self.user)
        self.course2 = Course.objects.create(
            course_subject='CS102',
            course_mnemonic='CS',
            course_catalog_nbr='102',
            course_enrollment_availability='25',
            #start_time=datetime.now(),
            #end_time=datetime.now()
        )
        self.course2.course_added_to_cart.add(self.user)
        self.course2.course_added_to_schedule.add(self.user)
    def test_shopping_cart_authenticated(self):
        request = self.factory.get('/shoppingCart')
        request.user = self.user

        response = shoppingCart(request)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'CS101')
        self.assertContains(response, 'CS102')


#class AddToCartViewTest(TestCase):
#   def setUp(self):
#        self.user = User.objects.create_user(username='testuser', password='testpass')
#        self.course = Course.objects.create()
#        self.url = reverse('addToCart', args=[self.course.pk])
        
#        self.client.login(username='testuser', password='testpass')
#        response = self.client.get(self.url)
#        self.assertEqual(response.status_code, 302)
#        self.assertIn(self.user, self.course.course_added_to_cart.all())

class ProfileViewTest(TestCase):
    
    def setUp(self):
        self.client = Client()
        self.username = 'user'
        self.password = 'pass'
        self.user = User.objects.create_user(self.username, password=self.password)
        
    def profileviewtest(self):
        self.client.login(username=self.username, password=self.password)
        response = self.client.get(reverse('profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Go to Calendar')


class calendarTest(TestCase):
    def seecalendar(self):
        client = Client()
        user = User.objects.create_user(username='user', password='pass')
        client.login(username='user', password='pass')
        course = Course.objects.create(course_days_of_week='MoWeFr', course_start_time='08:00:00', course_end_time='09:00:00')
        course.course_added_to_schedule.add(user)
        response = client.get(reverse('calendar'))
        self.assertContains(response, 'course')
        
    def testcorrecttime(self):
        client = Client()
        user = User.objects.create_user(username='user', password='pass')
        client.login(username='user', password='pass')
        course = Course.objects.create( course_days_of_week='MoWeFr', course_start_time='08:00 AM', course_end_time='09:00 AM')
        course.course_added_to_schedule.add(user)
        response = client.get(reverse('calendar'))
        self.assertContains(response, 'course')
        self.assertContains(response, 'Mo')
        self.assertContains(response, '08:00 AM')
        
    def overlappingcourses(self):
        client = Client()
        user = User.objects.create_user(username='user', password='password')
        client.login(username='user', password='password')
        course1 = Course.objects.create(course_days_of_week='Mo', course_start_time='08:00 AM', course_end_time='09:00 AM')
        course2 = Course.objects.create(course_days_of_week='Mo', course_start_time='08:30 AM', course_end_time='09:30 AM')
        course1.course_added_to_schedule.add(user)
        course2.course_added_to_schedule.add(user)
        response = client.get(reverse('calendar'))
        self.assertNotContains(response, 'course2')
        self.assertNotContains(response, 'course1')