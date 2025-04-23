from .views import obtener_configuraciones
from django.http import JsonResponse
from .models import Database, Mapa
from urllib.parse import urlencode
from django.utils import timezone
from django.conf import settings
from django.urls import reverse
from django.db.models import Q
import openai
import json
import re

def modelsettings(request):
    if request.method == 'POST':
        try:
            quest_id = request.POST.get('idSetings')
            hawkySettings = obtener_configuraciones(quest_id)
            modelData = hawkySettings[f'redes_sociales_{quest_id}']
            parsed_data = json.loads(modelData)
            return JsonResponse(parsed_data, status=200)
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'#{quest_id} no encontrada.'}, status=404)
    return JsonResponse({'success': False, 'message': 'Acción no permitida.'}, status=400)

def chatgpt(question, instructions):
    client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": instructions},
            {"role": "user", "content": question},
        ],
        temperature=0,
    )
    
    print(f"Prompt:{response.usage.prompt_tokens}")
    print(f"Compl:{response.usage.completion_tokens}")
    print(f"Total:{response.usage.total_tokens}")
    print()

    print(f"Respuesta: {response.choices[0].message.content}")

    return response.choices[0].message.content

def buscar_por_tags(pregunta):
    pregunta_tokens = re.findall(r'\b\w+\b', pregunta.lower())
    query = Q()
    for token in pregunta_tokens:
        query |= Q(tags__icontains=token)
    
    posibles = Database.objects.filter(query)
    resultados = []

    for item in posibles:
        item_tags = item.get_tag_list()
        coincidencias = set(pregunta_tokens) & set(item_tags)
        resultados.append((item, len(coincidencias)))

    resultados = sorted(resultados, key=lambda x: x[1], reverse=True)
    print(f"Pregunta: {pregunta}")
    print(f"Tokens: {pregunta_tokens}")
    print(f"Resultados: {resultados}")

    return [item for item, score in resultados if score > 0][:3]

def is_map(best_results, question):
    tag_map = any("mapa" in r.get_tag_list() for r in best_results)

    if tag_map:
        tokens_question = set(re.findall(r'\b\w+\b', question.lower()))
        places_name = Mapa.objects.filter(is_marker=False)

        for destiny in places_name:
            tokens_name = set(re.findall(r'\b\w+\b', destiny.nombre.lower()))
            if tokens_name & tokens_question:
                return destiny.nombre
            
    return False

def chatbot(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            pregunta = data.get('question', '').strip()
            ahora = timezone.localtime(timezone.now()).strftime('%d-%m-%Y_%H%M')

            mejores_resultados = buscar_por_tags(pregunta)

            if mejores_resultados:
                bloques_info = "\n\n".join([f"Tema relacionado:\n{r.informacion}" for r in mejores_resultados])
                system_prompt = (
                    f"Eres Hawky, asistente virtual de la Universidad Tecnológica de Coahuila (UTC). "
                    f"Usa emojis, no saludes, no repreguntes. "
                    f"Responde únicamente en base a la siguiente información:\n\n{bloques_info}\n\n"
                    f"Hoy es {ahora}."
                )
                respuesta_gpt = chatgpt(pregunta, system_prompt)

                destiny_map = is_map(mejores_resultados, pregunta)
                base_url = mejores_resultados[0].redirigir if hasattr(mejores_resultados[0], 'redirigir') else None

                if destiny_map:
                    map_url = reverse('map')
                    params = urlencode({'origin': 'Caseta 1', 'destiny': destiny_map})
                    base_url = f"{map_url}?{params}"

                respuesta = {
                    "titulo": mejores_resultados[0].titulo,
                    "informacion": respuesta_gpt,
                    "redirigir": base_url,
                    "imagenes": mejores_resultados[0].imagen.url if mejores_resultados[0].imagen else None
                }

                print(f'Bloques: {bloques_info}')
                print(f'Respuesta: {respuesta}')

            else:
                baseUrl = reverse('faq')
                pill = 'pills-create-quest-tab'
                respuesta = {
                    "informacion": "Lo siento, no encontré información relacionada con lo que me pides 🤔. "
                                   "Puedes consultar la página oficial de la UTC o escribirnos directamente. 😊",
                    "redirigir": f"{baseUrl}?tab={pill}",
                    "blank": False,
                }
            
            return JsonResponse({'success': True, 'answer': respuesta})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Error: {str(e)}'})
