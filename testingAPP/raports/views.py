from django.shortcuts import render
import pandas as pd
import os
from django.conf import settings
from .utils import get_files
from .forms import StandardReportForm

def standard_raport(request):
    context = {}
    context["test"] = get_files()
    if request.method == "POST":
        form = StandardReportForm(request.POST)
        if form.is_valid():
            file_name = form.cleaned_data["files"] + ".pkl"


            context["chosen"] = file_name

    else:
        form = StandardReportForm()

    context["form"] = form
    return render(request, "std_report.html", context)