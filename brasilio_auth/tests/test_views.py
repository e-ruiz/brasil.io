from unittest.mock import Mock, patch

from captcha.fields import ReCaptchaField
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from traffic_control.tests.util import TrafficControlClient

User = get_user_model()


@patch.object(ReCaptchaField, "validate", Mock(return_value=True))
class UserCreationViewTests(TestCase):
    client_class = TrafficControlClient

    def setUp(self):
        self.url = reverse("brasilio_auth:sign_up")
        passwd = "someverygoodpassword"
        self.data = {
            "username": "foo",
            "email": "foo@bar.com",
            "password1": passwd,
            "password2": passwd,
            "captcha": "captcha-code",
        }

    def test_render_correct_template(self):
        response = self.client.get(self.url)
        self.assertTemplateUsed(response, "brasilio_auth/user_creation_form.html")
        assert "form" in response.context

    def test_render_form_errors_if_invalid_post(self):
        response = self.client.post(self.url, data={})
        self.assertTemplateUsed(response, "brasilio_auth/user_creation_form.html")
        assert bool(response.context["form"].errors) is True

    def test_create_and_login_with_user(self):
        assert 1 == User.objects.count()  # auto import covid 19 user
        assert User.objects.filter(username=settings.COVID19_AUTO_IMPORT_USER).exists()

        response = self.client.post(self.url, data=self.data)
        user = User.objects.get(username="foo")

        self.assertRedirects(response, settings.LOGIN_REDIRECT_URL, fetch_redirect_response=False)
        assert "_auth_user_id" in self.client.session
        assert str(user.pk) == self.client.session["_auth_user_id"]

    def test_form_error_if_trying_to_create_user_with_existing_username(self):
        response = self.client.post(self.url, data=self.data)
        assert User.objects.filter(username="foo").exists()

        self.data["username"] = "FOO"
        self.data["email"] = "new@foo.com"
        response = self.client.post(self.url, data=self.data)
        self.assertTemplateUsed(response, "brasilio_auth/user_creation_form.html")
        print(response.context["form"].errors)
        assert bool(response.context["form"].errors) is True
