from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST

from poste.models import Post
from .forms import LoginForm, UserRegistrationForm, UserEditForm, ProfileEditForm
from .models import Profile, Contact
from actions.models import Action
from actions.utils import create_action
from common.decorators import ajax_required

def user_login(request):
    if request.method == 'POST':
        #lorsque on fait appel au view 'user_login' on fait une nouvelle instance de login form pour etre afficher dans la template
        form = LoginForm(request.POST)
        # pour vérifier c'est le form valide ou non
        if form.is_valid():
            cd = form.cleaned_data
            # pour vérifier la correspondance de données envoyés avec les données dans la base
            user = authenticate(username=cd['username'], password=cd['password'])
            #pour vérifier est ce que le compte d'utilisateur activé
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return HttpResponse('Authentification avec succée')
                else:
                    return HttpResponse('Votre compte est désactivé')
            else:
                return HttpResponse('Données incorrecte')
    else:
        form = LoginForm()
    return render(request, 'account/login.html', {'form': form})


def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)

        if user_form.is_valid():
            # Creation de nouveau objet user mais pas encore enregistré
            new_user = user_form.save(commit=False)
            # Définir le mot de passe choisi
            new_user.set_password(user_form.cleaned_data['password'])
            # Enregistrer l'objet user
            new_user.save()
            # créer un profile pour l'utilisateur
            profile = Profile.objects.create(user=new_user)
            return render(request,
                          'account/register_done.html',
                          {'new_user': new_user})
    else:
        user_form = UserRegistrationForm()
    return render(request, 'account/register.html', {'user_form': user_form})

# il faut authentifier pour modifier le profile
@login_required
def edit(request):
    if request.method == 'POST':
        #pour stocker les données du modèle d'utilisateur intégré
        user_form = UserEditForm(instance=request.user,
                                 data=request.POST)
        #pour stocker les données de profil associer au utilisateur
        profile_form = ProfileEditForm(instance=request.user.profile,
                                       data=request.POST,
                                       files=request.FILES)

        #pour valider les doneeés envoyeés
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Modification de profil avec succés')
        else:
            messages.error(request, 'Erreur dans la modification de profil')
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=request.user.profile)
    return render(request, 'account/edit.html', {'user_form': user_form,
                                                 'profile_form': profile_form})


# pour vérifier si l'utilisatateur courant , authentifier ou non
@login_required
def dashboard(request):

    posts = Post.objects.filter(author=request.user).order_by('published_date')
    # Display all actions by default
    actions = Action.objects.all().exclude(user=request.user)
    following_ids = request.user.following.values_list('id', flat=True)
    if following_ids:
        # If user is following others, retrieve only their actions
        actions = actions.filter(user_id__in=following_ids).select_related('user', 'user__profile').prefetch_related('target')
    actions = actions[:10]

    return render(request, 'account/dashboard.html', {'section': 'dashboard',
                                                      'posts': posts,
                                                      'actions': actions})


@login_required
def user_list(request):
    users = User.objects.filter(is_active=True)
    return render(request, 'account/user/list.html', {'section': 'people',
                                                      'users': users})


@login_required
def user_detail(request, username):
    user = get_object_or_404(User, username=username, is_active=True)
    return render(request, 'account/user/detail.html', {'section': 'people',
                                                        'user': user})
@ajax_required
@require_POST
@login_required
def user_follow(request):
    user_id = request.POST.get('id')
    action = request.POST.get('action')
    if user_id and action:
        try:
            user = User.objects.get(id=user_id)
            if action == 'follow':
                Contact.objects.get_or_create(user_from=request.user,
                                              user_to=user)
                create_action(request.user, 'is following', user)
            else:
                Contact.objects.filter(user_from=request.user,
                                       user_to=user).delete()
            return JsonResponse({'status':'ok'})
        except User.DoesNotExist:
            return JsonResponse({'status':'ko'})
    return JsonResponse({'status':'ko'})
