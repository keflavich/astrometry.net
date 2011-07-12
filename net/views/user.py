import shutil
import os, errno
import hashlib
import tempfile
import math
import urllib
import urllib2

from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, QueryDict
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import Context, RequestContext, loader
from django.contrib.auth.decorators import login_required

from astrometry.net.models import *
from astrometry.net import settings
from log import *
from django import forms
from django.http import HttpResponseRedirect

from astrometry.util import image2pnm
from astrometry.util.run_command import run_command
from astrometry.net.util import get_page

class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        exclude = ('apikey', 'default_license')

class LicenseForm(forms.ModelForm):
    class Meta:
        model = License
        exclude = ('license_uri','license_name')

def dashboard(request):
    return render_to_response("dashboard/base.html",
        {
        },
        context_instance = RequestContext(request))

@login_required
def save_profile(request):
    profile = request.user.get_profile()
    if request.method == 'POST':
        profile.display_name = request.POST['display_name']
        profile.default_license.allow_modifications = request.POST['allow_modifications']
        profile.default_license.allow_commercial_use = request.POST['allow_commercial_use']

        if profile.default_license.allow_modifications == 'd':
            profile.default_license.allow_modifications = License.get_default().allow_modifications
        if profile.default_license.allow_commercial_use == 'd':
            profile.default_license.allow_commercial_use = License.get_default().allow_commercial_use

        profile.save()

    return redirect('astrometry.net.views.user.dashboard_profile')

@login_required
def dashboard_profile(request):
    # user profile guaranteed to be created during openid login
    profile = request.user.get_profile()
           
    profile_form = ProfileForm(instance=profile)
    license_form = LicenseForm(instance=profile.default_license)
    context = {
        'profile_form':profile_form,
        'license_form':license_form,
        'profile':profile,
    }
    return render_to_response("dashboard/profile.html",
        context,
        context_instance = RequestContext(request))

@login_required
def dashboard_submissions(req):
    context = {
        'user_submissions':req.user.submissions.all().order_by('-submitted_on')
    }
    return render_to_response("dashboard/submissions.html",
        context,
        context_instance = RequestContext(req))

@login_required
def dashboard_user_images(req):
    page_number = req.GET.get('page',1)
    page = get_page(req.user.user_images.all().order_by('-submission__submitted_on', 'id'),3*10,page_number)
    
    context = {
        'user':req.user,
        'image_page':page
    }
    
    return render_to_response('dashboard/user_images.html',
        context,
        context_instance = RequestContext(req))


def index(req):
    context = {
        'users':User.objects.all()
    }
    return render_to_response("user/index.html",
        context,
        context_instance = RequestContext(req))


def public_profile(req, user_id=None):
    user = get_object_or_404(User, pk=user_id)

    context = {
        'display_user':user,
        'recent_submissions':user.submissions.all().order_by('-submitted_on')[:10],
    }
    return render_to_response('user/profile.html',
        context,
        context_instance = RequestContext(req))
