from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_auth = User.objects.create_user(username='Auth')
        cls.user_author = User.objects.create_user(username='Author')
        cls.group = Group.objects.create(
            title="Тестовая группа",
            slug="Test_slag",
            description="Тестовое описание"
        )
        cls.post = Post.objects.create(
            text="Тестовый пост",
            author=cls.user_author,
            group=cls.group
        )
        cls.status_code_url_names = {
            '/': HTTPStatus.OK,
            f'/group/{cls.group.slug}/': HTTPStatus.OK,
            f'/profile/{cls.post.author.username}/': HTTPStatus.OK,
            f'/posts/{cls.post.pk}/': HTTPStatus.OK,
            f'/posts/{cls.post.pk}/edit/': HTTPStatus.FOUND,
            '/create/': HTTPStatus.FOUND,
            '/unexisting_page/': HTTPStatus.NOT_FOUND
        }
        # Словарь для проверки существования шаблонов
        cls.templates_url_names = {
            '/': 'posts/index.html',
            f'/group/{cls.group.slug}/': 'posts/group_list.html',
            f'/profile/{cls.post.author.username}/': 'posts/profile.html',
            f'/posts/{cls.post.pk}/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            f'/posts/{cls.post.pk}/edit/': 'posts/create_post.html',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostURLTests.user_auth)
        self.author_client = Client()
        self.author_client.force_login(PostURLTests.user_author)

    # Проверка для неавторизованных пользователей
    def test_post_create_url_redirect_guest_on_login(self):
        """Страница /create/ перенаправит неавторизованного'
        'пользователя на авторизацию"""
        response = self.guest_client.get('/create/', follow=True)
        self.assertRedirects(response, '/auth/login/?next=/create/')

    def test_post_edit_url_redirect_guest_on_login(self):
        """Страница /post/<int:post_id>/edit/ перенаправит'
         'неавторизованного пользователя на авторизацию"""
        response = self.guest_client.get(
            f'/posts/{PostURLTests.post.pk}/edit/', follow=True
        )
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{PostURLTests.post.pk}/edit/'
        )

    # Проверка для авторизованных пользователей
    def test_post_create_url_exist_on_authorized(self):
        """Проверка доступности страницы /create/'
        'для авторизованного пользователя"""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_redirect_authorized_on_post_detail(self):
        """Проверка, что страница /post/<int:post_id>/edit/ перенаправит'
        'авторизованного пользователя (не автора) на страницу поста"""
        response = self.authorized_client.get(
            f'/posts/{PostURLTests.post.pk}/edit/', follow=True
        )
        self.assertRedirects(response, f'/posts/{PostURLTests.post.pk}/')

    def test_post_edit_url_exist_on_authorized(self):
        """Проверка доступности страницы /post/<int:post_id>/edit/'
        'автору поста"""
        response = self.author_client.get(
            f'/posts/{PostURLTests.post.pk}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_exists_at_desired_location(self):
        """Проверка страниц, доступных без авторизации"""
        for address, status_code in self.status_code_url_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, status_code)

    # Проверка вызываемых шаблонов для каждого адреса
    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for address, template in self.templates_url_names.items():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)
