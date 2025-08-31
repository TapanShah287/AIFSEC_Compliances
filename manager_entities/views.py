from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.core.paginator import Paginator
from django.db.models import Q
from django import forms
from .models import ManagerEntity
from .forms import ManagerForm 


def manager_list(request):
    q = (request.GET.get("q") or "").strip()
    qs = ManagerEntity.objects.all()
    if q:
        qs = qs.filter(Q(name__icontains=q) | Q(sebi_manager_registration_no__icontains=q) | Q(pan__icontains=q) | Q(gstin__icontains=q))
    page = Paginator(qs.order_by("name"), 25).get_page(request.GET.get("page"))
    return render(request, "manager_entities/manager_list.html", {"managers": page.object_list, "page_obj": page, "is_paginated": page.paginator.num_pages > 1, "request": request})

def manager_detail(request, pk):
    obj = get_object_or_404(ManagerEntity, pk=pk)
    return render(request, "manager_entities/manager_detail.html", {"manager": obj})

def manager_create(request):
    if request.method == "POST":
        form = ManagerForm(request.POST)
        if form.is_valid():
            obj = form.save()
            
            next_url = request.GET.get("next")
            if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts=request.get_host()):
                return redirect(next_url)
            
            return redirect(reverse("manager_entities:manager_detail", args=[obj.pk]))
    else:
        form = ManagerForm()
    return render(request, "manager_entities/manager_form.html", {"form": form})

def manager_update(request, pk):
    obj = get_object_or_404(ManagerEntity, pk=pk)
    if request.method == "POST":
        form = ManagerForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            return redirect(reverse("manager_entities:manager_detail", args=[obj.pk]))
    else:
        form = ManagerForm(instance=obj)
    return render(request, "manager_entities/manager_form.html", {"form": form, "manager": obj})
