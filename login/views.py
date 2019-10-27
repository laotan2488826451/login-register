from django.shortcuts import render,redirect
from django.conf import settings
from . import models,forms
import hashlib,datetime

# Create your views here.

#哈希码
def hash_code(s,salt='mysite'):
    h = hashlib.sha256()
    s += salt
    h.update(s.encode())  # update方法只接收bytes类型
    return h.hexdigest()

#创建确认码
def make_confirm_string(user):
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    code = hash_code(user.name,now)
    models.ConfirmString.objects.create(code=code,user=user,)
    return code

#发送邮件
def send_email(email,code):

    from django.core.mail import EmailMultiAlternatives

    subject = '来自老坛的注册邮件确认'

    text_content = '''感谢注册，如果你看到这条消息，说明你的邮箱服务器不提供HTML链接功能，请联系管理员！'''

    html_content = '''
                    <p>感谢注册<a href="http://{}/confirm/?code={}" target=blank>www.laotan.com</a>,\
                    这是来自老坛的问候！</p>
                    <p>点击链接你就上当！</p>
                    <p>此链接有效期为{}天！</p>
                    '''.format('127.0.0.1:8000',code,settings.CONFIRM_DAYS)

    msg = EmailMultiAlternatives(subject,text_content,settings.EMAIL_HOST_USER,[email])
    msg.attach_alternative(html_content,"text/html")
    msg.send()

def index(request):
    if not request.session.get('is_login',None):
        return redirect('/login/')
    return render(request, 'login/index.html')

def login(request):
    if request.session.get('is_login',None):        #不允许重复登录
        return redirect('/index/')
    if request.method == "POST":
        login_form = forms.UserForm(request.POST)
        message = '请检查填写的内容！'
        if login_form.is_valid():
            username = login_form.cleaned_data.get('username')
            password = login_form.cleaned_data.get('password')

            try:
                user = models.User.objects.get(name=username)
            except:
                message = '用户不存在'
                return render(request,'login/login.html',locals())

            if not user.has_confirmed:
                message = '该用户还未经过邮件确认！'
                return render(request,'login/login.html',locals())

            if user.password == hash_code(password):
                request.session['is_login'] = True
                request.session['user_id'] = user.id
                request.session['user_name'] = user.name
                return redirect('/index/')
            else:
                message = '密码不正确！'
                return render(request,'login/login.html',locals())
        else:
            return render(request, 'login/login.html',locals())

    login_form = forms.UserForm()
    return render(request, 'login/login.html',locals())

def register(request):
    if request.session.get('is_login',None):
        return redirect('/index/')

    if request.method == 'POST':
        register_form = forms.RegisterForm(request.POST)
        message = "请检查填写的内容！"
        if register_form.is_valid():
            username = register_form.cleaned_data.get('username')
            password1 = register_form.cleaned_data.get('password1')
            password2 = register_form.cleaned_data.get('password2')
            email = register_form.cleaned_data.get('email')
            sex = register_form.cleaned_data.get('sex')

            if password1 != password2:
                message = '两次输入的密码不同！'
                return render(request,'login/register.html',locals())
            else:
                if models.User.objects.filter(name=username):
                    message = '用户名已存在'
                    return render(request, 'login/register.html', locals())
                if models.User.objects.filter(email=email):
                    message = '该邮箱已经被注册了！'
                    return render(request, 'login/register.html', locals())

                new_user = models.User()            #获得模型实例
                new_user.name = username
                new_user.password = hash_code(password1)
                new_user.email = email
                new_user.sex = sex
                new_user.save()

                code = make_confirm_string(new_user)    #创建用户确认码
                send_email(email,code)                  #注册的邮箱和前面的哈希值

                message = "请前往邮箱进行确认!"
                return render(request,'login/confirm.html',locals())
        else:
            return render(request,'login/register.html',locals())
    register_form = forms.RegisterForm()
    return render(request, 'login/register.html',locals())

def logout(request):
    if not request.session.get('is_login',None):
        # 如果本来就未登录，则无法登出
        return redirect("/login/")

    request.session.flush()
    return redirect('/login/')

#确认视图
def user_confirm(request):
    code = request.GET.get('code',None)                         #从请求的url地址中获取确认码
    message = ''
    try:
        confirm = models.ConfirmString.objects.get(code=code)   #去数据库查询是否有确认码
    except:
        message = '无效的确认请求'
        return render(request,'login/confirm.html',locals())    #没有就返回confirm界面

    c_time = confirm.c_time                                     #如果有，获取注册时间
    now = datetime.datetime.now()
    if now > c_time + datetime.timedelta(settings.CONFIRM_DAYS):#判断现在时间与注册时间+过期时间对比
        confirm.user.delete()                                   #过期了 删掉注册的用户和注册码 然后返回confirm
        message = '您的邮件已经过期！请重试注册！'
        return render(request,'login/confirm.html',locals())
    else:
        confirm.user.has_confirmed = True                       #没过期 把用户has_confirmed改成True
        confirm.user.save()                                     #保存改变 表示通过确认
        confirm.delete()                                        #删除注册码 不删除用户
        message = '确认好了，去登录吧！'
        return render(request,'login/confirm.html',locals())
