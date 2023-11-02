from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect, get_object_or_404

# Create your views here.

import sys
import json
import csv
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, Http404, JsonResponse
from django.db.models import Q
from django.urls import reverse
from django.core.checks import messages
from io import StringIO
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
#     #     #Inês
#     #     self.over_population_button = QPushButton("Aulas em Sobrelotação", self)
#     #     self.over_population_button.clicked.connect(self.over_population_button_clicked)
#     #     self.layout.addWidget(self.over_population_button)
#     #
#     #     self.centralWidget().setLayout(self.layout)
#
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
#     def json_to_csv(self, input_file_or_url):
#         try:
#             with self.get_input_stream(input_file_or_url) as input_stream:
#                 json_data = json.load(input_stream)
#                 csv_data = json_data[0].keys()  # Extract the field names
#
#                 options = QFileDialog.Options()
#                 file_path, _ = QFileDialog.getSaveFileName(
#                     self, "Save CSV File", "", "CSV Files (*.csv);;All Files (*)", options=options)
#
#                 if file_path:
#                     with open(file_path, "w", newline="", encoding="utf-8") as csv_file:
#                         csv_writer = csv.DictWriter(csv_file, csv_data)
#                         csv_writer.writeheader()
#                         csv_writer.writerows(json_data)
#                     QMessageBox.information(self, "Success", "Successfully converted to: " + file_path)
#         except Exception as e:
#             QMessageBox.critical(self, "Error", "Error converting JSON to CSV: " + str(e))
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
#     #Inês
#     def over_population_button_clicked(self):
#         input_file = self.input_file_text.text()
#
#         if ".json" in input_file:
#             input_file = self.json_to_csv(self, input_file)
#
#         try:
#             with self.get_input_stream(input_file) as input_stream:
#                 csv_data = input_stream.read().decode("utf-8")
#                 csv_data = [line.split(';') for line in csv_data.split('\n') if line]  # Convert CSV string to a list of lists
#
#                 if csv_data:
#                     header_row = csv_data[0]
#                     lotacao_index = -1  # Initialize with an invalid index
#                     inscritos_index = -1  # Initialize with an invalid index
#
#                     # Find the index of the columns dynamically
#                     for index, column_name in enumerate(header_row):
#                         if "Lotação" in column_name:
#                             lotacao_index = index
#                         if "Inscritos no turno" in column_name:
#                             inscritos_index = index
#
#                     if lotacao_index != -1 and inscritos_index != -1:
#                         # Valid columns found, proceed with checking for overpopulation
#
#                         with open("overpopulated_classes.csv", "w", newline="", encoding="utf-8") as csv_file:
#                             csv_writer = csv.writer(csv_file)
#
#                             # Write the header row to the output file
#                             csv_writer.writerow(header_row)
#
#                             for row in csv_data[1:]:
#                                 try:
#                                     lotacao = int(row[lotacao_index])
#                                     inscritos = int(row[inscritos_index])
#                                     if isinstance(lotacao, int) and isinstance(inscritos, int):
#                                         if inscritos > lotacao:
#                                             print(row)
#                                             csv_writer.writerow(row)
#                                 except ValueError as e:
#                                     pass
#                         csv_file.close()
#
#         except Exception as e:
#             QMessageBox.critical(self, "Error", "Error showing Over Population: " + str(e))
#
#         # Display a message indicating the process is complete
#         QMessageBox.information(self, "Overpopulation Classes", "Overpopulated classes have been saved to 'overpopulated_classes.csv'.")
#
# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     ex = AppGUI()
#     ex.show()
#     sys.exit(app.exec_())


# def convertView(request):
#     print("ola1")
#     if request.method == 'POST':
#         uploaded_file = request.POST.get('uploaded_file')  # Add a hidden input field in your HTML form for this
#         print("ola2")
#
#         # Instantiate the AppGUI class
#         # aplicacao = AppGUI()
#         print("ola3")
#         app = AppGUI()
#         app.convert_button_clicked(uploaded_file)
#         print("ola4")
#     return render(request, 'calendario/homePage.html')

def csv_to_json(uploaded_file):
    try:
        data = uploaded_file.read().decode("utf-8")
        json_data = json.dumps(list(csv.DictReader(data.splitlines())))
        return json_data
    except Exception as e:
        return str(e)

def json_to_csv(uploaded_file):
    try:
        json_data = json.load(uploaded_file)
        csv_data = json_data[0].keys()
        csv_io = StringIO()

        csv_writer = csv.writer(csv_io)
        csv_writer.writerow(csv_data)

        for row in json_data:
            csv_writer.writerow([row[key] for key in csv_data])

        csv_io.seek(0)

        # Save the file to a location on the server
        file_path = os.path.join(settings.MEDIA_ROOT, 'converted.csv')
        with open(file_path, 'wb') as csv_file:
            csv_file.write(csv_io.read())

        return file_path  # Return the path to the saved file
    except Exception as e:
        return str(e)


def download_csv(file_name):
    file_path = os.path.join(settings.MEDIA_ROOT, 'csv_files', file_name)
    with open(file_path, 'rb') as csv_file:
        response = FileResponse(csv_file)
    return response

def download_json(file_name):
    file_path = os.path.join(settings.MEDIA_ROOT, 'json_files', file_name)
    with open(file_path, 'rb') as json_file:
        response = FileResponse(json_file)
    return response


def convertView(request):
    if request.method == 'POST':
        uploaded_file = request.FILES.get('uploaded_file')  # Ensure the input field in your HTML form is named 'uploaded_file'
        if uploaded_file:
            if uploaded_file.name.endswith(".csv"):
                # Handle CSV to JSON conversion
                file_path = csv_to_json(uploaded_file)
                file_name = os.path.basename(file_path)
                with open(file_path, 'r') as file:
                    file_data = file.read()
                download_link = reverse('download_json', args=[file_name])
                return JsonResponse({"download_link": download_link})
            elif uploaded_file.name.endswith(".json"):
                # Handle JSON to CSV conversion
                file_path = json_to_csv(uploaded_file)
                file_name = os.path.basename(file_path)
                with open(file_path, 'r') as file:
                    file_data = file.read()
                download_link = reverse('download_csv', args=[file_name])
                return JsonResponse({"download_link": download_link})
    return render(request, 'calendario/homePage.html')



def home(request):
    return render(request, 'calendario/homePage.html')

