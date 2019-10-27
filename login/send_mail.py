import os
from django.core.mail import send_mail

os.environ['DJANGO_SETTINGS_MODULE'] = 'mysite.settings'

if __name__ == '__main__':

    send_mail(
        '自己发来看一下自己',
        '想发个邮件没有那么难了呢',
        '2488826451@qq.com',
        ['2488826451@qq.com'],
        fail_silently=False
    )
