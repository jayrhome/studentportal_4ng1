from django.shortcuts import render
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic.base import TemplateView, RedirectView, View
from django.views.generic import ListView, DetailView
from django.views.generic.edit import FormView, CreateView, DeletionMixin
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db import IntegrityError, transaction
from django.db.models import Prefetch, Count, Q
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from ratelimit.decorators import ratelimit
from adminportal.models import *
from datetime import date, datetime
from django.core.exceptions import ValidationError, NON_FIELD_ERRORS
from django.db import IntegrityError
from . models import *
from studentportal.models import documentRequest


User = get_user_model()


def registrar_only(user):
    return user.is_registrar


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(registrar_only, login_url="studentportal:index")], name="dispatch")
class registrarDashboard(TemplateView):
    template_name = "registrarportal/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Dashboard"
        return context


@method_decorator([login_required(login_url="usersPortal:login"), user_passes_test(registrar_only, login_url="studentportal:index")], name="dispatch")
class getList_documentRequest(ListView, DeletionMixin):
    allow_empty = True
    context_object_name = "listOfDocumentRequests"
    http_method_names = ["get", "post"]
    paginate_by = 35
    template_name = "registrarPortal/documentRequests/listOfDocumentRequests.html"
    success_url = "/Registrar/RequestDocuments/"

    def delete(self, request, *args, **kwargs):
        try:
            self.cancel_this_request.is_cancelledByRegistrar = True
            self.cancel_this_request.save()
        except Exception as e:
            messages.warning(request, "Error.")
        return HttpResponseRedirect(self.success_url)

    def get_queryset(self):
        return documentRequest.registrarObjects.values("id", "document__documentName", "request_by__display_name", "scheduled_date")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Document Requests"
        return context

    def dispatch(self, request, *args, **kwargs):
        if ("pk" in request.POST) and request.method == "POST":
            self.cancel_this_request = documentRequest.registrarObjects.filter(
                id=int(request.POST["pk"])).first()
        return super().dispatch(request, *args, **kwargs)
