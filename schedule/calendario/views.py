from django.contrib.auth import authenticate, login
from django.core.files.storage import FileSystemStorage
from django.shortcuts import render, redirect, get_object_or_404

# Create your views here.


from django.http import JsonResponse
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
import re
from datetime import datetime

app_name = 'src'
global events_data
events_data = []

# Listar critérios de qualidade
def get_information_sections(file):
    global lotacao_index, inscritos_index, sala_index, sala_expectavel, sala_real
    global salas_desperdicadas_list, salas_sem_caracteristicas_list, aulas_sobrelotadas_list, aulas_sem_sala_list
    salas_desperdicadas_list=[]
    salas_sem_caracteristicas_list=[]
    aulas_sobrelotadas_list=[]
    aulas_com_sala_list=[]
    aulas_sem_sala_list=[]

    try:
        with file as input_stream:
            csv_data = input_stream.read().decode("utf-8")
            csv_data = [line.split(';') for line in csv_data.split('\n') if line]  # Convert CSV string to a list of lists
            header_row = csv_data[0]

            if csv_data:
                salas_desperdicadas=0
                salas_sem_caracteristicas=0
                if lotacao_index != -1 and inscritos_index != -1 and sala_index != -1 and sala_expectavel!=-1 and sala_real!=-1:
                    count = 0
                    sum_students = 0
                    aulas_com_sala = 0
                    total_aulas=0
                    tipo_de_sala_expectado=None
                    tipo_de_sala_real=None
                    nao_necessita_sala = 0

                    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    relative_path = os.path.join('calendario', 'static', 'overpopulated_classes.csv')
                    save_path = os.path.join(BASE_DIR, relative_path)
                    with open(save_path, "w", newline="", encoding="utf-8") as csv_file:
                        csv_writer = csv.writer(csv_file)
                        csv_writer.writerow(header_row)
                        for row in csv_data[1:]:
                            try:

                                tipo_de_sala_expectado = row[sala_expectavel]
                                if "Não necessita de sala" in tipo_de_sala_expectado:
                                    nao_necessita_sala+=1

                                lotacao = int(row[lotacao_index])
                                inscritos = int(row[inscritos_index])
                                if isinstance(lotacao, int) and isinstance(inscritos, int):
                                    if inscritos > lotacao:
                                        csv_writer.writerow(row)
                                        count+=1
                                        sum_students+=(inscritos-lotacao)
                                        aulas_sobrelotadas_list.append(row)
                                sala = row[sala_index]
                                aulas_com_sala+=1
                                aulas_com_sala_list.append(row)

                                tipo_de_sala_real = row[sala_real]
                                result = get_class_room_characteristics(tipo_de_sala_expectado, tipo_de_sala_real)
                                if result[0]>0:
                                    salas_desperdicadas+=result[0]
                                    salas_desperdicadas_list.append(row)
                                if result[1]>0:
                                    salas_sem_caracteristicas+=result[1]
                                    salas_sem_caracteristicas_list.append(row)
                                if row not in aulas_com_sala_list:
                                    aulas_sem_sala_list.append(row)
                            except ValueError as e:
                                print(str(e))
                            total_aulas+=1
                    return count, sum_students, total_aulas-aulas_com_sala-nao_necessita_sala, salas_desperdicadas, salas_sem_caracteristicas
    except Exception as e:
        return print(str(e))

def get_class_room_characteristics(tipo_de_sala_expectado, tipo_de_sala_real):
    salas_sem_caracteristicas=0
    salas_desperdicadas=0
    if "Arq" in tipo_de_sala_expectado.strip() and ("Arq" not in tipo_de_sala_real.strip() and "Computadores" not in tipo_de_sala_expectado.strip()):
        salas_sem_caracteristicas+=1
    if "Arq" in tipo_de_sala_real.strip() and ("Arq" not in tipo_de_sala_expectado.strip() and "Computadores" not in tipo_de_sala_real.strip()):
        salas_desperdicadas += 1
    if "Lab" in tipo_de_sala_expectado.strip() and ("Lab" not in tipo_de_sala_real.strip()) and salas_desperdicadas!=1 and salas_sem_caracteristicas!=1:
        salas_sem_caracteristicas += 1
    if "Lab" in tipo_de_sala_real.strip() and ("Lab" not in tipo_de_sala_expectado.strip()) and salas_desperdicadas!=1 and salas_sem_caracteristicas!=1:
        salas_desperdicadas += 1
    if "BYOD" in tipo_de_sala_expectado and "BYOD" not in tipo_de_sala_real and salas_desperdicadas!=1 and salas_sem_caracteristicas!=1:
        salas_sem_caracteristicas += 1
    if "BYOD" in tipo_de_sala_real and "BYOD" not in tipo_de_sala_expectado and salas_desperdicadas!=1 and salas_sem_caracteristicas!=1:
        salas_desperdicadas += 1
    if "videoconferencia" in tipo_de_sala_expectado and "videoconferencia" not in tipo_de_sala_real and salas_desperdicadas!=1 and salas_sem_caracteristicas!=1:
        salas_sem_caracteristicas+=1
    if "videoconferencia" in tipo_de_sala_real and "videoconferencia" not in tipo_de_sala_expectado and salas_desperdicadas != 1 and salas_sem_caracteristicas != 1:
        salas_desperdicadas += 1
    if "Não necessita de sala" in tipo_de_sala_expectado and tipo_de_sala_real and salas_desperdicadas!=1 and salas_sem_caracteristicas!=1:
        salas_desperdicadas+=1
    return salas_desperdicadas, salas_sem_caracteristicas

def get_informations(request):
    global salas_desperdicadas_list, salas_sem_caracteristicas_list, aulas_sobrelotadas_list, aulas_sem_sala_list
    if request.method == 'POST':
        file = request.FILES.get('input_file')

    if not file.name.endswith('.csv'):
        return HttpResponse("Por favor introduza um ficheiro CSV")

    try:
        result = get_information_sections(file)
        if result is None:
            return HttpResponse("An error occurred while processing the file or the columns aren't valid.")

        number, sum_students, aulas_sem_sala, salas_desperdicadas, salas_sem_caracteristicas = result
        return HttpResponse(
            f"Número de aulas em sobrelotação: {number}<br>"
            f"Número de alunos com aulas em sobrelotação: {sum_students}<br>"
            f"Número de aulas sem sala atribuída: {aulas_sem_sala}<br>"
            f"Número de características desperdiçadas nas salas atribuídas às aulas: {salas_desperdicadas}<br>"
            f"Número de salas sem as características solicitadas pelo docente: {salas_sem_caracteristicas}<br><br>"
        )
    except FileNotFoundError or Exception as e:
        return HttpResponse(str(e))

def get_informations_for_plot(file):
    if not file.name.endswith('.csv'):
        return HttpResponse("Por favor introduza um ficheiro CSV")

    try:
        result = get_information_sections(file)
        if result is None:
            return HttpResponse("An error occurred while processing the file or the columns aren't valid.")

        number, sum_students, aulas_sem_sala, salas_desperdicadas, salas_sem_caracteristicas = result
        return number, sum_students, aulas_sem_sala, salas_desperdicadas, salas_sem_caracteristicas

    except FileNotFoundError or Exception as e:
        return HttpResponse(str(e))


# Verificar novo critério de qualidade
def aux_new_criteria(expressao):
    global new_criteria_file
    try:
        print(new_criteria_file)
        csv_file_path = new_criteria_file
        with open(csv_file_path, 'r', encoding='utf-8') as csv_file:
            csv_content = csv_file.read()
        classes_list = []
        csv_data = [line.split(';') for line in csv_content.split('\n') if line]  # Convert CSV string to a list of lists
        count = 0
        classes_list.append(csv_data[0])

        if csv_data:
            for row in csv_data[1:]:
                try:
                    # Construir código dinâmico
                    code = f"expression_result = {expressao}"
                    local_vars = {'row': row,
                                  'Curso': (row[curso_index]) if 'Curso' in expressao else None,
                                  'Unidade': (row[unidade_execucao_index]) if 'Unidade' in expressao else None,
                                  'Turno': (row[turno_index]) if 'Turno' in expressao else None,
                                  'Turma': (row[turma_index]) if 'Turma' in expressao else None,
                                  'Inscritos': int(row[inscritos_index]) if 'Inscritos' in expressao else None,
                                  'Dia_Da_Semana': (row[dia_semana_index]) if 'Dia_Da_Semana' in expressao else None,
                                  'Início': (row[inicio_index]) if 'Início' in expressao else None,
                                  'Fim': (row[fim_index]) if 'Fim' in expressao else None,
                                  'Dia_Do_Ano': (row[dia_index]) if 'Dia_Do_Ano' in expressao else None,
                                  'Características_pedidas': (row[sala_expectavel]) if 'Características_pedidas' in expressao else None,
                                  'Sala': (row[sala_index]) if 'Sala' in expressao else None,
                                  'Lotação': int(row[lotacao_index]) if 'Lotação' in expressao else None,
                                  'Características_reais': (row[sala_real]) if 'Características_reais' in expressao else None,
                                  }

                    # Executar código dinâmico
                    exec(code, globals(), local_vars)
                    expression_result = local_vars['expression_result']

                    if expression_result:
                        count += 1
                        classes_list.append(row)
                        print(f'Expressão Avaliada: {expressao}')
                except Exception as e:
                    print(e)
        return count, classes_list
    except Exception as e:
        return HttpResponse('Expressão inválida.')

def calculator(request):
    global new_criteria_file
    if request.method == 'POST':
        uploaded_file = request.FILES.get('criteria_file')
        if uploaded_file:
            if uploaded_file.name.endswith(".csv"):
                file_path = os.path.join(settings.MEDIA_ROOT, uploaded_file.name)

                with open(file_path, 'wb') as destination:
                    for chunk in uploaded_file.chunks():
                        destination.write(chunk)

                new_criteria_file = file_path
    return render(request, 'calendario/calculator.html')

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def calcular_expressao(request):
    if request.method == 'POST':
        expressao = request.POST.get('expressao', '')
        print(expressao)
        count, classes_list = aux_new_criteria(expressao)

        return HttpResponse(str(count))
    return HttpResponse('Método não permitido')

def save_file(file_path, content):
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            file.write(content)
        return file_path
    except Exception as e:
        print(f"Error saving file: {e}")
        return None

# Converter ficheiros para csv ou json
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

def convertView(request):
    if request.method == 'POST':
        uploaded_file = request.FILES['uploaded_file']  # Ensure the input field in your HTML form is named 'uploaded_file'
        if uploaded_file:
            if uploaded_file.name.endswith(".csv"):
                # Handle CSV to JSON conversion
                file_path = csv_to_json(uploaded_file)
                if file_path:
                    # Define the desired save path for the file
                    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    relative_path = os.path.join('calendario', 'static', 'FicheiroConvertidoJson.json')
                    save_path = os.path.join(BASE_DIR, relative_path)
                    # Save the file using the save_file function
                    saved_file_path = save_file(save_path, file_path)

                    if saved_file_path:
                        # If the file was successfully saved, return the download link
                        file_name = os.path.basename(saved_file_path)
                        return JsonResponse({"download_link": saved_file_path})
                    else:
                        # Handle the case where the file couldn't be saved
                        return JsonResponse({"error": "Failed to save the file."})
            elif uploaded_file.name.endswith(".json"):
                # Handle JSON to CSV conversion
                BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                relative_path = os.path.join('calendario', 'static', 'FicheiroConvertidoCsv.csv')
                save_path = os.path.join(BASE_DIR, relative_path)
                result = json_to_csv(uploaded_file.read().decode("utf-8"))
                if result:
                    # Save the CSV data using the save_file function
                    saved_file_path = save_file(save_path, result)

                    if saved_file_path:
                        # If the file was successfully saved, you can return a download link or message here
                        file_name = os.path.basename(saved_file_path)
                        return JsonResponse({"download_link": saved_file_path})
                    else:
                        # Handle the case where the file couldn't be saved
                        return JsonResponse({"error": "Failed to save the CSV file."})
                else:
                    # Handle the case where the conversion or file saving failed
                    return JsonResponse({"error": f"Conversion failed with the following error: {result[1]}"})
    return render(request, 'calendario/homePage.html')

'''
from django.conf import settings

def handle_uploaded_file(uploaded_file, conversion_type):
    if conversion_type == 'csv_to_json':
        # Handle CSV to JSON conversion
        file_path = csv_to_json(uploaded_file)
    elif conversion_type == 'json_to_csv':
        # Handle JSON to CSV conversion
        result = json_to_csv(uploaded_file.read().decode("utf-8"))
        if result:
            file_path = result
        else:
            return None  # Handle the case where the conversion failed

    if file_path:

        if conversion_type == 'csv_to_json':
            rel_path = 'schedule/calendario/static/FicheiroConvertidoJson.json'
        else:
            rel_path = 'schedule/calendario/static/FicheiroConvertidoCsv.csv'

        # Caminho absoluto para o arquivo
        saved_file_path = os.path.join(settings.BASE_DIR, rel_path)

        if saved_file_path:
            return saved_file_path
        else:
            return None  # Handle the case where the file couldn't be saved
    else:
        return None  # Handle the case where the conversion failed


def handle_remote_file(remote_file_url, conversion_type):
    response = requests.get(remote_file_url)

    if response.status_code == 200:
        content = response.content

        # Create a temporary file from the content
        temp_file_path = create_temp_file(content)

        if temp_file_path:
            # Call the main function to handle the temporary file
            return handle_uploaded_file(temp_file_path, conversion_type)
        else:
            return None  # Handle the case where creating a temporary file failed
    else:
        return None  # Handle the case where downloading the remote file failed


def create_temp_file(content):
    # Create a temporary file and write the content
    temp_file_path = '/tmp/temp_file'  # You need to replace this with a proper temporary file path
    with open(temp_file_path, 'wb') as temp_file:
        temp_file.write(content)

    return temp_file_path


def convertView(request):
    global BASE_DIR
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if request.method == 'POST':
        if 'uploaded_file' in request.FILES:
            uploaded_file = request.FILES['uploaded_file']
            if uploaded_file.name.endswith(".csv"):
                saved_file_path = handle_uploaded_file(uploaded_file, 'csv_to_json')
            elif uploaded_file.name.endswith(".json"):
                saved_file_path = handle_uploaded_file(uploaded_file, 'json_to_csv')

            if saved_file_path:
                # If the file was successfully processed and saved, you can return a download link or message here
                file_name = os.path.basename(saved_file_path)
                return JsonResponse({"download_link": saved_file_path})
            else:
                # Handle the case where processing the file failed
                return JsonResponse({"error": "Failed to process the file."})

        elif 'remote_file_url' in request.POST:
            remote_file_url = request.POST['remote_file_url']
            saved_file_path = handle_remote_file(remote_file_url, 'csv_to_json')  # Adjust the conversion_type as needed

            if saved_file_path:
                # If the file was successfully processed and saved, you can return a download link or message here
                file_name = os.path.basename(saved_file_path)
                return JsonResponse({"download_link": saved_file_path})
            else:
                # Handle the case where processing the remote file failed
                return JsonResponse({"error": "Failed to process the remote file."})

    return render(request, 'calendario/homePage.html')
'''

# Criar novo horário
def class_rooms(request):
    if request.method == 'POST':
        class_rooms_file = request.FILES.get('class_rooms')
        classes_file = request.FILES.get('classes')

        if not class_rooms_file.name.endswith('.csv') or not classes_file.name.endswith('.csv'):
            return HttpResponse("Please upload valid CSV files")

        with class_rooms_file as class_rooms_input:
            class_rooms_csv_data = class_rooms_input.read().decode("utf-8")
            class_rooms_csv_data = [line.split(';') for line in class_rooms_csv_data.split('\n') if line]

        with classes_file as input_stream:
            csv_data = input_stream.read().decode("utf-8")
            csv_data = [line.split(';') for line in csv_data.split('\n') if line]  # Convert CSV string to a list of lists
            header_row = csv_data[0]
            if csv_data and class_rooms_csv_data:
                BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                relative_path = os.path.join('calendario', 'static', 'HorarioNovo.csv')
                save_path = os.path.join(BASE_DIR, relative_path)

                with open(save_path, "w", newline="", encoding="utf-8") as csv_file:
                    csv_writer = csv.writer(csv_file, delimiter=';')
                    csv_writer.writerow(header_row)
                    # Constrói o índice das salas

                    chosen_schedules = []

                    for row in csv_data[1:]:
                        try:
                            print("Linha " + str(csv_data.index(row)))

                            row_without_times = row[:6]
                            times = False
                            while times is False:
                                start_time, end_time = get_times(row, chosen_schedules, header_row)
                                if start_time is not None and end_time is not None:
                                    times = True

                            row_without_times.extend([start_time, end_time])
                            row_without_times.extend(row[8:-3])

                            available = False
                            while not available:
                                if "Não necessita de sala" in row[
                                    header_row.index('Características da sala pedida para a aula')]:
                                    available_room, lotacao_room, caracteristicas_sala_dada = '', '', ''
                                    available = True
                                    break  # Sair do loop quando a sala não é necessária
                                else:
                                    available_room, lotacao_room, caracteristicas_sala_dada = find_available_room(
                                        class_rooms_csv_data, row, header_row, chosen_schedules
                                    )
                                    if available_room is not None:
                                        available = True

                            row_without_times.extend([available_room, lotacao_room, caracteristicas_sala_dada])
                            csv_writer.writerow(row_without_times)

                            chosen_schedules.append(
                        {'turma': row[header_row.index('Turma')], 'dia': row[header_row.index('Dia')], 'start_time': start_time,
                         'end_time': end_time, 'sala': available_room})

                        except ValueError as e:
                                print(str(e))
    if save_path:
        # If the file was successfully saved, return the download link
        return JsonResponse({"download_link": save_path})
    return render(request, 'calendario/homePage.html')

import random


def get_times(row, chosen_schedules, header_row):
    start_time = {'A': '13:00:00', 'B': '08:00:00', 'C': '13:00:00', 'PL': '18:00:00'}
    end_time = {'A': '17:30:00', 'B': '12:30:00', 'C': '17:30:00', 'PL': '22:30:00'}
    duration = {'A': [60, 90, 120, 180], 'B': [60, 90, 120, 180], 'C': [60, 90, 120, 180], 'PL': [60, 90, 120, 180]}

    if "PL" in row[header_row.index('Turma')]:
        ano_letivo_match = 'PL'
    elif "Sáb" in row[header_row.index('Dia da Semana')]:
        ano_letivo_match = 'B'
    else:
        ano_letivo_match = re.search(r'([A-Ca-c])\d', row[header_row.index('Turma')])

    # Verifica se houve correspondência na expressão regular
    if ano_letivo_match:
        if isinstance(ano_letivo_match, str):
            ano_letivo = ano_letivo_match
        else:
            ano_letivo = ano_letivo_match.group(1)
    else:
        ano_letivo = 'C'

    if ano_letivo in start_time and ano_letivo in end_time:
        start_time_minutes = convert_to_minutes(start_time[ano_letivo])
        end_time_minutes = convert_to_minutes(end_time[ano_letivo])

        # Escolhe um valor aleatório entre start_range e end_range em incrementos de 30 minutos
        chosen_start_minutes = random.randint(start_time_minutes, end_time_minutes - 30)

        # Convertendo a diferença em minutos para um número de incrementos de 30 minutos
        minute_difference = (end_time_minutes - chosen_start_minutes)

        # Gerando um número aleatório de incrementos de 30 minutos e convertendo de volta para minutos
        duration_in_minutes = random.choice(duration[ano_letivo])
        chosen_end_minutes = chosen_start_minutes + duration_in_minutes

        day = row[header_row.index('Dia da Semana')]
        turma = row[header_row.index('Turma')]

        # Lógica para verificar sobreposição com aulas já agendadas
        for schedule_entry in chosen_schedules:
            if (
                    schedule_entry['turma'] == turma
                    and schedule_entry['dia'] == day
                    and overlap(convert_to_time(chosen_start_minutes), end, schedule_entry['start_time'],
                                schedule_entry['end_time'])
            ):
                return None, None
        if (convert_to_minutes(convert_to_time(chosen_end_minutes)) - convert_to_minutes(convert_to_time(chosen_start_minutes)) == 60
                or convert_to_minutes(convert_to_time(chosen_end_minutes)) - convert_to_minutes(convert_to_time(chosen_start_minutes)) == 90
                or convert_to_minutes(convert_to_time(chosen_end_minutes)) - convert_to_minutes(convert_to_time(chosen_start_minutes)) == 120
                or convert_to_minutes(convert_to_time(chosen_end_minutes)) - convert_to_minutes(convert_to_time(chosen_start_minutes)) == 180):
            print(f"Aula para {ano_letivo} - Início: {convert_to_time(chosen_start_minutes)},Fim: {convert_to_time(chosen_end_minutes)} - Sala disponível.")
            return convert_to_time(chosen_start_minutes), convert_to_time(chosen_end_minutes)

    return None, None

def convert_to_minutes(time_string):
    # Converte uma string de tempo para minutos
    hours, minutes, _ = map(int, time_string.split(':'))
    return hours * 60 + minutes

def convert_to_time(minutes):
    hours, remainder = divmod(minutes, 60)
    if remainder > 30:
        return f"{hours:02d}:00:00"
    else:
        return f"{hours:02d}:30:00"

def find_available_room(class_rooms_csv_data, row, header_row, chosen_schedules):
    day = row[header_row.index('Dia')]
    start_time = row[header_row.index('Início')]
    end_time = row[header_row.index('Fim')]
    sala_pedida = row[header_row.index('Características da sala pedida para a aula')]
    aula = row[header_row.index('Unidade de execução')]
    header_row = class_rooms_csv_data[0]

    for room_row in class_rooms_csv_data[1:]:
        room_id = room_row[header_row.index('Nome sala')]

        # Switch case para determinar o tipo de sala com base na sala_pedida
        if "Arq" in sala_pedida and "Computadores" not in sala_pedida:
            # Colunas que contêm "Arq"
            feature = [col for col in header_row if 'Arq' in col and 'Computadores' not in col]
            caracteristicas_sala_dada = has_feature(feature, room_row, header_row)
            if caracteristicas_sala_dada is not None and not room_has_class(chosen_schedules, room_id, day, start_time, end_time):
                return room_id, room_row[header_row.index('Capacidade Normal')], caracteristicas_sala_dada
        elif "Lab ISTA" in sala_pedida:
            '''if "electr" in aula.lower():
                print(aula)
                feature = [col for col in header_row if 'Laboratório de Electrónica' in col]
            '''
            if "Jornalismo" in sala_pedida:
                feature = [col for col in header_row if 'Jornalismo' in col]
            else:
                feature = [col for col in header_row if 'Laboratório' in col and "Jornalismo" not in col and "D" not in room_id]
            caracteristicas_sala_dada = has_feature(feature, room_row, header_row)
            if caracteristicas_sala_dada is not None and not room_has_class(chosen_schedules, room_id, day, start_time, end_time):
                return room_id, room_row[header_row.index('Capacidade Normal')], caracteristicas_sala_dada
        elif "Lab" in sala_pedida and not "ISTA" in sala_pedida:
            feature = [col for col in header_row if 'Laboratório' not in room_id and 'Laboratório' in col]
            caracteristicas_sala_dada = has_feature(feature, room_row, header_row)
            if caracteristicas_sala_dada is not None and not room_has_class(chosen_schedules, room_id, day, start_time, end_time):
                return room_id, room_row[header_row.index('Capacidade Normal')], caracteristicas_sala_dada
        elif "BYOD" in sala_pedida and not room_has_class(chosen_schedules, room_id, day, start_time, end_time):
            feature = [col for col in header_row if 'BYOD' in col]
            caracteristicas_sala_dada = has_feature(feature, room_row, header_row)
            if caracteristicas_sala_dada is not None:
                return room_id, room_row[header_row.index('Capacidade Normal')], caracteristicas_sala_dada
        elif "videoconferencia" in sala_pedida and not room_has_class(chosen_schedules, room_id, day, start_time, end_time):
            feature = [col for col in header_row if 'videoconferencia' in col]
            caracteristicas_sala_dada = has_feature(feature, room_row, header_row)
            if caracteristicas_sala_dada is not None:
                return room_id, room_row[header_row.index('Capacidade Normal')], caracteristicas_sala_dada
        elif "Não necessita de sala" in sala_pedida:
            return '', ''
        elif "Auditório" in sala_pedida or "auditório" in sala_pedida:
            feature = [col for col in header_row if 'Auditório' in col or 'auditório' in col]
            caracteristicas_sala_dada = has_feature(feature, room_row, header_row)
            if caracteristicas_sala_dada is not None and not room_has_class(chosen_schedules, room_id, day, start_time, end_time):
                return room_id, room_row[header_row.index('Capacidade Normal')], caracteristicas_sala_dada
        elif "aulas" in sala_pedida or "Aulas" in sala_pedida:
            if "Auditório" in sala_pedida:
                feature = [col for col in header_row if 'Auditório' in col]
            elif "Anfiteatro" in sala_pedida:
                feature = [col for col in header_row if 'Anfiteatro' in col]
            else:
                feature = [col for col in header_row if ('Aulas' in col or 'aulas' in col) and 'Anfiteatro' not in room_id and 'Auditório' not in room_id]
            caracteristicas_sala_dada = has_feature(feature, room_row, header_row)
            if caracteristicas_sala_dada is not None and not room_has_class(chosen_schedules, room_id, day, start_time, end_time):
                return room_id, room_row[header_row.index('Capacidade Normal')], caracteristicas_sala_dada

    return None, None, None  # Retorna None se não houver sala disponível

def has_feature(feature, room_row, header_row):
    features = []
    for column in feature:
        # Verifica se a célula contém "X"
        if room_row[header_row.index(column)] == 'X':
            features.append(str(column))
    if len(features) > 0:
        return ", ".join(features)
    return None

def room_has_class(chosen_schedules, room_id, day, start_time, end_time):
    # Verifica se a sala está ocupada no arquivo de aulas

    for schedule_entry in chosen_schedules:

        if (
                schedule_entry['sala'] == room_id
                and schedule_entry['dia'] == day
                and overlap(start_time, end_time, schedule_entry['start_time'],
                            schedule_entry['end_time'])
        ):
            print("Sala " + room_id + " ocupada.")
            return True  # A sala está ocupada
    print("Sala " + room_id + " disponível.")
    return False  # A sala está disponível

def overlap(start_time_1, end_time_1, start_time_2, end_time_2):
    # Converte os tempos de string para objetos time
    start_time_1 = convert_to_minutes(start_time_1)
    #print(start_time_1)
    end_time_1 = convert_to_minutes(end_time_1)
    start_time_2 = convert_to_minutes(start_time_2)
    end_time_2 = convert_to_minutes(end_time_2)
    '''print(start_time_2)
    print(end_time_1)
    print(end_time_2)
    '''

    # Verifica se há sobreposição de horários
    condition_1 = start_time_1 < start_time_2 < end_time_1
    condition_2 = start_time_1 < end_time_2 < end_time_1
    condition_3 = start_time_2 < start_time_1 < end_time_2
    condition_4 = start_time_2 < end_time_1 < end_time_2

    return condition_1 or condition_2 or condition_3 or condition_4

'''
def save_file(save_path, file_content):
    with open(save_path, 'w', encoding='utf-8') as file:
        file.write(file_content)
    return save_path
'''

def home(request):
    return render(request, 'calendario/homePage.html')

import json
from django.http import JsonResponse
import io

def observeCalendar(request):
    global curso_index
    global unidade_execucao_index
    global turno_index
    global turma_index
    global inscritos_index
    global dia_semana_index
    global inicio_index
    global fim_index
    global dia_index
    global sala_expectavel
    global sala_index
    global lotacao_index
    global sala_real

    global salas_desperdicadas_list, salas_sem_caracteristicas_list, aulas_sobrelotadas_list, aulas_sem_sala_list

    salas_desperdicadas_list = []
    salas_sem_caracteristicas_list = []
    aulas_sobrelotadas_list = []
    aulas_com_sala_list = []
    aulas_sem_sala_list = []

    if request.method == 'POST' and 'file' in request.FILES:
        uploaded_file = request.FILES['file']
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        relative_path = os.path.join('calendario', 'static')
        save_path = os.path.join(BASE_DIR, relative_path)
        fs = FileSystemStorage(location=save_path)
        filename = fs.save(uploaded_file.name, uploaded_file)

        try:
            curso_index = int(request.POST.get('curso_index'))
            unidade_execucao_index = int(request.POST.get('unidade_execucao_index'))
            turno_index = int(request.POST.get('turno_index'))
            turma_index = int(request.POST.get('turma_index'))
            inscritos_index = int(request.POST.get('inscritos_index'))
            dia_semana_index = int(request.POST.get('dia_semana_index'))
            inicio_index = int(request.POST.get('inicio_index'))
            fim_index = int(request.POST.get('fim_index'))
            dia_index = int(request.POST.get('dia_index'))
            sala_expectavel = int(request.POST.get('sala_expectavel'))
            sala_index = int(request.POST.get('sala_index'))
            lotacao_index = int(request.POST.get('lotacao_index'))
            sala_real = int(request.POST.get('sala_real'))
        except ValueError:
            # Handle the case where conversion to int fails
            return HttpResponse("Invalid input for indices. Please provide valid integer values.")


        if uploaded_file and uploaded_file.name.endswith('.csv'):
            with io.TextIOWrapper(uploaded_file.file, encoding='UTF-8') as file:
                csv_reader = csv.DictReader(file, delimiter=';')
                data = [row for row in csv_reader]
            events = process_csv_to_events(data)
            events_data = [
                {
                    'title': event['title'],
                    'start': event['start_time'],
                    'end': event['end_time'],
                    'quality': event['quality']
                }
                for event in events
            ]
            return render(request, 'calendario/observeCalendar.html', {'events_json': events_data})

    return render(request, 'calendario/observeCalendar.html')

import os

def get_events(request):
    global salas_desperdicadas_list, salas_sem_caracteristicas_list, aulas_sobrelotadas_list, aulas_sem_sala_list
    # Replace with the absolute path to your CSV file
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    relative_path = os.path.join('calendario', 'static', 'HorarioDeExemplo.csv')
    file_path = os.path.join(BASE_DIR, relative_path)
    if file_path.endswith('.csv'):
        with open(file_path, 'r', encoding="UTF-8") as file:
            csv_reader = csv.DictReader(file, delimiter=';')
            data = [row for row in csv_reader]
        events = process_csv_to_events(data)
        events_data = [
            {
                'title': event['title'],
                'start': event['start_time'],
                'end': event['end_time'],
                'quality': event['quality']
            }
            for event in events
        ]
        return JsonResponse({'events_json': events_data}, safe=False)

    return JsonResponse({'error': 'Invalid file or file not found'}, status=400)


def process_csv_to_events(data):
    global salas_desperdicadas_list, salas_sem_caracteristicas_list, aulas_sobrelotadas_list, aulas_sem_sala_list
    events = []

    # Read CSV data and extract relevant information
    for row in data:
        # Extract fields from the CSV row
        title = "{} - {}".format(row.get(r'\ufeffCurso', ''), row.get('Unidade de execução', ''))
        start_time = convert_to_iso_format(f"{row['Dia']};{row['Início']}")
        end_time = convert_to_iso_format(f"{row['Dia']};{row['Fim']}")
        quality = False
        if len(aulas_sobrelotadas_list) > 0:
            if row in aulas_sobrelotadas_list:
                quality = True
        # Create event object and add to the events list
        event = {
            'title': title,
            'start_time': start_time,
            'end_time': end_time,
            'quality':  quality
            # Add other event details as needed
        }
        events.append(event)
    return events

def convert_to_iso_format(datetime_str):
    components = datetime_str.split(';')

    # Check if both day and time components are present
    if len(components) == 2 and components[0] and components[1]:
        dia = components[0]
        hora = components[1]
        final = f"{dia.split('/')[2]}-{dia.split('/')[1]}-{dia.split('/')[0]}T{hora}"
        return final
    else:
        # Handle the case when either day or time is missing
        # You might want to customize this part based on your requirements
        print("Invalid date/time format:", datetime_str)
        return "2024-00-00T00:00:00"

import plotly.graph_objects as go
from django.shortcuts import render

def cordas_view(request):
    cursos_list = []
    sala_curso_dict = {}
    if request.method == 'POST':
        chord_file = request.FILES.get('chord_file')

        try:
            with chord_file as input_stream:
                csv_data = input_stream.read().decode("utf-8")
                csv_data = [line.split(';') for line in csv_data.split('\n') if line]  #
                header_row = csv_data[0]
                curso_index = header_row.index("\ufeffCurso")
                sala_index = header_row.index("Sala da aula")
                if csv_data:
                    for row in csv_data[1:]:
                        try:
                            curso = row[curso_index]
                            sala = row[sala_index]

                            new_cursos = curso.split(', ')

                            for i in new_cursos:
                                if i not in cursos_list:
                                    cursos_list.append(i)
                            sala_curso_dict[sala] = curso
                        except ValueError as e:
                            print(str(e))

        except Exception as e:
            return print(str(e))

        print(cursos_list)
        print(sala_curso_dict)
        fig = go.Figure(go.Sankey(
            node=dict(
                pad=15,
                thickness=20,
                line=dict(color="black", width=0.5),
                label=cursos_list,
            ),
            link=dict(
                source=[0, 0, 1, 1, 2, 2, 3],
                target=[2, 3, 2, 4, 3, 4, 4],
                value=[8, 4, 2, 8, 4, 2, 2, 8],
            )
        ))
        fig.update_layout(title_text="Chord Diagram Example")
        graph_json = fig.to_json()

    return render(request, 'calendario/cordas.html', {'graph_json':graph_json})

import plotly.graph_objects as go

def heatmap_view(request):
    z = [[.1, .3, .5, .7, .9],
                 [1, .8, .6, .4, .2],
                 [.2, 0, .5, .7, .9],
                 [.9, .8, .4, .2, 0],
                 [.3, .4, .5, .7, 1]]

    fig = px.imshow(z, text_auto=True)

    graph_json = fig.to_json()
    return render(request, 'calendario/heatmap.html', {'graph_json': graph_json})
