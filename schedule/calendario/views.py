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

                    save_path = r"C:\Users\inesc\OneDrive - ISCTE-IUL\Documentos\Iscte\Mestrado\ADS\projetoADSdjango\schedule\calendario\static\overpopulated_classes.csv"
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
                                        aulas_sobrelotadas_list.append(row)
                                sala = row[sala_index]
                                aulas_com_sala+=1
                                aulas_com_sala_list.append(row)

                                tipo_de_sala_expectado = row[sala_expectavel]
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
                    return count, sum_students, total_aulas-aulas_com_sala, salas_desperdicadas, salas_sem_caracteristicas
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
        if number==0:
            return HttpResponse("Erro ao recolher número de aulas em sobrelotação.")
        if sum_students==0:
            return HttpResponse("Erro ao recolher número de alunos com aulas em sobrelotação.")
        if aulas_sem_sala==0:
            return HttpResponse("Erro ao recolher número de aulas sem sala atribuída.")
        if salas_desperdicadas == 0:
            return HttpResponse("Erro ao recolher número de características desperdiçadas nas salas atribuídas às aulas.")
        if salas_sem_caracteristicas == 0:
            return HttpResponse("Erro ao recolher número de salas sem as características solicitadas pelo docente.")
            #Número de alunos em sobrelotação é número de alunos a mais em cada sobrelotação ou número total dessas aulas???
        return HttpResponse(
            f"Número de aulas em sobrelotação: {number}<br>"
            f"Número de alunos com aulas em sobrelotação: {sum_students}<br>"
            f"Número de aulas sem sala atribuída: {aulas_sem_sala}<br>"
            f"Número de características desperdiçadas nas salas atribuídas às aulas: {salas_desperdicadas}<br>"
            f"Número de salas sem as características solicitadas pelo docente: {salas_sem_caracteristicas}<br><br>"
            f"Aulas desperdiçadas: {salas_desperdicadas_list}<br><br>"
            f"Aulas sem características: {salas_sem_caracteristicas_list}<br><br>"
            f"Aulas sobrelotadas: {aulas_sobrelotadas_list}<br><br>"
            f"Aulas sem sala: {aulas_sem_sala_list}<br><br>"
        )
    # Retirar listas!!!!!
    except FileNotFoundError or Exception as e:
        return HttpResponse(str(e))

def aux_new_criteria(expressao):
    try:
        csv_file_path = r"C:\Users\inesc\OneDrive - ISCTE-IUL\Documentos\Iscte\Mestrado\ADS\projetoADSdjango\schedule\calendario\static\HorarioDeExemplo.csv"
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

#Para apagar
def find_columns(campo):
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


    if "Curso" in campo:
        return curso_index
    if "Unidade" in campo or "Cadeira" in campo:
        return unidade_execucao_index
    if "Inscritos no turno" in campo:
        return inscritos_index
    if "Turno" in campo or "turno" in campo:
        return turno_index
    if "Turma" in campo:
        return turma_index
    if "Dia" in campo and "Semana" in campo:
        return dia_semana_index
    if "Início" in campo:
        return inicio_index
    if "Fim" in campo:
        return fim_index
    if "Dia" in campo and "Semana" not in campo:
        return dia_index
    if "Características" in campo and "pedida" in campo:
        return sala_expectavel
    if "Sala" in campo and "pedida" not in campo and "reais" not in campo:
        return sala_index
    if "Lotação" in campo:
        return lotacao_index
    if "Características" in campo and "reais" in campo:
        return sala_real

def calculator(request):
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
        uploaded_file = request.FILES.get('uploaded_file')  # Ensure the input field in your HTML form is named 'uploaded_file'
        if uploaded_file:
            if uploaded_file.name.endswith(".csv"):
                # Handle CSV to JSON conversion
                file_path = csv_to_json(uploaded_file)
                if file_path:
                    # Define the desired save path for the file
                    save_path = r"C:\Users\inesc\OneDrive - ISCTE-IUL\Documentos\Iscte\Mestrado\ADS\projetoADSdjango\schedule\calendario\static\FicheiroConvertidoJson.json"

                    # Save the file using the save_file function
                    saved_file_path = save_file(save_path, file_path)

                    if saved_file_path:
                        # If the file was successfully saved, return the download link
                        file_name = os.path.basename(saved_file_path)
                        return JsonResponse({"download_link": saved_file_path})
                        '''download_link = reverse('download_file', args=[file_name])
                        return JsonResponse({"download_link": download_link})'''
                    else:
                        # Handle the case where the file couldn't be saved
                        return JsonResponse({"error": "Failed to save the file."})
            elif uploaded_file.name.endswith(".json"):
                # Handle JSON to CSV conversion

                save_path = r"C:\Users\inesc\OneDrive - ISCTE-IUL\Documentos\Iscte\Mestrado\ADS\projetoADSdjango\schedule\calendario\static\FicheiroConvertidoCsv.csv"
                #success, error = json_to_csv(uploaded_file.read().decode("utf-8"))
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
                save_path = r"C:\Users\inesc\OneDrive - ISCTE-IUL\Documentos\Iscte\Mestrado\ADS\projetoADSdjango\schedule\calendario\static\HorarioNovo.csv"
                with open(save_path, "w", newline="", encoding="utf-8") as csv_file:
                    csv_writer = csv.writer(csv_file, delimiter=';')
                    csv_writer.writerow(header_row)

                    chosen_schedules = []

                    for row in csv_data[1:]:
                        try:
                            print("Linha " + str(csv_data.index(row)))
                    # Usando DictReader para mapear o cabeçalho aos valores em cada linha
                    #csv_reader = csv.DictReader(input_stream, delimiter=';')

                    #for row in csv_data:
                        #try:
                            #row_without_times = [row[key] for key in header_row[:5]]
                            row_without_times = row[:6]
                            times = False
                            while times is False:
                                start_time, end_time = get_times(row, chosen_schedules, header_row)
                                if start_time is not None and end_time is not None:
                                    print("Cucu com horas")
                                    times = True

                            row_without_times.extend([start_time, end_time])
                            #row_without_times.extend(start_time, end_time)
                            row_without_times.extend(row[8:-3])

                            # Se encontrar uma sala disponível, adiciona à linha de dados
                            header_row_class_rooms = class_rooms_csv_data[0]

                            # Constrói o índice das salas
                            room_index = build_room_index(class_rooms_csv_data, header_row_class_rooms)

                            available = False
                            while not available:
                                if "Não necessita de sala" in row[
                                    header_row.index('Características da sala pedida para a aula')]:
                                    available_room, lotacao_room, caracteristicas_sala_dada = '', '', ''
                                    available = True
                                    break  # Sair do loop quando a sala não é necessária
                                else:
                                    print("Eu passo-me")
                                    available_room, lotacao_room, caracteristicas_sala_dada = find_available_room(
                                        class_rooms_csv_data, row, header_row, chosen_schedules, room_index
                                    )
                                    if available_room is not None:
                                        available = True

                            row_without_times.extend([available_room, lotacao_room, caracteristicas_sala_dada])
                            csv_writer.writerow(row_without_times)
                            #row_without_last_three_columns.extend(available_room, lotacao_room, sala_dada)
                            #csv_writer.writerow(row_without_last_three_columns)

                            chosen_schedules.append(
                        {'turma': row[header_row.index('Turma')], 'dia': row[header_row.index('Dia')], 'start_time': start_time,
                         'end_time': end_time, 'sala': available_room})

                        except ValueError as e:
                                print(str(e))

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
        minute_difference = (end_time_minutes - chosen_start_minutes) // 30

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
                print(
                    f"Aula para {ano_letivo} - Início: {convert_to_time(chosen_start_minutes)}, Fim: {convert_to_time(chosen_end_minutes)} - Sala indisponível (sobreposição de horários).")
                return None, None

        print(
            f"Aula para {ano_letivo} - Início: {convert_to_time(chosen_start_minutes)},Fim: {convert_to_time(chosen_end_minutes)} - Sala disponível.")
        return convert_to_time(chosen_start_minutes), convert_to_time(chosen_end_minutes)

    return None, None

def convert_to_minutes(time_string):
    # Converte uma string de tempo para minutos
    hours, minutes, _ = map(int, time_string.split(':'))
    return hours * 60 + minutes

def convert_to_time(minutes):
    hours, remainder = divmod(minutes, 60)
    minutes, _ = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:00"

def build_room_index(class_rooms_csv_data, header_row):
    room_index = {}

    for room_row in class_rooms_csv_data[1:]:
        room_id = room_row[header_row.index('Nome sala')]
        characteristics = {}

        for column in header_row:
            if 'Arq' in column and 'Computadores' not in column:
                characteristics[column] = room_row[header_row.index(column)]
            elif 'Lab' in column:
                characteristics[column] = room_row[header_row.index(column)]
            elif 'BYOD' in column:
                characteristics[column] = room_row[header_row.index(column)]
            elif 'videoconferencia' in column:
                characteristics[column] = room_row[header_row.index(column)]
            elif 'Auditório' in column or 'auditório' in column:
                characteristics[column] = room_row[header_row.index(column)]
            elif 'Aulas' in column or 'aulas' in column or 'Sala' in column:
                characteristics[column] = room_row[header_row.index(column)]


        room_index[room_id] = {
            'lotacao': room_row[header_row.index('Capacidade Normal')],
            'caracteristicas': characteristics
        }

    return room_index

def find_available_room(class_rooms_csv_data, row, header_row, chosen_schedules, room_index):
    day = row[header_row.index('Dia')]
    start_time = row[header_row.index('Início')]
    end_time = row[header_row.index('Fim')]
    sala_pedida = row[header_row.index('Características da sala pedida para a aula')]

    for room_id, room_info in room_index.items():
        print("Juro que estou a tentar")
        # Verifica se a sala atende a pelo menos uma característica marcada na sala_pedida
        #characteristic_index = has_feature(sala_pedida.split(','), room_info['caracteristicas'], header_row)
        #if characteristic_index is not None:
        if any(room_info['caracteristicas'].get(characteristic) == 'X' for characteristic in sala_pedida.split(' ')):
            print("Há uma :0")

            characteristic_index = has_feature(sala_pedida.split(','), room_info['caracteristicas'], header_row)
            print(characteristic_index)
            if not room_has_class(chosen_schedules, room_id, day, start_time, end_time):
                print("E não tem aulas :0")
                return room_id, room_info['lotacao'], room_info['caracteristicas']
                #return room_id, room_info['lotacao'],  room_info['caracteristicas'][header_row.index(characteristic)]

    for room_id, room_info in room_index.items():
        if "Arq" not in room_info['caracteristicas'] and "Lab" not in room_info['caracteristicas'] and "Auditório" not in room_info['caracteristicas']:
            if not room_has_class(chosen_schedules, room_id, day, start_time, end_time):
                return room_id, room_info['lotacao'], room_info['caracteristicas']

    return None, None, None  # Retorna None se não houver sala disponível

def has_feature(features, room_row, header_row):
    for index, column in enumerate(header_row):
        if any(feature in column for feature in features):
            # Verifica se a célula contém "X"
            if room_row[index] == 'X':
                return index

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
    # Verifica se há sobreposição de horários
    return start_time_1 < end_time_2 and start_time_2 < end_time_1

def save_file(save_path, file_content):
    with open(save_path, 'w', encoding='utf-8') as file:
        file.write(file_content)
    return save_path

def home(request):
    return render(request, 'calendario/homePage.html')

import json
from django.http import JsonResponse


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
        fs = FileSystemStorage(location=r"C:\Users\inesc\OneDrive - ISCTE-IUL\Documentos\Iscte\Mestrado\ADS\projetoADSdjango\schedule\calendario\static")
        filename = fs.save(uploaded_file.name, uploaded_file)
        #print(uploaded_file)

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
            with open(uploaded_file.temporary_file_path(), 'r', encoding="UTF-8") as file:
                csv_reader = csv.DictReader(file, delimiter=';')
                data = [row for row in csv_reader]
            events = process_csv_to_events(data)
            events_data = [
                {
                    'title': event['title'],
                    'start': event['start_time'],
                    'end': event['end_time'],
                }
                for event in events
            ]
            #events_json = json.dumps(events)
            return render(request, 'calendario/observeCalendar.html', {'events_json': events_data})

    return render(request, 'calendario/observeCalendar.html')

import os

def get_events(request):
    global salas_desperdicadas_list, salas_sem_caracteristicas_list, aulas_sobrelotadas_list, aulas_sem_sala_list
    # Replace with the absolute path to your CSV file
    file_path = r"C:\Users\inesc\OneDrive - ISCTE-IUL\Documentos\Iscte\Mestrado\ADS\projetoADSdjango\schedule\calendario\static\HorarioDeExemplo.csv"
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
        #print(events_data)
        return JsonResponse({'events_json': events_data}, safe=False)

    return JsonResponse({'error': 'Invalid file or file not found'}, status=400)


def process_csv_to_events(data):
    global salas_desperdicadas_list, salas_sem_caracteristicas_list, aulas_sobrelotadas_list, aulas_sem_sala_list
    events = []


    # Read CSV data and extract relevant information
    for row in data:
        # Extract fields from the CSV row
        #print(row)
        #title = f"{row[r'\\ufeffCurso']} - {row['Unidade de execução']}"
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

def heatmap_view(request):
    z = [[.1, .3, .5, .7, .9],
         [1, .8, .6, .4, .2],
         [.2, 0, .5, .7, .9],
         [.9, .8, .4, .2, 0],
         [.3, .4, .5, .7, 1]]

    fig = px.imshow(z, text_auto=True)

    graph_json = fig.to_json()

    return render(request, 'calendario/heatmap.html', {'graph_json': graph_json})

import plotly.graph_objects as go
from django.shortcuts import render

def cordas_view(request):
    fig = go.Figure(go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=["A", "B", "C", "D", "E"],
        ),
        link=dict(
            source=[0, 0, 1, 1, 2, 2, 3, 3],
            target=[2, 3, 2, 4, 3, 4, 3, 4],
            value=[8, 4, 2, 8, 4, 2, 2, 8],
        )
    ))

    fig.update_layout(title_text="Chord Diagram Example")
    graph_json = fig.to_json()

    return render(request, 'calendario/cordas.html', {'graph_json': graph_json})