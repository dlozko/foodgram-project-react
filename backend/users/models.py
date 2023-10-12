import re

from django.contrib.auth.models import AbstractUser
from django.db import models
from rest_framework.exceptions import ValidationError


class User(AbstractUser):
    username = models.CharField('Имя пользователя',
                                max_length=150,
                                unique=True,
                                blank=False,
                                null=False)
    first_name = models.CharField('Имя',
                                  max_length=150,
                                  blank=False,
                                  null=False)
    last_name = models.CharField('Фамилия',
                                 max_length=150,
                                 blank=False,
                                 null=False)
    email = models.EmailField('Email',
                              unique=True,
                              max_length=200,
                              blank=False,
                              null=False)
    password = models.CharField('Пароль',
                                max_length=150,
                                blank=False,
                                null=False)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'Пользователь {self.username}'


class Follow(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE,
                             related_name='follower',
                             verbose_name='Подписчик')
    author = models.ForeignKey(User,
                               on_delete=models.CASCADE,
                               related_name='followings',
                               verbose_name='Автор')

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [models.UniqueConstraint(
            fields=['user', 'author'], name='unique_user_author')]

    def __str__(self):
        return f'{self.user.username} подписан на {self.author.username}'
