from django.shortcuts import render, redirect
from .forms import UploadFileForm, EditActionsForm, EditChooseForm, EXCLUDED_FIELDS
import pandas as pd
import os
from django.conf import settings
from .utils import get_unique_filename, perform_save

def load(request):
    context = {}

    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            uploaded_file = request.FILES["file"]
            uploaded_filename = form.cleaned_data["filename"]
            uploaded_header = form.cleaned_data["header"]
            uploaded_delimiter = form.cleaned_data["delimiter"]
            uploaded_skip_rows = form.cleaned_data["skip_rows"]
            uploaded_custom_columns = form.cleaned_data["custom_columns"]

            # Set column names
            if uploaded_header == -1:
                header = None
            elif uploaded_header > 0:
                header = uploaded_header - 1
            else:
                context['header_msg'] = "Number must be positive!"
                header = None
            column_names = uploaded_custom_columns if uploaded_custom_columns else header

            skiprows = uploaded_skip_rows if uploaded_skip_rows else 0
    
            try:
                if column_names == None:
                    df = pd.read_csv(uploaded_file, skiprows=skiprows, delimiter=uploaded_delimiter)

                elif type(column_names) == int:
                    df = pd.read_csv(uploaded_file, header=column_names, skiprows=skiprows, delimiter=uploaded_delimiter)

                else:
                    columns = [col.strip() for col in column_names.split(',')]
                    df = pd.read_csv(uploaded_file, names=columns, skiprows=skiprows, delimiter=uploaded_delimiter)

                # Display on site
                context["preview"] = df.head(2).to_html(classes="table table-bordered")
                

                # Save to temp
                safe_path = get_unique_filename(settings.TEMP_DIR, uploaded_filename)
                perform_save(df, safe_path)
                df_columns = df.columns.to_list()

                # Basic info
                info = []
                for col in df_columns:
                    counts = df[col].count()
                    zero_counts = (df[col][df[col] == 0]).count() if pd.api.types.is_numeric_dtype(df[col]) else "Not applicable"
                    missing_values = df[col].isnull().sum()
                    unique = df[col].nunique()
                    col_type = str(df[col].dtype)

                    info.append({
                        "name": col,
                        "counts": counts,
                        "zeros": zero_counts,
                        "missing": missing_values,
                        "unique": unique,
                        "type": col_type,
                    })

                context["info"] = info
                context["success"] = True
                del df
            except Exception as e:
                context["error"] = f"Błąd podczas wczytywania pliku: {str(e)}"
        else:
            context["error"] = "Formularz nieprawidłowy."
    else:
        form = UploadFileForm()

    context["form"] = form
    return render(request, "loadDF.html", context)


def edit(request):
    context = {}
    hard_form_fields = EXCLUDED_FIELDS
    context["excluded_fields"] = hard_form_fields # To exclude hard coded fields from form

    selected_file = request.POST.get("selected_file")

    if request.method == "POST":
        action = request.POST.get("action")


        if action == "choose":
            file_form = EditChooseForm(request.POST)
            if file_form.is_valid():
                selected_file = file_form.cleaned_data["files"] or selected_file
                context["selected_file"] = selected_file

                # Edit form
                column_file = os.path.join(settings.TEMP_DIR, selected_file + ".json")
                form_actions = EditActionsForm(filename=column_file)

                context["form_files"] = file_form
                context["form_actions"] = form_actions


        elif action == "edit":
            # Perform actions on file
            column_file = os.path.join(settings.TEMP_DIR, selected_file + ".json")
            form_actions = EditActionsForm(data=request.POST, filename=column_file)
            if form_actions.is_valid():
                df_route = os.path.join(settings.TEMP_DIR, selected_file + ".pkl")
                df: pd.DataFrame = pd.read_pickle(df_route)

                columns_drop = form_actions.cleaned_data["drops"]
                df = df.drop(columns=columns_drop)

                col_types = form_actions.cleaned_data
                for col, new_type in col_types.items():
                    if col in hard_form_fields:
                        continue
                    if new_type:
                        try:
                            if new_type == "category":
                                df[col] = df[col].astype("category")
                            elif new_type == "bool":
                                df[col] = df[col].astype("bool")
                            elif new_type == "int":
                                df[col] = pd.to_numeric(df[col], downcast="integer", errors='raise')
                            elif new_type == "float":
                                df[col] = pd.to_numeric(df[col], downcast="float", errors='raise')
                            elif new_type == "str":
                                df[col] = df[col].astype("string")
                            elif new_type == "datetime":
                                df[col] = pd.to_datetime(df[col], errors='raise')
                        except Exception as e:
                            context["error_conversion"] = f"Error during conversion {col}: {e}"
                            return render(request, 'edit.html', context)

                # Save DataFrame
                delete_df = form_actions.cleaned_data.get("delete_old")
                new_name = form_actions.cleaned_data.get("new_name")
                if (not new_name) and (not delete_df):
                    safe_path = get_unique_filename(settings.TEMP_DIR, selected_file + "_edited")
                elif (not new_name) and delete_df:
                    safe_path = os.path.join(settings.TEMP_DIR, selected_file)
                else:
                    safe_path = get_unique_filename(settings.TEMP_DIR, new_name)

                # Delete old DataFrame
                if delete_df:
                    try:
                        os.remove(df_route)
                        print(selected_file)
                        os.remove(column_file)
                    except Exception as e:
                        context["error_remove"] = f"There was a problem during deleting file: {e}"
                        return render(request, 'edit.html', context)
                    
                # Add informations to meta data
                additional_info = {}
                target = form_actions.cleaned_data["target"]
                additional_info["target"] = target

                # Save new DataFrame
                perform_save(df, safe_path, additional_info)

                # Refresh page to update informations
                return redirect('edit')

        context["form_actions"] = form_actions
        context["form_files"] = file_form

    else:
        context["form_files"] = EditChooseForm()
        context["form_actions"] = None
    return render(request, 'edit.html', context)


def clear_temp(request):
    for file in os.listdir(settings.TEMP_DIR):
        try:
            path = os.path.join(settings.TEMP_DIR, file)
            os.remove(path)
        except Exception as e:
            pass # For now its not implemented as intended 
            
    return redirect('load')
