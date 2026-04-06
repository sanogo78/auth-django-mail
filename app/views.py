from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from authentification import settings
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.core.mail import send_mail, EmailMessage
from .token import generatorToken

# Create your views here.

# creation des fonctions
def home(request):
    return render(request, 'app/index.html')

def register(request):
    if request.method == "POST":
        # on recupère les données entrer par l'utilisateurs.
        username = request.POST['username']
        firstname = request.POST['firstname']
        lastname = request.POST['lastname']
        email = request.POST['email']
        password = request.POST['password']
        password1 = request.POST['password1']
        # verification des données de l'tulisateur existantes
        if User.objects.filter(username=username):
            messages.error(request, "Ce nom d'utilisateur est déjà utilisé !")
            return redirect('register')
        if User.objects.filter(email=email):
            messages.error(request, "Ce mail a déjà été utiliser !")
            return redirect('register')
        if not username.isalnum():
            messages.error(request, 'Saisissez un nom correct SVP !')
            return redirect('register')
        if password != password1:
            messages.error(request, 'Les mot de pass ne corresponde pas !')
            return redirect('register')
        
        mon_utilisteur = User.objects.create_user(username, email, password)
        mon_utilisteur.first_name = firstname
        mon_utilisteur.last_name = lastname
        mon_utilisteur.is_active = False
        mon_utilisteur.save() # pour enregistrer l'utilisateur
        messages.success(request, 'Votre compte a été créer avec succès !')
        # Envoi d'email de bienvenue
        subject = "Bienvenue chez SANOGO djang log"
        message = "Bienvenue" + "" + str(mon_utilisteur) + "\n\n Nous sommes heureux de vous compter parmi nous \n\n\n Merci ! \n\n\n\n SANOGO PONNON MADOU"
        from_email = settings.EMAIL_HOST_USER
        to_list = [mon_utilisteur.email]
        send_mail(subject, message, from_email, to_list, fail_silently=False)
    # Mail de confirmation
        current_site = get_current_site(request)
        email_subject = "Confirmation de l'adresse mail sur sanogo authen"
        messageConfirm = render_to_string('emailconfirm.html', {
            'name': mon_utilisteur.first_name,
            'domain': current_site.domain,
            'uidb64': urlsafe_base64_encode(force_bytes(mon_utilisteur.pk)),
            'token': generatorToken.make_token(mon_utilisteur),
        })
        
        email = EmailMessage(
            email_subject,
            messageConfirm,
            settings.EMAIL_HOST_USER,
            [mon_utilisteur.email]
        )
        
        email.fail_silently = False
        email.send()
        
        return redirect('login')
        
    return render(request, 'app/register.html')

def Login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            login(request, user)
            firstname = user.first_name
            return render(request, 'app/index.html', {'firstname': firstname})
        my_user = User.objects.filter(username=username).first()
        if my_user is not None and my_user.is_active is False:
            messages.error(request, "Vous n'avez pas confirmer votre adress email, faite le avant de vous connecter ")
            return redirect('login')
        else:
            messages.error(request, 'Mauvaise authentification')
            return redirect('login')
    return render(request, 'app/login.html')

def logOut(request):
    logout(request)
    messages.success(request, 'Vous avez été bien deconnecter !')
    return redirect('home')

def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
        
    if user is not None and generatorToken.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Votre a bien été activé Félicitation connectez vous mainteant !')
        return redirect('login')
    else:
        messages.error(request, 'Activation échouée !!!!')
        return redirect('home')
