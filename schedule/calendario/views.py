from django.contrib.auth import authenticate, login
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect, get_object_or_404

# Create your views here.

import sys
import json
import csv
import os
from django.urls import reverse
from django.http import JsonResponse
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, Http404, JsonResponse
from django.db.models import Q
from django.urls import reverse
from django.core.checks import messages
from io import StringIO, TextIOWrapper
import os
from django.conf import settings
from django.http import FileResponse

app_name = 'src'

# def convertView(request):
#     if request.method == 'POST':
#         form = ArquivoForm(request.POST, request.FILES)
#         if form.is_valid():
#             uploaded_file = form.cleaned_data['arquivo']
#             app = appGUI()
#             app.convert_button_clicked(uploaded_file)
#     else:
#         form = ArquivoForm()
#     return render(request, 'homePage.html', {'form': form})

# class AppGUI():
#     def __init__(self):
#         super().__init__()
#         # self.initUI()
#
#     # def initUI(self):
#     #     self.setWindowTitle("Calendar Tools")
#     #     self.setFixedSize(400, 250)
#     #
#     #     central_widget = QWidget()
#     #     self.setCentralWidget(central_widget)
#     #
#     #     self.layout = QVBoxLayout()
#     #
#     #     self.input_label = QLabel("Input File/URL:", self)
#     #     self.layout.addWidget(self.input_label)
#     #
#     #     self.input_file_text = QLineEdit(self)
#     #     self.layout.addWidget(self.input_file_text)
#     #
#     #     self.button_group = QButtonGroup(self)
#     #
#     #     self.convert_button = QPushButton("Convert", self)
#     #     self.convert_button.clicked.connect(self.convert_button_clicked)
#     #     self.layout.addWidget(self.convert_button)
#     #
#     def convert_button_clicked(self, input_file_or_url):
#         # input_file_or_url = self.input_file_text.text()
#         option = 2
#
#         if ".csv" in input_file_or_url:
#             option = 1
#
#         # try:
#         if option == 1:
#             AppGUI.csv_to_json(input_file_or_url)
#         elif option == 2:
#             AppGUI.json_to_csv(input_file_or_url)
#         # else:
#                 # raise ValueError("Invalid option: " + option)
#         # except ValueError as e:
#             # QMessageBox.critical(self, "Error", str(e))
#         sys.exit()
#
#
#     def csv_to_json(self, input_file_or_url):
#         # try:
#         with self.get_input_stream(input_file_or_url) as input_stream:
#             csv_data = input_stream.read().decode("utf-8")
#             json_data = json.dumps(list(csv.DictReader(csv_data.splitlines())))
#
#             options = QFileDialog.Options()
#             file_path, _ = QFileDialog.getSaveFileName(self, "Save JSON File", "", "JSON Files (*.json);;All Files (*)", options=options)
#
#             if file_path:
#                 self.save_file(file_path, json_data)
#         # except Exception as e:
#         #     QMessageBox.critical(self, "Error", "Error converting CSV to JSON: " + str(e))
#
    # def json_to_csv(self, input_file_or_url):
    #     try:
    #         with self.get_input_stream(input_file_or_url) as input_stream:
    #             json_data = json.load(input_stream)
    #             csv_data = json_data[0].keys()  # Extract the field names
    #
    #             options = QFileDialog.Options()
    #             file_path, _ = QFileDialog.getSaveFileName(
    #                 self, "Save CSV File", "", "CSV Files (*.csv);;All Files (*)", options=options)
    #
    #             if file_path:
    #                 with open(file_path, "w", newline="", encoding="utf-8") as csv_file:
    #                     csv_writer = csv.DictWriter(csv_file, csv_data)
    #                     csv_writer.writeheader()
    #                     csv_writer.writerows(json_data)
    #                 QMessageBox.information(self, "Success", "Successfully converted to: " + file_path)
    #     except Exception as e:
    #         QMessageBox.critical(self, "Error", "Error converting JSON to CSV: " + str(e))
#
#     def get_input_stream(self, input_file_or_url):
#         if input_file_or_url.startswith("http") or input_file_or_url.startswith("https"):
#             from urllib.request import urlopen
#             return urlopen(input_file_or_url)
#         else:
#             return open(input_file_or_url, "rb")
#
# def save_file(file_type):
#     options = QFileDialog.Options()
#     file_path, _ = QFileDialog.getSaveFileName("Save " + file_type + " File", "", "", options=options)
#     if file_path:
#         try:
#             with open(file_path, "w", encoding="utf-8") as file:
#                 file.write(content)
#             QMessageBox.information(self, "Success", "Successfully converted to: " + file_path)
#         except Exception as e:
#             QMessageBox.critical(self, "Error", "Error saving file: " + str(e))
#

def get_information_sections(file):
    try:
        with file as input_stream:
            csv_data = input_stream.read().decode("utf-8")
            csv_data = [line.split(';') for line in csv_data.split('\n') if line]  # Convert CSV string to a list of lists
            if csv_data:
                lotacao_index = -1  # Initialize with an invalid index
                inscritos_index = -1  # Initialize with an invalid index
                # Vale a pena usar sala quando se pode usar as características???
                sala_index=-1
                sala_expectavel=-1
                sala_real=-1
                header_row = csv_data[0]
                salas_desperdiçadas=0
                salas_sem_caracteristicas=0

                # Find the index of the columns dynamically
                for index, column_name in enumerate(header_row):
                    if "Lotação" in column_name:
                        lotacao_index = index
                    if "Inscritos no turno" in column_name:
                        inscritos_index = index
                    if "Sala da aula" in column_name:
                        sala_index = index
                    if "Características da sala pedida para a aula" in column_name:
                        sala_expectavel = index
                    if "Características reais da sala" in column_name:
                        sala_real = index
                #Separar???
                if lotacao_index != -1 and inscritos_index != -1 and sala_index != -1 and sala_expectavel!=-1 and sala_real!=-1:
                    count = 0
                    sum_students = 0
                    aulas_sem_sala = 0
                    total_aulas=0
                    tipo_de_sala_expectado=None
                    tipo_de_sala_real=None

                    # Valid columns found, proceed with checking for overpopulation

                    save_path = save_path = "C:\\Users\\danie\\PycharmProjects\\projetoADSdjango\\schedule\\calendario\\static\\overpopulated_classes.csv"
                    with open(save_path, "w", newline="", encoding="utf-8") as csv_file:
                        csv_writer = csv.writer(csv_file)
                        csv_writer.writerow(header_row)
                        for row in csv_data[1:]:
                            try:
                                lotacao = int(row[lotacao_index])
                                inscritos = int(row[inscritos_index])
                                if isinstance(lotacao, int) and isinstance(inscritos, int):
                                    if inscritos > lotacao:
                                        csv_writer.writerow(row)
                                        count+=1
                                        sum_students+=(inscritos-lotacao)
                                sala = row[sala_index]
                                aulas_sem_sala+=1
                                tipo_de_sala_expectado = row[sala_expectavel]
                                tipo_de_sala_real = row[sala_real]
                                result = get_class_room_characteristics(tipo_de_sala_expectado, tipo_de_sala_real)
                                salas_desperdiçadas+=result[0]
                                salas_sem_caracteristicas+=result[1]
                            except ValueError as e:
                                str(e)
                            total_aulas+=1
                    #print(tipos_de_sala_1, tipos_de_sala_2)
                    return count, sum_students, total_aulas-aulas_sem_sala, salas_desperdiçadas, salas_sem_caracteristicas
    except Exception as e:
        return None

def get_class_room_characteristics(tipo_de_sala_expectado, tipo_de_sala_real):
    salas_sem_caracteristicas=0
    salas_desperdiçadas=0
    #list=[]
    # Pedir Sala de Aulas e sair Arq???
    if "Arq" in tipo_de_sala_expectado.strip() and ("Arq" not in tipo_de_sala_real.strip() and "Computadores" not in tipo_de_sala_expectado.strip()):
        salas_sem_caracteristicas+=1
    if "Arq" in tipo_de_sala_real.strip() and ("Arq" not in tipo_de_sala_expectado.strip() and "Computadores" not in tipo_de_sala_real.strip()):
        salas_desperdiçadas += 1
    # if "Lab" in tipo_de_sala_expectado.strip() and (tipo_de_sala_expectado.strip() not in tipo_de_sala_real.strip()):
    #     salas_sem_caracteristicas += 1
    # if "Lab" in tipo_de_sala_real.strip() and ("Lab" not in tipo_de_sala_expectado.strip()):
    #     salas_desperdiçadas += 1
    if "Lab" in tipo_de_sala_expectado.strip() and ("Lab" not in tipo_de_sala_real.strip()) and salas_desperdiçadas!=1 and salas_sem_caracteristicas!=1:
        salas_sem_caracteristicas += 1
    if "Lab" in tipo_de_sala_real.strip() and ("Lab" not in tipo_de_sala_expectado.strip()) and salas_desperdiçadas!=1 and salas_sem_caracteristicas!=1:
        salas_desperdiçadas += 1
    if "BYOD" in tipo_de_sala_expectado and "BYOD" not in tipo_de_sala_real and salas_desperdiçadas!=1 and salas_sem_caracteristicas!=1:
        salas_sem_caracteristicas += 1
    # Se for de aulas???
    if "BYOD" in tipo_de_sala_real and "BYOD" not in tipo_de_sala_expectado and "aulas" not in tipo_de_sala_real and salas_desperdiçadas!=1 and salas_sem_caracteristicas!=1:
        salas_desperdiçadas += 1
    #Videoconferencia????
    if "videoconferencia" in tipo_de_sala_expectado and "videoconferencia" not in tipo_de_sala_real and salas_desperdiçadas!=1 and salas_sem_caracteristicas!=1:
        salas_sem_caracteristicas+=1
    if "Não necessita de sala" in tipo_de_sala_expectado and tipo_de_sala_real and salas_desperdiçadas!=1 and salas_sem_caracteristicas!=1:
        salas_desperdiçadas+=1
    # if ("Aulas" or "aulas" in tipo_de_sala_expectado) and "aulas" not in tipo_de_sala_real:
    #     salas_desperdiçadas+=1
    # if ("Aulas" in tipo_de_sala_expectado or "aulas" in tipo_de_sala_expectado) and "aulas" not in tipo_de_sala_real:
    #     salas_sem_caracteristicas+=1
    # if salas_sem_caracteristicas!=0 or salas_desperdiçadas!=0:
    #     if (tipo_de_sala_expectado, tipo_de_sala_real) not in list:
    #         list.append((tipo_de_sala_expectado, tipo_de_sala_real))
    #         print(list[-1])
    #
    return salas_desperdiçadas, salas_sem_caracteristicas

def get_informations(request):
    if request.method == 'POST':
        file = request.FILES.get('input_file')

    if not file.name.endswith('.csv'):
        return HttpResponse("Please upload a valid CSV file")
    try:
        result = get_information_sections(file)
        if result is None:
            return HttpResponse("An error occurred while processing the file.")
        number, sum_students, aulas_sem_sala, salas_desperdiçadas, salas_sem_caracteristicas = result
        if number==0:
            return HttpResponse("Erro ao recolher número de aulas em sobrelotação.")
        if sum_students==0:
            return HttpResponse("Erro ao recolher número de alunos com aulas em sobrelotação.")
        if aulas_sem_sala==0:
            return HttpResponse("Erro ao recolher número de aulas sem sala atribuída.")
        if salas_desperdiçadas == 0:
            return HttpResponse("Erro ao recolher número de características desperdiçadas nas salas atribuídas às aulas.")
        if salas_sem_caracteristicas == 0:
            return HttpResponse("Erro ao recolher número de salas sem as características solicitadas pelo docente.")
            #Número de alunos em sobrelotação é número de alunos a mais em cada sobrelotação ou número total dessas aulas???
        return HttpResponse(
            f"Número de aulas em sobrelotação: {number}<br>"
            f"Número de alunos com aulas em sobrelotação: {sum_students}<br>"
            f"Número de aulas sem sala atribuída: {aulas_sem_sala}<br>"
           f"Número de características desperdiçadas nas salas atribuídas às aulas: {salas_desperdiçadas}<br>"
           f"Número de salas sem as características solicitadas pelo docente: {salas_sem_caracteristicas}"
        )
    except FileNotFoundError or Exception as e:
        return HttpResponse(str(e))

def save_file(file_path, content):
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)
        return file_path
    except Exception as e:
        return None

# def csv_to_json(uploaded_file):
#     try:
#         data = uploaded_file.read().decode("utf-8")
#         json_data = json.dumps(list(csv.DictReader(data.splitlines())))
#         return json_data
#     except Exception as e:
#         return str(e)
def csv_to_json(uploaded_file):
    try:
        # Read the CSV data
        data = uploaded_file.read().decode("utf-8").splitlines()

        # Get the header row and the data rows
        header = data[0]
        rows = data[1:]

        # Split the header into field names
        field_names = header.split(';')

        # Create a list of dictionaries
        result = []
        for row in rows:
            values = row.split(';')
            item = {}
            for i, field_name in enumerate(field_names):
                item[field_name] = values[i]
            result.append(item)

        # Convert the list of dictionaries to JSON
        json_data = json.dumps(result)
        return json_data
    except Exception as e:
        return str(e)

# def json_to_csv(json_file_path, csv_file_path):
#     try:
#         # Read the JSON data from the input file
#         with open(json_file_path, 'r') as json_file:
#             json_data = json.load(json_file)
#
#         if not json_data:
#             raise ValueError("No data found in the JSON input.")
#
#         # Extract the field names from the first item in the list
#         field_names = list(json_data[0].keys())
#
#         # Write the data to a CSV file
#         with open(csv_file_path, "w", newline="", encoding="utf-8") as csv_file:
#             csv_writer = csv.writer(csv_file)
#
#             # Write the header row
#             csv_writer.writerow(field_names)
#
#             # Write the data rows
#             for item in json_data:
#                 values = [item[field] for field in field_names]
#                 csv_writer.writerow(values)
#
#         return True, None
#     except Exception as e:
#         return False, str(e)
def json_to_csv(input_data):
    try:
        # Load the JSON data
        json_data = json.loads(input_data)

        if not json_data:
            raise ValueError("No data found in the JSON input.")

        # Extract the field names from the first dictionary
        field_names = list(json_data[0].keys())

        # Create a StringIO buffer to write CSV data
        csv_buffer = StringIO()
        csv_writer = csv.DictWriter(csv_buffer, fieldnames=field_names)

        # Write the header row
        csv_writer.writeheader()

        # Write the data rows
        csv_writer.writerows(json_data)

        # Get the CSV data as a string
        csv_data = csv_buffer.getvalue()

        return csv_data
    except Exception as e:
        return str(e)

def download_csv(file_name):
    file_path = os.path.join(settings.MEDIA_ROOT, 'csv_files', file_name)
    with open(file_path, 'w', encoding="utf-8") as csv_file:
        csv_file.write()
        response = FileResponse(csv_file)
    return response

def download_json(file_name):
    file_path = os.path.join(settings.MEDIA_ROOT, 'json_files', file_name)
    with open(file_path, 'rb') as json_file:
        response = FileResponse(json_file)
    return response


# def convertView(request):
#     if request.method == 'POST':
#         uploaded_file = request.FILES.get('uploaded_file')  # Ensure the input field in your HTML form is named 'uploaded_file'
#         if uploaded_file:
#             if uploaded_file.name.endswith(".csv"):
#                 # Handle CSV to JSON conversion
#                 file_path = csv_to_json(uploaded_file)
#                 file_name = os.path.basename(file_path)
#                 with open(file_path, 'r') as file:
#                     file_data = file.read()
#                 download_link = reverse('download_json', args=[file_name])
#                 return JsonResponse({"download_link": download_link})
#             elif uploaded_file.name.endswith(".json"):
#                 # Handle JSON to CSV conversion
#                 file_path = json_to_csv(uploaded_file)
#                 file_name = os.path.basename(file_path)
#                 with open(file_path, 'r') as file:
#                     file_data = file.read()
#                 download_link = reverse('download_csv', args=[file_name])
#                 return JsonResponse({"download_link": download_link})
#     return render(request, 'calendario/homePage.html')

def convertView(request):
    if request.method == 'POST':
        uploaded_file = request.FILES.get('uploaded_file')  # Ensure the input field in your HTML form is named 'uploaded_file'
        if uploaded_file:
            if uploaded_file.name.endswith(".csv"):
                # Handle CSV to JSON conversion
                file_path = csv_to_json(uploaded_file)
                if file_path:
                    # Define the desired save path for the file
                    save_path = save_path = "C:\\Users\\danie\\PycharmProjects\\projetoADSdjango\\schedule\\calendario\\static\\FicheiroConvertidoJson.json"

                    # Save the file using the save_file function
                    saved_file_path = save_file(save_path, file_path)

                    if saved_file_path:
                        # If the file was successfully saved, return the download link
                        file_name = os.path.basename(saved_file_path)
                        download_link = reverse('download_file', args=[file_name])
                        return JsonResponse({"download_link": download_link})
                    else:
                        # Handle the case where the file couldn't be saved
                        return JsonResponse({"error": "Failed to save the file."})
            elif uploaded_file.name.endswith(".json"):
                # Handle JSON to CSV conversion
                save_path = "C:\\Users\\danie\\PycharmProjects\\projetoADSdjango\\schedule\\calendario\\static\\ficheiroconvertidojson.csv"
                success, error = json_to_csv(uploaded_file.read().decode("utf-8"))

                if success:
                    # Save the CSV data using the save_file function
                    saved_file_path = save_file(save_path, error)

                    if saved_file_path:
                        # If the file was successfully saved, you can return a download link or message here
                        file_name = os.path.basename(saved_file_path)
                        return JsonResponse({"download_link": saved_file_path})
                    else:
                        # Handle the case where the file couldn't be saved
                        return JsonResponse({"error": "Failed to save the CSV file."})
                else:
                    # Handle the case where the conversion or file saving failed
                    return JsonResponse({"error": f"Conversion failed with the following error: {error}"})
    return render(request, 'calendario/homePage.html')

def class_rooms(request):
    if request.method == 'POST':
        file = request.FILES.get('class_rooms')

    if not file.name.endswith('.csv'):
        return HttpResponse("Please upload a valid CSV file")
    save_path = "C:\\Users\\danie\\PycharmProjects\\projetoADSdjango\\schedule\\calendario\\static\\FicheiroSalas.csv"
    try:
        file_content = file.read().decode("utf-8")
        saved_file_path = save_file(save_path, file_content)
    except Exception as e:
        return HttpResponse(f"Error processing the uploaded file: {str(e)}")

    return render(request, 'calendario/homePage.html')

# def convertView(request):
#     if request.method == 'POST':
#         uploaded_file = request.FILES.get(
#             'uploaded_file')  # Ensure the input field in your HTML form is named 'uploaded_file'
#         if uploaded_file:
#             if uploaded_file.name.endswith(".csv"):
#                 # Handle CSV to JSON conversion
#                 file_path = csv_to_json(uploaded_file)
#                 if file_path:
#                     # Define the desired save path for the file
#                     save_path = "C:\\Users\\guiva\\OneDrive\\Documents\\ISCTE\\Primeiro ano Mestrado ISCTE\\ADS\\projetoADSdjango\\schedule\\calendario\\static\\ficheiroconvertidocsv.json"
#
#                     # Save the file using the save_file function
#                     saved_file_path = save_file(save_path, file_path)
#
#                     if saved_file_path:
#                         # If the file was successfully saved, return the download link
#                         file_name = os.path.basename(saved_file_path)
#                         return render(request, 'calendario/homePage.html')
#                         # download_link = reverse('download_file', args=[file_name])
#                         # return JsonResponse({"download_link": download_link})
#                     else:
#                         # Handle the case where the file couldn't be saved
#                         return render(request, 'calendario/homePage.html')
#                         # return JsonResponse({"error": "Failed to save the file."})
#             elif uploaded_file.name.endswith(".json"):
#                 # Define the desired save path for the CSV file
#                 save_path = "C:\\Users\\guiva\\OneDrive\\Documents\\ISCTE\\Primeiro ano Mestrado ISCTE\\ADS\\projetoADSdjango\\schedule\\calendario\\static\\ficheiroconvertidojson.csv"
#
#                 success, error = json_to_csv(uploaded_file.read().decode("utf-8"), save_path)
#
#                 if success:
#                     # Define the desired save path for the CSV file
#                     # save_path = "C:\\Users\\guiva\\OneDrive\\Documents\\ISCTE\\Primeiro ano Mestrado ISCTE\\ADS\\projetoADSdjango\\schedule\\calendario\\static\\ficheiroconvertidojson.csv"
#
#                     # Save the CSV data using the save_file function
#                     saved_file_path = save_file(save_path, error)
#
#                     if saved_file_path:
#                         # If the file was successfully saved, you can return a download link or message here
#                         file_name = os.path.basename(saved_file_path)
#                         return HttpResponse("JSON file successfully converted to CSV.")
#                     else:
#                         # Handle the case where the file couldn't be saved
#                         return HttpResponse("Failed to save the CSV file.")
#                 else:
#                     # Handle the case where the conversion or file saving failed
#                     return HttpResponse(f"Conversion failed with the following error: {error}")


def observeCalendar(request):
    if request.method == 'POST' and 'file' in request.FILES:
        uploaded_file = request.FILES['file']
        if uploaded_file:

            if uploaded_file.name.endswith('.csv'):

                result = process_calendar_file_csv(uploaded_file)
                return render(request, 'calendario/observeCalendar.html', {'result': result})

            fs = FileSystemStorage()
            fs.save(uploaded_file.name, uploaded_file)

    return render(request, 'calendario/observeCalendar.html')

def process_calendar_file_csv(upload_file):
    data = upload_file.read().decode("utf-8").splitlines()

    # Get the header row and the data rows
    header = data[0]
    rows = data[1:]

    # Split the header into field names
    field_names = header.split(';')

    # Create a list of dictionaries
    result = []
    for row in rows:
        values = row.split(';')
        item = {}
        for i, field_name in enumerate(field_names):
            item[field_name] = values[i]
        result.append(item)
    return result

def home(request):
    return render(request, 'calendario/homePage.html')

