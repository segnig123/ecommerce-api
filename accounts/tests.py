from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

User = get_user_model()


class RegistrationTests(APITestCase):

    def setUp(self):
        self.url = reverse('register')

        self.valid_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'StrongPassword123!',
            'first_name': 'Test',
            'last_name': 'User'
        }

    def test_user_registration(self):
        response = self.client.post(
            self.url,
            self.valid_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(
            User.objects.filter(email='test@example.com').exists()
        )

    def test_password_is_hashed(self):
        self.client.post(self.url, self.valid_data, format='json')

        user = User.objects.get(email='test@example.com')

        self.assertNotEqual(user.password, self.valid_data['password'])
        self.assertTrue(user.check_password(self.valid_data['password']))

    def test_password_is_not_returned(self):
        response = self.client.post(
            self.url,
            self.valid_data,
            format='json'
        )

        self.assertNotIn('password', response.data)

    def test_duplicate_email_registration(self):
        User.objects.create_user(
            username='existinguser',
            email='test@example.com',
            password='StrongPassword123!'
        )

        response = self.client.post(
            self.url,
            self.valid_data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_weak_password_registration(self):
        data = self.valid_data.copy()
        data['password'] = '123'

        response = self.client.post(
            self.url,
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_fields_cannot_be_assigned_through_registration(self):
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'StrongPassword123!',
            'is_staff': True,
            'is_superuser': True
        }

        response = self.client.post(
            self.url,
            data,
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        new_user = User.objects.get(email='newuser@example.com')

        self.assertFalse(new_user.is_staff)
        self.assertFalse(new_user.is_superuser)


class AuthenticationTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='authuser',
            email='auth@example.com',
            password='StrongPassword123!'
        )

        self.token_url = reverse('token_obtain_pair')
        self.profile_url = reverse('user_profile')

    def test_login_with_valid_credentials(self):
        response = self.client.post(
            self.token_url,
            {
                'username': 'authuser',
                'password': 'StrongPassword123!'
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_with_invalid_password(self):
        response = self.client.post(
            self.token_url,
            {
                'username': 'authuser',
                'password': 'WrongPassword123!'
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_profile_without_token(self):
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_access_profile_with_valid_token(self):
        response = self.client.post(
            self.token_url,
            {
                'username': 'authuser',
                'password': 'StrongPassword123!'
            },
            format='json'
        )

        access_token = response.data['access']

        self.client.credentials(
            HTTP_AUTHORIZATION=f'Bearer {access_token}'
        )

        profile_response = self.client.get(self.profile_url)

        self.assertEqual(
            profile_response.status_code,
            status.HTTP_200_OK
        )

    def test_refresh_access_token(self):
        login_response = self.client.post(
            self.token_url,
            {
                'username': 'authuser',
                'password': 'StrongPassword123!'
            },
            format='json'
        )

        refresh_token = login_response.data['refresh']

        refresh_url = reverse('token_refresh')

        response = self.client.post(
            refresh_url,
            {'refresh': refresh_token},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)


class PasswordChangeTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='passworduser',
            email='password@example.com',
            password='OldPassword123!'
        )

        self.url = reverse('change_password')
        self.client.force_authenticate(user=self.user)

    def test_change_password_successfully(self):
        response = self.client.post(
            self.url,
            {
                'old_password': 'OldPassword123!',
                'new_password': 'NewStrongPassword456!'
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.user.refresh_from_db()

        self.assertTrue(
            self.user.check_password('NewStrongPassword456!')
        )

    def test_change_password_with_wrong_old_password(self):
        response = self.client.post(
            self.url,
            {
                'old_password': 'WrongPassword123!',
                'new_password': 'NewStrongPassword456!'
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_without_authentication(self):
        self.client.force_authenticate(user=None)

        response = self.client.post(
            self.url,
            {
                'old_password': 'OldPassword123!',
                'new_password': 'NewStrongPassword456!'
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserProfileTests(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username='profileuser',
            email='profile@example.com',
            password='StrongPassword123!'
        )

        self.url = reverse('user_profile')
        self.client.force_authenticate(user=self.user)

    def test_profile_returns_authenticated_user(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'profileuser')
        self.assertEqual(response.data['email'], 'profile@example.com')


class UserListPermissionTests(APITestCase):

    def setUp(self):
        self.url = reverse('user_list')

        self.customer = User.objects.create_user(
            username='customer',
            email='customer@example.com',
            password='StrongPassword123!'
        )

        self.admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='StrongPassword123!',
            is_staff=True
        )

    def test_admin_can_view_user_list(self):
        self.client.force_authenticate(user=self.admin)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_customer_cannot_view_user_list(self):
        self.client.force_authenticate(user=self.customer)

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_user_cannot_view_user_list(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UserModelTests(APITestCase):

    def test_user_string_representation(self):
        user = User.objects.create_user(
            username='modeluser',
            email='model@example.com',
            password='StrongPassword123!'
        )

        self.assertEqual(str(user), 'modeluser')

    def test_email_must_be_unique(self):
        User.objects.create_user(
            username='user1',
            email='same@example.com',
            password='StrongPassword123!'
        )

        duplicate_user = User(
            username='user2',
            email='same@example.com'
        )

        with self.assertRaises(ValidationError):
            duplicate_user.validate_unique()