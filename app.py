import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from supabase import create_client, Client
from PIL import Image
import io
import tempfile
import os
import uuid
import re
import hashlib
import time

# ============================================
# CONFIGURACION DE SUPABASE
# ============================================
def init_supabase():
    try:
        supabase_url = st.secrets["SUPABASE_URL"]
        supabase_key = st.secrets["SUPABASE_KEY"]
        supabase: Client = create_client(supabase_url, supabase_key)
        return supabase
    except Exception as e:
        st.error(f"Error de conexión con Supabase: {str(e)}")
        st.stop()

supabase = init_supabase()

# ============================================
# URL DE LA IMAGEN DE FONDO
# ============================================
FONDO_URL = "https://assets.change.org/photos/0/lt/kp/EelTkpfkXQbEiEQ-800x450-noPad.jpg?1528608279"

# ============================================
# FUNCIÓN PARA DÓLAR
# ============================================
def get_dolar():
    try:
        response = supabase.table("configuracion").select("dolar").eq("id", 1).execute()
        if response.data and response.data[0].get("dolar"):
            return float(response.data[0]["dolar"])
        return 55.0
    except Exception:
        return 55.0

def actualizar_dolar_manual(nuevo_valor):
    try:
        supabase.table("configuracion").update({"dolar": nuevo_valor}).eq("id", 1).execute()
        return True
    except Exception:
        return False

# ============================================
# BASE DE DATOS DE ENFERMEDADES (200 ENFERMEDADES)
# ============================================
BASE_DATOS_ENFERMEDADES = {
    # === ENFERMEDADES CARDIOVASCULARES (15) ===
    "Hipertensión Arterial": {
        "sintomas": ["dolor de cabeza", "visión borrosa", "fatiga", "palpitaciones", "mareos", "sangrado nasal", "dificultad para respirar", "zumbido en oídos"],
        "factores_riesgo": ["sobrepeso", "obesidad", "tabaquismo", "sedentarismo", "estrés", "historia familiar", "consumo de sal"],
        "especialidad": "Cardiología",
        "urgencia": "Alta",
        "recomendaciones": ["Medir presión arterial diariamente", "Reducir consumo de sal", "Ejercicio regular", "Consulta con cardiólogo"],
        "tratamiento": "Enalapril, losartán, diuréticos, cambios en estilo de vida",
        "solo_mujeres": False
    },
    "Hipotensión Arterial": {
        "sintomas": ["mareos", "visión borrosa", "fatiga", "náuseas", "palidez", "desmayos", "dificultad para concentrarse", "sed"],
        "factores_riesgo": ["deshidratación", "embarazo", "problemas cardíacos", "diabetes", "anemia", "medicamentos"],
        "especialidad": "Cardiología",
        "urgencia": "Media",
        "recomendaciones": ["Aumentar consumo de líquidos", "Consumir sal moderadamente", "Evitar cambios bruscos de posición", "Consulta con cardiólogo"],
        "tratamiento": "Aumento de líquidos, sal en dieta, medicamentos según causa",
        "solo_mujeres": False
    },
    "Isquemia Cardíaca": {
        "sintomas": ["dolor en el pecho", "dificultad para respirar", "fatiga", "palpitaciones", "dolor en brazo izquierdo", "náuseas", "sudoración"],
        "factores_riesgo": ["hipertensión", "colesterol alto", "tabaquismo", "diabetes", "sedentarismo", "historia familiar"],
        "especialidad": "Cardiología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR A URGENCIAS INMEDIATAMENTE", "Reposo absoluto", "No automedicarse", "Consulta con cardiólogo urgente"],
        "tratamiento": "Nitroglicerina, antiagregantes, angioplastia, cirugía de bypass",
        "solo_mujeres": False
    },
    "Infarto Agudo de Miocardio": {
        "sintomas": ["dolor en el pecho", "dificultad para respirar", "sudoración", "náuseas", "vómitos", "dolor en brazo izquierdo", "palpitaciones", "ansiedad"],
        "factores_riesgo": ["hipertensión", "colesterol alto", "tabaquismo", "diabetes", "sedentarismo", "historia familiar", "obesidad"],
        "especialidad": "Cardiología",
        "urgencia": "Alta",
        "recomendaciones": ["LLAMAR AL 911 INMEDIATAMENTE", "Reposo absoluto", "No automedicarse", "Masticar aspirina si no es alérgico"],
        "tratamiento": "Angioplastia, trombolíticos, anticoagulantes, cirugía de bypass",
        "solo_mujeres": False
    },
    "Arritmia Cardíaca": {
        "sintomas": ["palpitaciones", "mareos", "dificultad para respirar", "dolor en el pecho", "fatiga", "desmayos", "ansiedad"],
        "factores_riesgo": ["hipertensión", "enfermedad coronaria", "hipertiroidismo", "consumo de cafeína", "estrés", "tabaquismo"],
        "especialidad": "Cardiología",
        "urgencia": "Media",
        "recomendaciones": ["Evitar cafeína y alcohol", "Manejar el estrés", "Consulta con cardiólogo", "Monitoreo cardíaco"],
        "tratamiento": "Antiarrítmicos, betabloqueadores, marcapasos",
        "solo_mujeres": False
    },
    "Insuficiencia Cardíaca": {
        "sintomas": ["dificultad para respirar", "fatiga", "hinchazón de pies", "hinchazón de tobillos", "aumento de peso", "tos", "palpitaciones"],
        "factores_riesgo": ["hipertensión", "enfermedad coronaria", "diabetes", "obesidad", "tabaquismo", "historia familiar"],
        "especialidad": "Cardiología",
        "urgencia": "Alta",
        "recomendaciones": ["Control de peso", "Reducir consumo de sal", "Ejercicio moderado", "Consulta con cardiólogo"],
        "tratamiento": "Diuréticos, betabloqueadores, inhibidores ECA",
        "solo_mujeres": False
    },
    "Angina de Pecho": {
        "sintomas": ["dolor en el pecho", "opresión en el pecho", "dificultad para respirar", "fatiga", "náuseas", "sudoración", "mareos"],
        "factores_riesgo": ["hipertensión", "colesterol alto", "tabaquismo", "diabetes", "sedentarismo", "estrés"],
        "especialidad": "Cardiología",
        "urgencia": "Alta",
        "recomendaciones": ["Reposo inmediato", "Nitroglicerina sublingual", "Evitar esfuerzos", "Consulta con cardiólogo"],
        "tratamiento": "Nitroglicerina, betabloqueadores, aspirina",
        "solo_mujeres": False
    },
    "Aneurisma Aórtico": {
        "sintomas": ["dolor abdominal", "dolor en el pecho", "dolor de espalda", "palpitaciones", "dificultad para respirar", "náuseas", "vómitos"],
        "factores_riesgo": ["hipertensión", "tabaquismo", "colesterol alto", "historia familiar", "edad > 60"],
        "especialidad": "Cardiología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR A URGENCIAS INMEDIATAMENTE", "Reposo absoluto", "No automedicarse", "Consulta con cirujano vascular"],
        "tratamiento": "Cirugía de reparación, stent endovascular",
        "solo_mujeres": False
    },
    "Fibrilación Auricular": {
        "sintomas": ["palpitaciones", "mareos", "dificultad para respirar", "fatiga", "dolor en el pecho", "desmayos", "ansiedad"],
        "factores_riesgo": ["hipertensión", "enfermedad coronaria", "hipertiroidismo", "diabetes", "consumo de alcohol"],
        "especialidad": "Cardiología",
        "urgencia": "Alta",
        "recomendaciones": ["Control médico urgente", "Evitar alcohol y cafeína", "Monitoreo cardíaco", "Consulta con cardiólogo"],
        "tratamiento": "Anticoagulantes, betabloqueadores, cardioversión",
        "solo_mujeres": False
    },
    "Taquicardia Sinusal": {
        "sintomas": ["palpitaciones", "ansiedad", "mareos", "dificultad para respirar", "fatiga", "dolor en el pecho", "sudoración"],
        "factores_riesgo": ["estrés", "ansiedad", "fiebre", "anemia", "hipertiroidismo", "consumo de cafeína"],
        "especialidad": "Cardiología",
        "urgencia": "Media",
        "recomendaciones": ["Técnicas de relajación", "Evitar estimulantes", "Consulta con cardiólogo", "Monitoreo cardíaco"],
        "tratamiento": "Betabloqueadores, manejo de ansiedad",
        "solo_mujeres": False
    },
    "Bradicardia Sinusal": {
        "sintomas": ["fatiga", "mareos", "desmayos", "dificultad para respirar", "palpitaciones", "confusión", "dolor en el pecho"],
        "factores_riesgo": ["edad avanzada", "hipotiroidismo", "bloqueo cardíaco", "medicamentos", "enfermedad coronaria"],
        "especialidad": "Cardiología",
        "urgencia": "Media",
        "recomendaciones": ["Consulta con cardiólogo", "Monitoreo cardíaco", "Evitar medicamentos que bajen la frecuencia"],
        "tratamiento": "Marcapasos, ajuste de medicamentos",
        "solo_mujeres": False
    },
    "Cardiopatía Isquémica": {
        "sintomas": ["dolor en el pecho", "dificultad para respirar", "fatiga", "palpitaciones", "náuseas", "sudoración", "mareos"],
        "factores_riesgo": ["hipertensión", "colesterol alto", "tabaquismo", "diabetes", "sedentarismo", "historia familiar"],
        "especialidad": "Cardiología",
        "urgencia": "Alta",
        "recomendaciones": ["Control de factores de riesgo", "Dieta saludable", "Ejercicio moderado", "Consulta con cardiólogo"],
        "tratamiento": "Aspirina, estatinas, betabloqueadores, revascularización",
        "solo_mujeres": False
    },
    "Miocardiopatía Dilatada": {
        "sintomas": ["dificultad para respirar", "fatiga", "hinchazón de pies", "hinchazón de tobillos", "palpitaciones", "dolor en el pecho"],
        "factores_riesgo": ["infecciones virales", "alcoholismo", "hipertensión", "historia familiar", "embarazo"],
        "especialidad": "Cardiología",
        "urgencia": "Alta",
        "recomendaciones": ["Control médico estricto", "Dieta baja en sal", "Ejercicio moderado", "Consulta con cardiólogo"],
        "tratamiento": "Diuréticos, betabloqueadores, inhibidores ECA, trasplante",
        "solo_mujeres": False
    },
    "Endocarditis Infecciosa": {
        "sintomas": ["fiebre", "escalofríos", "fatiga", "dolor articular", "dolor muscular", "palpitaciones", "dificultad para respirar"],
        "factores_riesgo": ["válvulas cardíacas dañadas", "drogas intravenosas", "infecciones dentales", "catéteres"],
        "especialidad": "Cardiología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR A URGENCIAS INMEDIATAMENTE", "Reposo", "Antibióticos", "Consulta con cardiólogo"],
        "tratamiento": "Antibióticos intravenosos, cirugía de válvulas",
        "solo_mujeres": False
    },
    "Pericarditis": {
        "sintomas": ["dolor en el pecho", "fiebre", "fatiga", "dificultad para respirar", "palpitaciones", "tos", "náuseas"],
        "factores_riesgo": ["infecciones virales", "enfermedades autoinmunes", "insuficiencia renal", "traumatismos"],
        "especialidad": "Cardiología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR A URGENCIAS INMEDIATAMENTE", "Reposo", "Antiinflamatorios", "Consulta con cardiólogo"],
        "tratamiento": "Antiinflamatorios, colchicina, corticoides",
        "solo_mujeres": False
    },
    
    # === ENFERMEDADES RESPIRATORIAS (15) ===
    "Bronquitis Aguda": {
        "sintomas": ["tos", "producción de moco", "dificultad para respirar", "sibilancias", "dolor en el pecho", "fiebre", "fatiga"],
        "factores_riesgo": ["tabaquismo", "exposición a contaminantes", "infecciones virales", "bajas defensas", "cambios bruscos de temperatura"],
        "especialidad": "Neumología",
        "urgencia": "Media",
        "recomendaciones": ["Reposo", "Aumentar consumo de líquidos", "Usar humidificador", "Consulta con neumólogo si persiste"],
        "tratamiento": "Broncodilatadores, antiinflamatorios, antibióticos si es bacteriana",
        "solo_mujeres": False
    },
    "Bronquitis Crónica": {
        "sintomas": ["tos crónica", "producción de moco", "dificultad para respirar", "fatiga", "sibilancias", "infecciones frecuentes"],
        "factores_riesgo": ["tabaquismo", "exposición a contaminantes", "infecciones repetidas", "historia familiar"],
        "especialidad": "Neumología",
        "urgencia": "Media",
        "recomendaciones": ["Dejar de fumar", "Evitar contaminantes", "Rehabilitación pulmonar", "Consulta con neumólogo"],
        "tratamiento": "Broncodilatadores, corticosteroides, oxigenoterapia",
        "solo_mujeres": False
    },
    "Catarro Común (Resfriado)": {
        "sintomas": ["congestión nasal", "estornudos", "tos", "dolor de garganta", "fiebre leve", "fatiga", "dolor de cabeza"],
        "factores_riesgo": ["cambios de temperatura", "bajas defensas", "contacto con personas enfermas", "estrés"],
        "especialidad": "Medicina General",
        "urgencia": "Baja",
        "recomendaciones": ["Reposo", "Aumentar consumo de líquidos", "Té con miel y limón", "Consulta si empeora"],
        "tratamiento": "Antihistamínicos, analgésicos, descongestionantes",
        "solo_mujeres": False
    },
    "Neumonía": {
        "sintomas": ["fiebre alta", "tos con flema", "dificultad para respirar", "dolor en el pecho", "fatiga", "escalofríos", "sudoración"],
        "factores_riesgo": ["edad avanzada", "tabaquismo", "enfermedades crónicas", "bajas defensas", "influenza"],
        "especialidad": "Neumología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR AL MÉDICO URGENTEMENTE", "Reposo absoluto", "Aumentar líquidos", "No automedicarse"],
        "tratamiento": "Antibióticos, antipiréticos, oxigenoterapia si es necesario",
        "solo_mujeres": False
    },
    "Neumonía Viral": {
        "sintomas": ["fiebre", "tos seca", "dificultad para respirar", "fatiga", "dolor muscular", "dolor de cabeza", "escalofríos"],
        "factores_riesgo": ["edad avanzada", "inmunosupresión", "enfermedades crónicas", "tabaquismo"],
        "especialidad": "Neumología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR AL MÉDICO URGENTEMENTE", "Reposo", "Hidratación", "Oxigenoterapia si es necesario"],
        "tratamiento": "Antivirales, antipiréticos, oxigenoterapia",
        "solo_mujeres": False
    },
    "Neumonía Bacteriana": {
        "sintomas": ["fiebre alta", "tos con flema purulenta", "dificultad para respirar", "dolor en el pecho", "escalofríos", "fatiga"],
        "factores_riesgo": ["edad avanzada", "tabaquismo", "enfermedades crónicas", "inmunosupresión"],
        "especialidad": "Neumología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR AL MÉDICO URGENTEMENTE", "Antibióticos", "Reposo", "Hidratación"],
        "tratamiento": "Antibióticos, antipiréticos, oxigenoterapia",
        "solo_mujeres": False
    },
    "Asma Bronquial": {
        "sintomas": ["dificultad para respirar", "sibilancias", "tos", "opresión en el pecho", "fatiga", "sensación de ahogo"],
        "factores_riesgo": ["alergias", "historia familiar", "tabaquismo", "obesidad", "exposición a alérgenos"],
        "especialidad": "Neumología",
        "urgencia": "Alta",
        "recomendaciones": ["Usar inhalador de rescate", "Evitar alérgenos", "Consulta con neumólogo"],
        "tratamiento": "Broncodilatadores, corticosteroides inhalados",
        "solo_mujeres": False
    },
    "Asma Alérgica": {
        "sintomas": ["dificultad para respirar", "sibilancias", "tos", "opresión en el pecho", "fatiga", "sensación de ahogo"],
        "factores_riesgo": ["alergias", "historia familiar", "exposición a alérgenos", "cambios climáticos"],
        "especialidad": "Neumología",
        "urgencia": "Alta",
        "recomendaciones": ["Evitar alérgenos", "Usar inhalador", "Consulta con neumólogo", "Tratamiento de alergias"],
        "tratamiento": "Broncodilatadores, corticosteroides, antihistamínicos",
        "solo_mujeres": False
    },
    "EPOC (Enfermedad Pulmonar Obstructiva Crónica)": {
        "sintomas": ["dificultad para respirar", "tos crónica", "producción de moco", "fatiga", "sibilancias", "opresión en el pecho"],
        "factores_riesgo": ["tabaquismo", "exposición a contaminantes", "historia familiar", "edad > 40"],
        "especialidad": "Neumología",
        "urgencia": "Alta",
        "recomendaciones": ["Dejar de fumar", "Rehabilitación pulmonar", "Uso de broncodilatadores", "Consulta con neumólogo"],
        "tratamiento": "Broncodilatadores, corticosteroides, oxigenoterapia",
        "solo_mujeres": False
    },
    "Enfisema Pulmonar": {
        "sintomas": ["dificultad para respirar", "tos crónica", "producción de moco", "fatiga", "pérdida de peso", "opresión en el pecho"],
        "factores_riesgo": ["tabaquismo", "exposición a contaminantes", "historia familiar", "edad > 50"],
        "especialidad": "Neumología",
        "urgencia": "Alta",
        "recomendaciones": ["Dejar de fumar", "Rehabilitación pulmonar", "Oxigenoterapia", "Consulta con neumólogo"],
        "tratamiento": "Broncodilatadores, corticosteroides, oxigenoterapia",
        "solo_mujeres": False
    },
    "Fibrosis Pulmonar": {
        "sintomas": ["dificultad para respirar", "tos seca", "fatiga", "pérdida de peso", "dolor en el pecho", "dedos en palillo"],
        "factores_riesgo": ["exposición a toxinas", "tabaquismo", "enfermedades autoinmunes", "historia familiar"],
        "especialidad": "Neumología",
        "urgencia": "Alta",
        "recomendaciones": ["Oxigenoterapia", "Rehabilitación pulmonar", "Evitar irritantes", "Consulta con neumólogo"],
        "tratamiento": "Pirfenidona, nintedanib, oxigenoterapia",
        "solo_mujeres": False
    },
    "Neumotórax": {
        "sintomas": ["dolor en el pecho", "dificultad para respirar", "tos", "fatiga", "palpitaciones", "ansiedad"],
        "factores_riesgo": ["tabaquismo", "enfermedad pulmonar", "traumatismos", "historia familiar"],
        "especialidad": "Neumología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR A URGENCIAS INMEDIATAMENTE", "Oxigenoterapia", "Reposo", "No automedicarse"],
        "tratamiento": "Toracocentesis, drenaje pleural, cirugía",
        "solo_mujeres": False
    },
    "Derrame Pleural": {
        "sintomas": ["dificultad para respirar", "dolor en el pecho", "tos", "fiebre", "fatiga", "pérdida de peso"],
        "factores_riesgo": ["insuficiencia cardíaca", "infecciones", "cáncer", "enfermedades autoinmunes"],
        "especialidad": "Neumología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR AL MÉDICO URGENTEMENTE", "Toracocentesis", "Tratamiento de la causa", "Consulta con neumólogo"],
        "tratamiento": "Toracocentesis, diuréticos, tratamiento de la causa",
        "solo_mujeres": False
    },
    "Tuberculosis Pulmonar": {
        "sintomas": ["tos crónica", "fiebre", "sudoración nocturna", "pérdida de peso", "fatiga", "hemoptisis", "dolor en el pecho"],
        "factores_riesgo": ["contacto con infectados", "inmunosupresión", "desnutrición", "tabaquismo", "hacinamiento"],
        "especialidad": "Infectología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR AL MÉDICO URGENTEMENTE", "Aislamiento", "Tratamiento antituberculoso", "Seguimiento médico"],
        "tratamiento": "Antibióticos para TB (isoniazida, rifampicina, etambutol, pirazinamida)",
        "solo_mujeres": False
    },
    "SARS-CoV-2 (COVID-19)": {
        "sintomas": ["fiebre", "tos", "dificultad para respirar", "fatiga", "dolor de cabeza", "pérdida de olfato", "pérdida de gusto", "dolor de garganta"],
        "factores_riesgo": ["edad avanzada", "enfermedades crónicas", "obesidad", "inmunosupresión", "contacto con infectados"],
        "especialidad": "Infectología",
        "urgencia": "Alta",
        "recomendaciones": ["AISLAMIENTO INMEDIATO", "ACUDIR AL MÉDICO URGENTEMENTE", "Hidratación", "Monitoreo de oxígeno"],
        "tratamiento": "Antivirales, antipiréticos, oxigenoterapia, vacunación",
        "solo_mujeres": False
    },
    "Gripe (Influenza)": {
        "sintomas": ["fiebre alta", "tos", "dolor de garganta", "dolor muscular", "dolor de cabeza", "fatiga", "escalofríos"],
        "factores_riesgo": ["contacto con personas enfermas", "bajas defensas", "cambios de temperatura"],
        "especialidad": "Medicina General",
        "urgencia": "Media",
        "recomendaciones": ["Reposo", "Aumentar líquidos", "Antipiréticos", "Consulta si empeora"],
        "tratamiento": "Antivirales, antipiréticos, descanso",
        "solo_mujeres": False
    },
    "Faringitis": {
        "sintomas": ["dolor de garganta", "dificultad para tragar", "fiebre", "fatiga", "dolor de cabeza", "inflamación de ganglios"],
        "factores_riesgo": ["infecciones virales", "tabaquismo", "alergias", "cambios climáticos", "bajas defensas"],
        "especialidad": "Otorrinolaringología",
        "urgencia": "Media",
        "recomendaciones": ["Gárgaras con agua tibia y sal", "Aumentar líquidos", "Reposo vocal", "Consulta si persiste"],
        "tratamiento": "Antibióticos si es bacteriana, antiinflamatorios, analgésicos",
        "solo_mujeres": False
    },
    "Amigdalitis": {
        "sintomas": ["dolor de garganta", "dificultad para tragar", "fiebre", "inflamación de amígdalas", "dolor de cabeza", "fatiga"],
        "factores_riesgo": ["infecciones virales", "bacterianas", "bajas defensas", "contacto con infectados"],
        "especialidad": "Otorrinolaringología",
        "urgencia": "Media",
        "recomendaciones": ["Reposo", "Aumentar líquidos", "Gárgaras", "Consulta con otorrinolaringólogo"],
        "tratamiento": "Antibióticos, antiinflamatorios, analgésicos, cirugía en casos recurrentes",
        "solo_mujeres": False
    },
    "Sinusitis": {
        "sintomas": ["dolor facial", "congestión nasal", "secreción nasal", "dolor de cabeza", "fiebre", "fatiga", "dolor dental"],
        "factores_riesgo": ["alergias", "infecciones respiratorias", "tabaquismo", "pólipos nasales", "desviación del tabique"],
        "especialidad": "Otorrinolaringología",
        "urgencia": "Media",
        "recomendaciones": ["Inhalaciones de vapor", "Descongestionantes", "Aumentar líquidos", "Consulta con otorrinolaringólogo"],
        "tratamiento": "Antibióticos, descongestionantes, corticoides nasales",
        "solo_mujeres": False
    },
    "Rinitis Alérgica": {
        "sintomas": ["estornudos", "congestión nasal", "secreción nasal", "picazón en nariz", "picazón en ojos", "lagrimeo", "tos"],
        "factores_riesgo": ["alergias", "historia familiar", "exposición a alérgenos", "cambios climáticos"],
        "especialidad": "Alergología",
        "urgencia": "Baja",
        "recomendaciones": ["Evitar alérgenos", "Antihistamínicos", "Lavados nasales", "Consulta con alergólogo"],
        "tratamiento": "Antihistamínicos, corticoides nasales, inmunoterapia",
        "solo_mujeres": False
    },
    
    # === ENFERMEDADES NEUROLÓGICAS (15) ===
    "Cefalea Tensional": {
        "sintomas": ["dolor de cabeza", "sensación de presión", "dolor en la nuca", "dolor en los hombros", "irritabilidad", "dificultad para concentrarse"],
        "factores_riesgo": ["estrés", "ansiedad", "falta de sueño", "mala postura", "tensión muscular"],
        "especialidad": "Neurología",
        "urgencia": "Baja",
        "recomendaciones": ["Descanso", "Técnicas de relajación", "Aplicar compresas frías", "Consulta si persiste"],
        "tratamiento": "Analgésicos, relajantes musculares, terapia de relajación",
        "solo_mujeres": False
    },
    "Migraña": {
        "sintomas": ["dolor de cabeza pulsátil", "náuseas", "vómitos", "sensibilidad a la luz", "sensibilidad al sonido", "aura visual", "fatiga"],
        "factores_riesgo": ["estrés", "cambios hormonales", "falta de sueño", "historia familiar", "consumo de alcohol", "alimentos específicos"],
        "especialidad": "Neurología",
        "urgencia": "Media",
        "recomendaciones": ["Descanso en lugar oscuro", "Hidratación", "Evitar factores desencadenantes", "Consulta con neurólogo"],
        "tratamiento": "Triptanos, antiinflamatorios, betabloqueadores",
        "solo_mujeres": False
    },
    "Migraña con Aura": {
        "sintomas": ["aura visual", "dolor de cabeza pulsátil", "náuseas", "vómitos", "sensibilidad a la luz", "sensibilidad al sonido", "fatiga"],
        "factores_riesgo": ["estrés", "cambios hormonales", "historia familiar", "consumo de alcohol", "alimentos específicos"],
        "especialidad": "Neurología",
        "urgencia": "Media",
        "recomendaciones": ["Descanso en lugar oscuro", "Hidratación", "Evitar factores desencadenantes", "Consulta con neurólogo"],
        "tratamiento": "Triptanos, antiinflamatorios, betabloqueadores",
        "solo_mujeres": False
    },
    "Migraña Crónica": {
        "sintomas": ["dolor de cabeza frecuente", "náuseas", "vómitos", "sensibilidad a la luz", "sensibilidad al sonido", "fatiga", "depresión"],
        "factores_riesgo": ["estrés", "cambios hormonales", "historia familiar", "consumo de alcohol", "alimentos específicos"],
        "especialidad": "Neurología",
        "urgencia": "Alta",
        "recomendaciones": ["Consulta con neurólogo", "Tratamiento preventivo", "Evitar factores desencadenantes", "Registro de migrañas"],
        "tratamiento": "Betabloqueadores, antidepresivos, anticonvulsivantes, toxina botulínica",
        "solo_mujeres": False
    },
    "Neuritis": {
        "sintomas": ["dolor agudo", "hormigueo", "entumecimiento", "debilidad muscular", "quemazón", "sensibilidad al tacto", "dificultad para mover"],
        "factores_riesgo": ["diabetes", "alcoholismo", "infecciones virales", "deficiencias nutricionales", "enfermedades autoinmunes"],
        "especialidad": "Neurología",
        "urgencia": "Media",
        "recomendaciones": ["Reposo", "Fisioterapia", "Calor local", "Consulta con neurólogo"],
        "tratamiento": "Antiinflamatorios, analgésicos, vitaminas del complejo B",
        "solo_mujeres": False
    },
    "Neuralgia del Trigémino": {
        "sintomas": ["dolor facial intenso", "dolor en la mandíbula", "dolor en el ojo", "dolor en la mejilla", "espasmos faciales", "sensibilidad al tacto"],
        "factores_riesgo": ["edad > 50", "esclerosis múltiple", "compresión vascular", "traumatismos faciales"],
        "especialidad": "Neurología",
        "urgencia": "Alta",
        "recomendaciones": ["Consulta con neurólogo", "Medicamentos anticonvulsivantes", "Evitar factores desencadenantes", "Cirugía en casos graves"],
        "tratamiento": "Carbamazepina, gabapentina, cirugía descompresiva",
        "solo_mujeres": False
    },
    "Accidente Cerebrovascular (ACV)": {
        "sintomas": ["adormecimiento del labio", "debilidad en un lado del cuerpo", "dificultad para hablar", "visión borrosa", "dolor de cabeza", "mareos", "pérdida de equilibrio"],
        "factores_riesgo": ["hipertensión", "diabetes", "tabaquismo", "colesterol alto", "edad avanzada", "historia familiar"],
        "especialidad": "Neurología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR A URGENCIAS INMEDIATAMENTE", "No automedicarse", "Mantener reposo", "LLAMAR AL 911"],
        "tratamiento": "Trombólisis, anticoagulantes, rehabilitación",
        "solo_mujeres": False
    },
    "Accidente Cerebrovascular Isquémico": {
        "sintomas": ["debilidad en un lado del cuerpo", "dificultad para hablar", "visión borrosa", "mareos", "pérdida de equilibrio", "dolor de cabeza"],
        "factores_riesgo": ["hipertensión", "diabetes", "tabaquismo", "colesterol alto", "edad avanzada", "historia familiar"],
        "especialidad": "Neurología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR A URGENCIAS INMEDIATAMENTE", "No automedicarse", "Mantener reposo", "LLAMAR AL 911"],
        "tratamiento": "Trombólisis, anticoagulantes, rehabilitación",
        "solo_mujeres": False
    },
    "Accidente Cerebrovascular Hemorrágico": {
        "sintomas": ["dolor de cabeza intenso", "náuseas", "vómitos", "debilidad en un lado del cuerpo", "dificultad para hablar", "visión borrosa", "pérdida de conciencia"],
        "factores_riesgo": ["hipertensión", "aneurismas", "malformaciones vasculares", "edad avanzada", "historia familiar"],
        "especialidad": "Neurología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR A URGENCIAS INMEDIATAMENTE", "LLAMAR AL 911", "No automedicarse", "Mantener reposo absoluto"],
        "tratamiento": "Cirugía, control de presión arterial, rehabilitación",
        "solo_mujeres": False
    },
    "Tic Nervioso": {
        "sintomas": ["tic nervioso en el ojo", "movimientos involuntarios", "parpadeo excesivo", "contracciones faciales", "estrés", "ansiedad"],
        "factores_riesgo": ["estrés", "ansiedad", "fatiga", "falta de sueño", "consumo de cafeína"],
        "especialidad": "Neurología",
        "urgencia": "Baja",
        "recomendaciones": ["Reducir el estrés", "Técnicas de relajación", "Dormir adecuadamente", "Consulta con neurólogo si persiste"],
        "tratamiento": "Terapia de relajación, medicamentos en casos severos",
        "solo_mujeres": False
    },
    "Parálisis Facial": {
        "sintomas": ["adormecimiento del labio", "debilidad facial", "caída de un lado de la cara", "dificultad para sonreír", "babeo", "dificultad para cerrar el ojo"],
        "factores_riesgo": ["infecciones virales", "estrés", "diabetes", "embarazo", "sistema inmunológico débil"],
        "especialidad": "Neurología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR AL MÉDICO URGENTEMENTE", "Proteger el ojo", "Fisioterapia facial", "Evitar corrientes de aire"],
        "tratamiento": "Corticosteroides, antivirales, fisioterapia",
        "solo_mujeres": False
    },
    "Parkinson": {
        "sintomas": ["temblores", "rigidez muscular", "bradicinesia", "inestabilidad postural", "dificultad para hablar", "trastornos del sueño", "depresión"],
        "factores_riesgo": ["edad > 60", "historia familiar", "exposición a toxinas", "sexo masculino"],
        "especialidad": "Neurología",
        "urgencia": "Media",
        "recomendaciones": ["Fisioterapia", "Terapia ocupacional", "Ejercicio regular", "Consulta con neurólogo"],
        "tratamiento": "Levodopa, agonistas dopaminérgicos",
        "solo_mujeres": False
    },
    "Alzheimer": {
        "sintomas": ["pérdida de memoria", "confusión", "dificultad para hablar", "cambios de humor", "desorientación", "dificultad para realizar tareas", "aislamiento social"],
        "factores_riesgo": ["edad > 65", "historia familiar", "sedentarismo", "hipertensión", "diabetes", "tabaquismo"],
        "especialidad": "Neurología",
        "urgencia": "Alta",
        "recomendaciones": ["Estimulación cognitiva", "Estructura y rutina", "Apoyo familiar", "Consulta con neurólogo"],
        "tratamiento": "Donepezilo, memantina",
        "solo_mujeres": False
    },
    "Esclerosis Múltiple": {
        "sintomas": ["fatiga", "debilidad muscular", "dificultad para caminar", "visión borrosa", "hormigueo", "entumecimiento", "problemas de equilibrio"],
        "factores_riesgo": ["historia familiar", "sexo femenino", "edad 20-40", "infecciones virales", "clima templado"],
        "especialidad": "Neurología",
        "urgencia": "Alta",
        "recomendaciones": ["Consulta con neurólogo", "Fisioterapia", "Terapia ocupacional", "Medicamentos inmunomoduladores"],
        "tratamiento": "Interferón, glatiramer, corticosteroides",
        "solo_mujeres": False
    },
    "Epilepsia": {
        "sintomas": ["convulsiones", "pérdida de conciencia", "movimientos involuntarios", "mirada fija", "confusión", "miedo intenso", "alteraciones sensoriales"],
        "factores_riesgo": ["historia familiar", "lesiones cerebrales", "infecciones del SNC", "tumores cerebrales", "accidentes cerebrovasculares"],
        "especialidad": "Neurología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR AL MÉDICO URGENTEMENTE", "Medicamentos anticonvulsivantes", "Evitar factores desencadenantes", "Consulta con neurólogo"],
        "tratamiento": "Anticonvulsivantes (carbamazepina, valproato, lamotrigina)",
        "solo_mujeres": False
    },
    "Meningitis": {
        "sintomas": ["fiebre alta", "dolor de cabeza intenso", "rigidez de cuello", "náuseas", "vómitos", "sensibilidad a la luz", "confusión"],
        "factores_riesgo": ["infecciones virales", "bacterianas", "inmunosupresión", "edad avanzada", "contacto con infectados"],
        "especialidad": "Neurología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR A URGENCIAS INMEDIATAMENTE", "LLAMAR AL 911", "No automedicarse", "Aislamiento"],
        "tratamiento": "Antibióticos, antivirales, antipiréticos, hospitalización",
        "solo_mujeres": False
    },
    "Encefalitis": {
        "sintomas": ["fiebre", "dolor de cabeza", "confusión", "convulsiones", "alteraciones del comportamiento", "dificultad para hablar", "debilidad muscular"],
        "factores_riesgo": ["infecciones virales", "inmunosupresión", "picaduras de mosquitos", "edad avanzada"],
        "especialidad": "Neurología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR A URGENCIAS INMEDIATAMENTE", "Hospitalización", "Antivirales", "Reposo"],
        "tratamiento": "Antivirales, corticosteroides, tratamiento sintomático",
        "solo_mujeres": False
    },
    
    # === ENFERMEDADES GASTROINTESTINALES (15) ===
    "Diarrea Aguda": {
        "sintomas": ["deposiciones líquidas", "dolor abdominal", "náuseas", "vómitos", "fiebre", "deshidratación", "pérdida de apetito"],
        "factores_riesgo": ["alimentos contaminados", "virus", "bacterias", "intolerancias alimentarias", "estrés", "medicamentos"],
        "especialidad": "Gastroenterología",
        "urgencia": "Media",
        "recomendaciones": ["Hidratación oral", "Dieta blanda", "Reposo", "Consulta si persiste más de 3 días"],
        "tratamiento": "Sales de rehidratación, probióticos, antidiarreicos",
        "solo_mujeres": False
    },
    "Diarrea Crónica": {
        "sintomas": ["deposiciones líquidas frecuentes", "dolor abdominal", "pérdida de peso", "fatiga", "deshidratación", "malnutrición"],
        "factores_riesgo": ["enfermedad inflamatoria intestinal", "síndrome de intestino irritable", "intolerancias alimentarias", "infecciones crónicas"],
        "especialidad": "Gastroenterología",
        "urgencia": "Media",
        "recomendaciones": ["Consulta con gastroenterólogo", "Dieta específica", "Suplementos nutricionales", "Hidratación"],
        "tratamiento": "Tratamiento de la causa, probióticos, antidiarreicos",
        "solo_mujeres": False
    },
    "Gastroenteritis": {
        "sintomas": ["diarrea", "vómitos", "dolor abdominal", "fiebre", "deshidratación", "pérdida de apetito", "malestar general"],
        "factores_riesgo": ["alimentos contaminados", "falta de higiene", "sistema inmunológico débil", "viajes"],
        "especialidad": "Gastroenterología",
        "urgencia": "Media",
        "recomendaciones": ["Reposo", "Hidratación", "Dieta blanda", "Consulta si hay deshidratación"],
        "tratamiento": "Sales de rehidratación, probióticos, medicamentos según causa",
        "solo_mujeres": False
    },
    "Enfermedad de Crohn": {
        "sintomas": ["dolor abdominal", "diarrea crónica", "fatiga", "pérdida de peso", "sangre en heces", "fiebre", "úlceras bucales"],
        "factores_riesgo": ["historia familiar", "tabaquismo", "edad < 40", "origen judío", "consumo de antiinflamatorios"],
        "especialidad": "Gastroenterología",
        "urgencia": "Media",
        "recomendaciones": ["Dieta baja en fibra", "Suplementos nutricionales", "Evitar irritantes", "Consulta con gastroenterólogo"],
        "tratamiento": "Corticosteroides, inmunomoduladores, biológicos",
        "solo_mujeres": False
    },
    "Colitis Ulcerosa": {
        "sintomas": ["diarrea con sangre", "dolor abdominal", "urgencia defecatoria", "fatiga", "pérdida de peso", "fiebre", "anemia"],
        "factores_riesgo": ["historia familiar", "edad 15-35", "origen judío", "tabaquismo", "factores ambientales"],
        "especialidad": "Gastroenterología",
        "urgencia": "Alta",
        "recomendaciones": ["Consulta con gastroenterólogo", "Dieta específica", "Medicamentos antiinflamatorios", "Control médico"],
        "tratamiento": "Aminosalicilatos, corticosteroides, inmunosupresores",
        "solo_mujeres": False
    },
    "Gastritis": {
        "sintomas": ["dolor abdominal", "náuseas", "vómitos", "sensación de llenura", "pérdida de apetito", "ardor estomacal", "eructos"],
        "factores_riesgo": ["consumo de antiinflamatorios", "estrés", "alcohol", "tabaquismo", "infección por H. pylori"],
        "especialidad": "Gastroenterología",
        "urgencia": "Media",
        "recomendaciones": ["Evitar alimentos irritantes", "Comer porciones pequeñas", "Reducir estrés", "Consulta con gastroenterólogo"],
        "tratamiento": "Antiacidos, protectores gástricos, antibióticos si es por H. pylori",
        "solo_mujeres": False
    },
    "Gastritis Crónica": {
        "sintomas": ["dolor abdominal persistente", "náuseas", "pérdida de apetito", "pérdida de peso", "anemia", "fatiga"],
        "factores_riesgo": ["infección por H. pylori", "consumo crónico de antiinflamatorios", "tabaquismo", "alcoholismo", "enfermedades autoinmunes"],
        "especialidad": "Gastroenterología",
        "urgencia": "Media",
        "recomendaciones": ["Consulta con gastroenterólogo", "Dieta específica", "Medicamentos", "Seguimiento médico"],
        "tratamiento": "Protectores gástricos, antibióticos, cambios en dieta",
        "solo_mujeres": False
    },
    "Úlcera Gástrica": {
        "sintomas": ["dolor abdominal", "ardor", "náuseas", "vómitos", "pérdida de peso", "sangre en heces", "vómitos con sangre"],
        "factores_riesgo": ["consumo de antiinflamatorios", "estrés", "alcohol", "tabaquismo", "infección por H. pylori"],
        "especialidad": "Gastroenterología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR AL MÉDICO URGENTEMENTE", "Evitar alimentos irritantes", "Reducir estrés", "No automedicarse"],
        "tratamiento": "Protectores gástricos, antibióticos, cambios en dieta",
        "solo_mujeres": False
    },
    "Úlcera Duodenal": {
        "sintomas": ["dolor abdominal que mejora con comida", "ardor", "náuseas", "pérdida de peso", "sangre en heces", "vómitos"],
        "factores_riesgo": ["infección por H. pylori", "consumo de antiinflamatorios", "tabaquismo", "alcohol", "estrés"],
        "especialidad": "Gastroenterología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR AL MÉDICO URGENTEMENTE", "Dieta específica", "Medicamentos", "No automedicarse"],
        "tratamiento": "Antibióticos, protectores gástricos, antiácidos",
        "solo_mujeres": False
    },
    "Síndrome de Intestino Irritable": {
        "sintomas": ["dolor abdominal", "distensión", "diarrea", "estreñimiento", "mucosidad en heces", "fatiga", "ansiedad"],
        "factores_riesgo": ["estrés", "ansiedad", "depresión", "historia familiar", "alimentos específicos"],
        "especialidad": "Gastroenterología",
        "urgencia": "Baja",
        "recomendaciones": ["Dieta baja en FODMAP", "Manejo del estrés", "Ejercicio regular", "Consulta con gastroenterólogo"],
        "tratamiento": "Antiespasmódicos, probióticos, cambios en dieta",
        "solo_mujeres": False
    },
    "Reflujo Gastroesofágico (ERGE)": {
        "sintomas": ["acidez", "regurgitación", "dolor en el pecho", "dificultad para tragar", "tos crónica", "ronquera", "sensación de nudo en garganta"],
        "factores_riesgo": ["obesidad", "embarazo", "tabaquismo", "alcohol", "alimentos grasos", "comidas abundantes"],
        "especialidad": "Gastroenterología",
        "urgencia": "Media",
        "recomendaciones": ["Evitar comidas abundantes", "Elevar cabecera de cama", "Reducir peso", "Consulta con gastroenterólogo"],
        "tratamiento": "Antiacidos, inhibidores de bomba de protones, cambios en estilo de vida",
        "solo_mujeres": False
    },
    "Hernia Hiatal": {
        "sintomas": ["acidez", "regurgitación", "dificultad para tragar", "dolor en el pecho", "eructos", "sensación de llenura", "problemas respiratorios"],
        "factores_riesgo": ["obesidad", "embarazo", "edad avanzada", "tabaquismo", "esfuerzos físicos"],
        "especialidad": "Gastroenterología",
        "urgencia": "Media",
        "recomendaciones": ["Comidas pequeñas", "Evitar acostarse después de comer", "Reducir peso", "Consulta con gastroenterólogo"],
        "tratamiento": "Antiacidos, inhibidores de bomba de protones, cirugía en casos graves",
        "solo_mujeres": False
    },
    "Apendicitis": {
        "sintomas": ["dolor abdominal en cuadrante inferior derecho", "náuseas", "vómitos", "fiebre", "pérdida de apetito", "distensión abdominal"],
        "factores_riesgo": ["obstrucción fecal", "infecciones", "historia familiar", "edad 10-30"],
        "especialidad": "Cirugía General",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR A URGENCIAS INMEDIATAMENTE", "No comer ni beber", "No automedicarse", "Evaluación quirúrgica"],
        "tratamiento": "Apendicectomía, antibióticos",
        "solo_mujeres": False
    },
    "Pancreatitis Aguda": {
        "sintomas": ["dolor abdominal intenso", "náuseas", "vómitos", "fiebre", "distensión abdominal", "ictericia", "taquicardia"],
        "factores_riesgo": ["cálculos biliares", "alcoholismo", "hipertrigliceridemia", "medicamentos", "traumatismos"],
        "especialidad": "Gastroenterología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR A URGENCIAS INMEDIATAMENTE", "Hospitalización", "Ayuno", "No automedicarse"],
        "tratamiento": "Líquidos intravenosos, analgésicos, nutrición parenteral",
        "solo_mujeres": False
    },
    "Pancreatitis Crónica": {
        "sintomas": ["dolor abdominal recurrente", "pérdida de peso", "diarrea", "esteatorrea", "náuseas", "vómitos", "diabetes"],
        "factores_riesgo": ["alcoholismo crónico", "tabaquismo", "historia familiar", "hipercalcemia", "hiperlipidemia"],
        "especialidad": "Gastroenterología",
        "urgencia": "Media",
        "recomendaciones": ["Evitar alcohol", "Dieta baja en grasas", "Suplementos de enzimas", "Consulta con gastroenterólogo"],
        "tratamiento": "Analgésicos, enzimas pancreáticas, insulina",
        "solo_mujeres": False
    },
    "Colecistitis": {
        "sintomas": ["dolor abdominal en cuadrante superior derecho", "náuseas", "vómitos", "fiebre", "ictericia", "fatiga"],
        "factores_riesgo": ["cálculos biliares", "obesidad", "embarazo", "edad avanzada", "sexo femenino"],
        "especialidad": "Cirugía General",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR A URGENCIAS INMEDIATAMENTE", "Dieta baja en grasas", "Antibióticos", "Evaluación quirúrgica"],
        "tratamiento": "Colecistectomía, antibióticos",
        "solo_mujeres": False
    },
    
    # === ENFERMEDADES MUSCULOESQUELÉTICAS (15) ===
    "Artritis Reumatoide": {
        "sintomas": ["dolor articular", "rigidez matutina", "inflamación", "fatiga", "fiebre", "pérdida de peso", "deformidad articular"],
        "factores_riesgo": ["historia familiar", "tabaquismo", "obesidad", "sexo femenino", "edad > 40"],
        "especialidad": "Reumatología",
        "urgencia": "Media",
        "recomendaciones": ["Reposo", "Fisioterapia", "Medicamentos antiinflamatorios", "Consulta con reumatólogo"],
        "tratamiento": "Metotrexato, corticosteroides, anti-TNF",
        "solo_mujeres": False
    },
    "Artrosis (Osteoartritis)": {
        "sintomas": ["dolor articular", "rigidez", "dificultad para moverse", "crujidos", "inflamación leve", "deformidad", "pérdida de flexibilidad"],
        "factores_riesgo": ["edad avanzada", "obesidad", "sobreuso de articulaciones", "lesiones previas", "historia familiar"],
        "especialidad": "Reumatología",
        "urgencia": "Baja",
        "recomendaciones": ["Ejercicio de bajo impacto", "Pérdida de peso", "Fisioterapia", "Consulta con reumatólogo"],
        "tratamiento": "Analgésicos, antiinflamatorios, fisioterapia, cirugía en casos graves",
        "solo_mujeres": False
    },
    "Artritis Psoriásica": {
        "sintomas": ["dolor articular", "inflamación", "enrojecimiento", "lesiones cutáneas", "descamación", "fatiga", "rigidez matutina"],
        "factores_riesgo": ["psoriasis", "historia familiar", "edad 30-50", "tabaquismo", "obesidad"],
        "especialidad": "Reumatología",
        "urgencia": "Media",
        "recomendaciones": ["Consulta con reumatólogo", "Medicamentos antiinflamatorios", "Fisioterapia", "Tratamiento de psoriasis"],
        "tratamiento": "AINE, metotrexato, biológicos",
        "solo_mujeres": False
    },
    "Cervicalgia (Dolor de Cuello)": {
        "sintomas": ["dolor en el cuello", "rigidez", "dolor de cabeza", "dificultad para mover el cuello", "dolor en hombros", "hormigueo en brazos"],
        "factores_riesgo": ["mala postura", "uso excesivo de dispositivos", "estrés", "lesiones", "sobrepeso"],
        "especialidad": "Traumatología",
        "urgencia": "Baja",
        "recomendaciones": ["Aplicar calor local", "Ejercicios de estiramiento", "Mejorar postura", "Consulta si persiste"],
        "tratamiento": "Analgésicos, relajantes musculares, fisioterapia",
        "solo_mujeres": False
    },
    "Lumbalgia (Dolor de Espalda)": {
        "sintomas": ["dolor lumbar", "rigidez", "dificultad para moverse", "dolor al estar de pie", "dolor al sentarse", "irradiación a piernas"],
        "factores_riesgo": ["mala postura", "sedentarismo", "sobrepeso", "levantar objetos pesados", "estrés"],
        "especialidad": "Traumatología",
        "urgencia": "Baja",
        "recomendaciones": ["Aplicar calor o frío", "Reposo", "Ejercicios de fortalecimiento", "Consulta si persiste"],
        "tratamiento": "Analgésicos, relajantes musculares, fisioterapia",
        "solo_mujeres": False
    },
    "Hernia Discal": {
        "sintomas": ["dolor lumbar", "irradiación a piernas", "hormigueo", "debilidad en piernas", "dificultad para moverse", "dolor al estornudar"],
        "factores_riesgo": ["levantar objetos pesados", "sedentarismo", "sobrepeso", "mala postura", "traumatismos"],
        "especialidad": "Traumatología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR AL MÉDICO URGENTEMENTE", "Reposo", "Evitar esfuerzos", "Fisioterapia"],
        "tratamiento": "Analgésicos, antiinflamatorios, fisioterapia, cirugía en casos graves",
        "solo_mujeres": False
    },
    "Espondilitis Anquilosante": {
        "sintomas": ["dolor lumbar crónico", "rigidez", "dificultad para moverse", "fatiga", "dolor en articulaciones", "problemas oculares"],
        "factores_riesgo": ["historia familiar", "sexo masculino", "edad 20-40", "gen HLA-B27"],
        "especialidad": "Reumatología",
        "urgencia": "Media",
        "recomendaciones": ["Fisioterapia", "Ejercicio regular", "Postura adecuada", "Consulta con reumatólogo"],
        "tratamiento": "Antiinflamatorios, biológicos, fisioterapia",
        "solo_mujeres": False
    },
    "Gota": {
        "sintomas": ["dolor articular intenso", "inflamación", "enrojecimiento", "calor en la articulación", "fiebre", "limitación del movimiento"],
        "factores_riesgo": ["alimentos ricos en purinas", "alcohol", "obesidad", "hipertensión", "diabetes", "historia familiar"],
        "especialidad": "Reumatología",
        "urgencia": "Media",
        "recomendaciones": ["Dieta baja en purinas", "Hidratación", "Evitar alcohol", "Consulta con reumatólogo"],
        "tratamiento": "Antiinflamatorios, colchicina, alopurinol",
        "solo_mujeres": False
    },
    "Fibromialgia": {
        "sintomas": ["dolor generalizado", "fatiga", "trastornos del sueño", "rigidez matutina", "dolor de cabeza", "problemas de memoria", "ansiedad"],
        "factores_riesgo": ["estrés", "ansiedad", "depresión", "traumatismos", "historia familiar"],
        "especialidad": "Reumatología",
        "urgencia": "Baja",
        "recomendaciones": ["Ejercicio suave", "Técnicas de relajación", "Terapia cognitivo-conductual", "Consulta con reumatólogo"],
        "tratamiento": "Analgésicos, antidepresivos, pregabalina",
        "solo_mujeres": False
    },
    "Bursitis": {
        "sintomas": ["dolor en la articulación", "inflamación", "enrojecimiento", "calor local", "limitación del movimiento", "sensibilidad al tacto"],
        "factores_riesgo": ["movimientos repetitivos", "posturas forzadas", "traumatismos", "infecciones", "artritis"],
        "especialidad": "Traumatología",
        "urgencia": "Media",
        "recomendaciones": ["Reposo", "Hielo local", "Compresión", "Consulta con traumatólogo"],
        "tratamiento": "Antiinflamatorios, corticosteroides, fisioterapia",
        "solo_mujeres": False
    },
    "Tendinitis": {
        "sintomas": ["dolor en el tendón", "inflamación", "sensibilidad", "limitación del movimiento", "crepitación", "debilidad"],
        "factores_riesgo": ["movimientos repetitivos", "sobreuso", "mala postura", "edad avanzada", "actividades deportivas"],
        "especialidad": "Traumatología",
        "urgencia": "Media",
        "recomendaciones": ["Reposo", "Hielo", "Elevación", "Consulta con traumatólogo"],
        "tratamiento": "Antiinflamatorios, fisioterapia, corticosteroides",
        "solo_mujeres": False
    },
    "Fractura Ósea": {
        "sintomas": ["dolor intenso", "deformidad", "hinchazón", "imposibilidad de mover", "moretones", "sensibilidad al tacto"],
        "factores_riesgo": ["traumatismos", "caídas", "osteoporosis", "actividades deportivas", "accidentes"],
        "especialidad": "Traumatología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR A URGENCIAS INMEDIATAMENTE", "Inmovilización", "No mover el área", "Aplicar hielo"],
        "tratamiento": "Inmovilización, cirugía, rehabilitación",
        "solo_mujeres": False
    },
    "Osteoporosis": {
        "sintomas": ["dolor de espalda", "pérdida de altura", "postura encorvada", "fracturas frecuentes", "dolor óseo"],
        "factores_riesgo": ["edad avanzada", "sexo femenino", "menopausia", "tabaquismo", "alcoholismo", "baja ingesta de calcio"],
        "especialidad": "Reumatología",
        "urgencia": "Media",
        "recomendaciones": ["Suplementos de calcio y vitamina D", "Ejercicio de carga", "Dieta rica en calcio", "Consulta con reumatólogo"],
        "tratamiento": "Bisfosfonatos, terapia hormonal, calcitonina",
        "solo_mujeres": False
    },
    "Escoliosis": {
        "sintomas": ["curvatura de la columna", "dolor de espalda", "hombros desiguales", "cadera prominente", "dificultad para respirar", "fatiga"],
        "factores_riesgo": ["historia familiar", "sexo femenino", "edad adolescente", "enfermedades neuromusculares"],
        "especialidad": "Traumatología",
        "urgencia": "Media",
        "recomendaciones": ["Fisioterapia", "Ejercicios de fortalecimiento", "Consulta con traumatólogo", "Seguimiento regular"],
        "tratamiento": "Fisioterapia, corsé, cirugía en casos graves",
        "solo_mujeres": False
    },
    "Síndrome del Túnel Carpiano": {
        "sintomas": ["hormigueo en mano", "entumecimiento", "dolor en muñeca", "debilidad en mano", "dificultad para agarrar objetos", "dolor nocturno"],
        "factores_riesgo": ["movimientos repetitivos", "embarazo", "diabetes", "obesidad", "hipotiroidismo"],
        "especialidad": "Traumatología",
        "urgencia": "Media",
        "recomendaciones": ["Reposo", "Férula nocturna", "Ejercicios de estiramiento", "Consulta con traumatólogo"],
        "tratamiento": "Antiinflamatorios, corticosteroides, cirugía",
        "solo_mujeres": False
    },
    "Fascitis Plantar": {
        "sintomas": ["dolor en el talón", "dolor al caminar", "rigidez matutina", "sensibilidad en la planta del pie", "dolor al estar de pie"],
        "factores_riesgo": ["sobrepeso", "uso de calzado inadecuado", "actividades deportivas", "trabajo de pie", "pies planos"],
        "especialidad": "Traumatología",
        "urgencia": "Media",
        "recomendaciones": ["Reposo", "Hielo", "Calzado adecuado", "Consulta con traumatólogo"],
        "tratamiento": "Fisioterapia, antiinflamatorios, plantillas",
        "solo_mujeres": False
    },
    
    # === INFECCIONES (15) ===
    "Infección Urinaria": {
        "sintomas": ["dolor al orinar", "micción frecuente", "orina turbia", "olor fuerte en orina", "dolor pélvico", "fiebre", "escalofríos"],
        "factores_riesgo": ["falta de higiene", "relaciones sexuales", "embarazo", "diabetes", "uso de anticonceptivos"],
        "especialidad": "Urología",
        "urgencia": "Media",
        "recomendaciones": ["Aumentar consumo de agua", "Jugo de arándano", "Higiene adecuada", "Consulta con urólogo"],
        "tratamiento": "Antibióticos, analgésicos, aumento de líquidos",
        "solo_mujeres": False
    },
    "Cistitis": {
        "sintomas": ["dolor al orinar", "micción frecuente", "urgencia urinaria", "orina con sangre", "dolor pélvico", "fiebre", "malestar general"],
        "factores_riesgo": ["infecciones recurrentes", "embarazo", "diabetes", "uso de catéteres", "relaciones sexuales"],
        "especialidad": "Urología",
        "urgencia": "Media",
        "recomendaciones": ["Hidratación", "Higiene", "Evitar irritantes", "Consulta con urólogo"],
        "tratamiento": "Antibióticos, analgésicos, aumento de líquidos",
        "solo_mujeres": False
    },
    "Pielonefritis": {
        "sintomas": ["fiebre alta", "escalofríos", "dolor lumbar", "dolor al orinar", "náuseas", "vómitos", "fatiga"],
        "factores_riesgo": ["infección urinaria no tratada", "embarazo", "diabetes", "cálculos renales", "catéteres"],
        "especialidad": "Urología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR AL MÉDICO URGENTEMENTE", "Reposo", "Hidratación", "No automedicarse"],
        "tratamiento": "Antibióticos, antipiréticos, hidratación",
        "solo_mujeres": False
    },
    "Gonorrea": {
        "sintomas": ["secreción uretral", "dolor al orinar", "dolor testicular", "secreción vaginal", "dolor pélvico", "fiebre", "sangrado entre periodos"],
        "factores_riesgo": ["relaciones sexuales sin protección", "múltiples parejas", "contacto sexual", "bajo nivel socioeconómico"],
        "especialidad": "Infectología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR AL MÉDICO URGENTEMENTE", "Tratamiento antibiótico", "Aislamiento", "Pruebas de pareja"],
        "tratamiento": "Antibióticos (ceftriaxona, azitromicina)",
        "solo_mujeres": False
    },
    "Sífilis": {
        "sintomas": ["úlcera genital", "erupción cutánea", "fiebre", "fatiga", "dolor de cabeza", "pérdida de peso", "caída de cabello"],
        "factores_riesgo": ["relaciones sexuales sin protección", "múltiples parejas", "contacto sexual", "historia de enfermedades de transmisión sexual"],
        "especialidad": "Infectología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR AL MÉDICO URGENTEMENTE", "Tratamiento antibiótico", "Pruebas de pareja", "Seguimiento médico"],
        "tratamiento": "Penicilina, antibióticos",
        "solo_mujeres": False
    },
    "VIH/SIDA": {
        "sintomas": ["fiebre", "fatiga", "pérdida de peso", "diarrea", "infecciones recurrentes", "sudoración nocturna", "ganglios inflamados"],
        "factores_riesgo": ["relaciones sexuales sin protección", "compartir agujas", "transfusiones", "transmisión perinatal"],
        "especialidad": "Infectología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR AL MÉDICO URGENTEMENTE", "Tratamiento antirretroviral", "Seguimiento médico", "Prevención"],
        "tratamiento": "Antirretrovirales, manejo de síntomas",
        "solo_mujeres": False
    },
    "Toxoplasmosis": {
        "sintomas": ["fiebre", "fatiga", "dolor de cabeza", "dolor muscular", "ganglios inflamados", "visión borrosa", "confusión"],
        "factores_riesgo": ["contacto con gatos", "carne cruda", "inmunosupresión", "embarazo", "trasplantes"],
        "especialidad": "Infectología",
        "urgencia": "Media",
        "recomendaciones": ["Evitar contacto con gatos", "Cocinar bien la carne", "Higiene", "Consulta con médico"],
        "tratamiento": "Antibióticos, antiparasitarios",
        "solo_mujeres": False
    },
    "Leishmaniasis": {
        "sintomas": ["úlceras cutáneas", "fiebre", "fatiga", "pérdida de peso", "bazo agrandado", "hígado agrandado", "anemia"],
        "factores_riesgo": ["picaduras de insectos", "vida en áreas tropicales", "inmunosupresión", "desnutrición"],
        "especialidad": "Infectología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR AL MÉDICO URGENTEMENTE", "Tratamiento antiparasitario", "Reposo", "Prevención de picaduras"],
        "tratamiento": "Antimoniales, anfotericina B",
        "solo_mujeres": False
    },
    "Malaria": {
        "sintomas": ["fiebre", "escalofríos", "sudoración", "dolor de cabeza", "dolor muscular", "fatiga", "vómitos"],
        "factores_riesgo": ["picaduras de mosquitos", "viajes a zonas endémicas", "inmunosupresión"],
        "especialidad": "Infectología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR A URGENCIAS INMEDIATAMENTE", "Tratamiento antipalúdico", "Reposo", "Prevención de picaduras"],
        "tratamiento": "Antipalúdicos (cloroquina, artemisinina)",
        "solo_mujeres": False
    },
    "Fiebre Amarilla": {
        "sintomas": ["fiebre", "dolor de cabeza", "dolor muscular", "náuseas", "vómitos", "ictericia", "sangrado"],
        "factores_riesgo": ["picaduras de mosquitos", "viajes a zonas endémicas", "no vacunado"],
        "especialidad": "Infectología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR A URGENCIAS INMEDIATAMENTE", "Vacunación", "Reposo", "Prevención de picaduras"],
        "tratamiento": "Sintomático, hidratación, soporte vital",
        "solo_mujeres": False
    },
    "Zika": {
        "sintomas": ["fiebre", "erupción cutánea", "dolor articular", "dolor de cabeza", "dolor muscular", "conjuntivitis", "fatiga"],
        "factores_riesgo": ["picaduras de mosquitos", "viajes a zonas endémicas", "embarazo"],
        "especialidad": "Infectología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR AL MÉDICO URGENTEMENTE", "Reposo", "Hidratación", "Prevención de picaduras"],
        "tratamiento": "Sintomático, hidratación, prevención",
        "solo_mujeres": False
    },
    "Chikungunya": {
        "sintomas": ["fiebre", "dolor articular intenso", "dolor de cabeza", "dolor muscular", "erupción cutánea", "fatiga", "náuseas"],
        "factores_riesgo": ["picaduras de mosquitos", "viajes a zonas endémicas", "inmunosupresión"],
        "especialidad": "Infectología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR AL MÉDICO URGENTEMENTE", "Reposo", "Hidratación", "Analgésicos"],
        "tratamiento": "Analgésicos, antiinflamatorios, hidratación",
        "solo_mujeres": False
    },
    "Tétanos": {
        "sintomas": ["rigidez muscular", "espasmos", "dificultad para tragar", "fiebre", "sudoración", "taquicardia", "hipertensión"],
        "factores_riesgo": ["heridas contaminadas", "falta de vacunación", "mordeduras", "quemaduras"],
        "especialidad": "Infectología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR A URGENCIAS INMEDIATAMENTE", "Antitoxina", "Vacunación", "Cuidado de heridas"],
        "tratamiento": "Antitoxina, antibióticos, soporte vital",
        "solo_mujeres": False
    },
    "Rabia": {
        "sintomas": ["fiebre", "dolor de cabeza", "hidrofobia", "ansiedad", "agitación", "alucinaciones", "parálisis"],
        "factores_riesgo": ["mordeduras de animales", "contacto con animales infectados", "viajes a zonas endémicas"],
        "especialidad": "Infectología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR A URGENCIAS INMEDIATAMENTE", "Vacunación", "Inmunoglobulina", "Cuidado de heridas"],
        "tratamiento": "Vacunación, inmunoglobulina, soporte vital",
        "solo_mujeres": False
    },
    "Fiebre Tifoidea": {
        "sintomas": ["fiebre alta", "dolor de cabeza", "dolor abdominal", "estreñimiento", "diarrea", "erupción cutánea", "fatiga"],
        "factores_riesgo": ["consumo de agua contaminada", "falta de higiene", "viajes a zonas endémicas", "contacto con infectados"],
        "especialidad": "Infectología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR AL MÉDICO URGENTEMENTE", "Reposo", "Hidratación", "Aislamiento"],
        "tratamiento": "Antibióticos, antipiréticos, hidratación",
        "solo_mujeres": False
    },
    "Dengue": {
        "sintomas": ["fiebre alta", "dolor de cabeza", "dolor muscular", "dolor articular", "erupción cutánea", "sangrado", "fatiga"],
        "factores_riesgo": ["picaduras de mosquitos", "vivir en zonas tropicales", "temporada de lluvias"],
        "especialidad": "Infectología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR AL MÉDICO URGENTEMENTE", "Reposo", "Hidratación", "No tomar aspirina"],
        "tratamiento": "Antipiréticos, hidratación, vigilancia médica",
        "solo_mujeres": False
    },
    "Dengue Hemorrágico": {
        "sintomas": ["fiebre", "sangrado", "petequias", "hematomas", "dolor abdominal", "vómitos", "hipotensión"],
        "factores_riesgo": ["dengue previo", "inmunosupresión", "edad avanzada", "enfermedades crónicas"],
        "especialidad": "Infectología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR A URGENCIAS INMEDIATAMENTE", "Hospitalización", "Transfusiones", "Vigilancia intensiva"],
        "tratamiento": "Transfusiones, hidratación, soporte vital",
        "solo_mujeres": False
    },
    "Varicela": {
        "sintomas": ["fiebre", "erupción con ampollas", "picazón", "dolor de cabeza", "fatiga", "pérdida de apetito"],
        "factores_riesgo": ["contacto con infectados", "bajas defensas", "no vacunado"],
        "especialidad": "Dermatología",
        "urgencia": "Media",
        "recomendaciones": ["Reposo", "No rascar", "Baños de avena", "Consulta si fiebre alta"],
        "tratamiento": "Antipiréticos, antihistamínicos, antivirales",
        "solo_mujeres": False
    },
    "Sarampión": {
        "sintomas": ["fiebre alta", "tos", "congestión nasal", "conjuntivitis", "erupción", "dolor de cabeza", "fatiga"],
        "factores_riesgo": ["no vacunado", "contacto con infectados", "bajas defensas"],
        "especialidad": "Infectología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR AL MÉDICO URGENTEMENTE", "Aislamiento", "Hidratación", "Reposo"],
        "tratamiento": "Sintomático, vitaminas, vigilancia médica",
        "solo_mujeres": False
    },
    "Paperas": {
        "sintomas": ["inflamación de parótidas", "fiebre", "dolor al masticar", "dolor de cabeza", "fatiga", "pérdida de apetito"],
        "factores_riesgo": ["no vacunado", "contacto con infectados"],
        "especialidad": "Infectología",
        "urgencia": "Media",
        "recomendaciones": ["Reposo", "Aumentar líquidos", "Compresas frías", "Consulta si complicaciones"],
        "tratamiento": "Analgésicos, antipiréticos, hidratación",
        "solo_mujeres": False
    },
    "Rubéola": {
        "sintomas": ["fiebre", "erupción", "dolor articular", "inflamación de ganglios", "dolor de cabeza", "fatiga", "conjuntivitis"],
        "factores_riesgo": ["no vacunado", "contacto con infectados", "embarazo"],
        "especialidad": "Infectología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR AL MÉDICO URGENTEMENTE", "Aislamiento", "Reposo", "Hidratación"],
        "tratamiento": "Sintomático, prevención en embarazadas",
        "solo_mujeres": False
    },
    
    # === ENFERMEDADES METABÓLICAS Y ENDOCRINAS (10) ===
    "Diabetes Tipo 1": {
        "sintomas": ["sed excesiva", "micción frecuente", "fatiga", "visión borrosa", "hambre extrema", "pérdida de peso", "infecciones frecuentes"],
        "factores_riesgo": ["historia familiar", "enfermedades autoinmunes", "infecciones virales", "edad < 30"],
        "especialidad": "Endocrinología",
        "urgencia": "Alta",
        "recomendaciones": ["Control de glucosa", "Insulina", "Dieta balanceada", "Consulta con endocrinólogo"],
        "tratamiento": "Insulina, monitoreo de glucosa",
        "solo_mujeres": False
    },
    "Diabetes Tipo 2": {
        "sintomas": ["sed excesiva", "micción frecuente", "fatiga", "visión borrosa", "hambre extrema", "pérdida de peso", "infecciones frecuentes"],
        "factores_riesgo": ["sobrepeso", "obesidad", "hipertensión", "historia familiar", "sedentarismo", "edad > 45"],
        "especialidad": "Endocrinología",
        "urgencia": "Media",
        "recomendaciones": ["Control de glucosa", "Dieta balanceada", "Ejercicio regular", "Consulta con endocrinólogo"],
        "tratamiento": "Metformina, insulina, cambios en estilo de vida",
        "solo_mujeres": False
    },
    "Diabetes Gestacional": {
        "sintomas": ["sed excesiva", "micción frecuente", "fatiga", "visión borrosa", "infecciones frecuentes"],
        "factores_riesgo": ["embarazo", "sobrepeso", "historia familiar", "edad > 35", "diabetes gestacional previa"],
        "especialidad": "Endocrinología",
        "urgencia": "Alta",
        "recomendaciones": ["Control de glucosa", "Dieta balanceada", "Ejercicio regular", "Consulta con endocrinólogo"],
        "tratamiento": "Dieta, ejercicio, insulina si es necesario",
        "solo_mujeres": False
    },
    "Hipotiroidismo": {
        "sintomas": ["fatiga", "aumento de peso", "sensibilidad al frío", "piel seca", "caída de cabello", "depresión", "estreñimiento"],
        "factores_riesgo": ["historia familiar", "mujeres > 40", "enfermedad autoinmune", "embarazo", "radiación"],
        "especialidad": "Endocrinología",
        "urgencia": "Media",
        "recomendaciones": ["Control de tiroides", "Dieta balanceada", "Ejercicio regular", "Consulta con endocrinólogo"],
        "tratamiento": "Levotiroxina, cambios en estilo de vida",
        "solo_mujeres": False
    },
    "Hipertiroidismo": {
        "sintomas": ["pérdida de peso", "palpitaciones", "ansiedad", "intolerancia al calor", "sudoración", "fatiga", "temblores"],
        "factores_riesgo": ["historia familiar", "mujeres", "enfermedad autoinmune", "embarazo", "estrés"],
        "especialidad": "Endocrinología",
        "urgencia": "Media",
        "recomendaciones": ["Control de tiroides", "Dieta balanceada", "Técnicas de relajación", "Consulta con endocrinólogo"],
        "tratamiento": "Metimazol, yodo radioactivo, cirugía",
        "solo_mujeres": False
    },
    "Enfermedad de Addison": {
        "sintomas": ["fatiga", "pérdida de peso", "hiperpigmentación", "hipotensión", "hipoglucemia", "náuseas", "vómitos", "dolor abdominal"],
        "factores_riesgo": ["enfermedades autoinmunes", "tuberculosis", "infecciones", "hemorragia adrenal", "medicamentos"],
        "especialidad": "Endocrinología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR AL MÉDICO URGENTEMENTE", "Suplementos hormonales", "Dieta balanceada", "Consulta con endocrinólogo"],
        "tratamiento": "Corticosteroides, hidratación",
        "solo_mujeres": False
    },
    "Síndrome de Cushing": {
        "sintomas": ["aumento de peso", "cara redonda", "obesidad central", "estrías", "hipertensión", "debilidad muscular", "diabetes"],
        "factores_riesgo": ["uso crónico de corticosteroides", "tumores hipofisarios", "tumores suprarrenales", "sexo femenino"],
        "especialidad": "Endocrinología",
        "urgencia": "Alta",
        "recomendaciones": ["Consulta con endocrinólogo", "Reducción de corticosteroides", "Cirugía", "Tratamiento sintomático"],
        "tratamiento": "Cirugía, radioterapia, medicamentos",
        "solo_mujeres": False
    },
    "Hiperlipidemia": {
        "sintomas": ["asintomático", "xantomas", "fatiga", "dolor abdominal", "mareos", "visión borrosa"],
        "factores_riesgo": ["dieta alta en grasas", "sedentarismo", "obesidad", "historia familiar", "diabetes", "hipotiroidismo"],
        "especialidad": "Endocrinología",
        "urgencia": "Media",
        "recomendaciones": ["Dieta saludable", "Ejercicio regular", "Medicamentos", "Consulta con endocrinólogo"],
        "tratamiento": "Estatinas, fibratos, cambios en estilo de vida",
        "solo_mujeres": False
    },
    "Síndrome Metabólico": {
        "sintomas": ["obesidad abdominal", "hipertensión", "hiperglucemia", "hipertrigliceridemia", "colesterol HDL bajo", "fatiga"],
        "factores_riesgo": ["sedentarismo", "dieta alta en calorías", "obesidad", "historia familiar", "edad avanzada"],
        "especialidad": "Endocrinología",
        "urgencia": "Alta",
        "recomendaciones": ["Pérdida de peso", "Ejercicio regular", "Dieta saludable", "Consulta con endocrinólogo"],
        "tratamiento": "Control de peso, medicamentos para diabetes e hipertensión",
        "solo_mujeres": False
    },
    "Obesidad": {
        "sintomas": ["índice de masa corporal > 30", "fatiga", "dificultad para respirar", "dolor articular", "sudoración", "problemas de autoestima"],
        "factores_riesgo": ["dieta alta en calorías", "sedentarismo", "historia familiar", "trastornos hormonales", "medicamentos"],
        "especialidad": "Endocrinología",
        "urgencia": "Media",
        "recomendaciones": ["Dieta balanceada", "Ejercicio regular", "Cambios en estilo de vida", "Consulta con endocrinólogo"],
        "tratamiento": "Dieta, ejercicio, medicamentos, cirugía bariátrica",
        "solo_mujeres": False
    },
    
    # === ENFERMEDADES AUTOINMUNES (5) ===
    "Lupus Eritematoso Sistémico": {
        "sintomas": ["fatiga", "dolor articular", "erupción en la cara", "fiebre", "caída de cabello", "úlceras bucales", "dolor en el pecho"],
        "factores_riesgo": ["sexo femenino", "edad 15-45", "historia familiar", "exposición solar", "infecciones"],
        "especialidad": "Reumatología",
        "urgencia": "Alta",
        "recomendaciones": ["Protección solar", "Reposo", "Medicamentos antiinflamatorios", "Consulta con reumatólogo"],
        "tratamiento": "Corticosteroides, antipalúdicos, inmunosupresores",
        "solo_mujeres": False
    },
    "Anemia": {
        "sintomas": ["fatiga", "debilidad", "palidez", "mareos", "dificultad para respirar", "palpitaciones", "manos y pies fríos"],
        "factores_riesgo": ["deficiencia de hierro", "dieta pobre", "sangrado menstrual", "embarazo", "enfermedades crónicas"],
        "especialidad": "Hematología",
        "urgencia": "Media",
        "recomendaciones": ["Dieta rica en hierro", "Suplementos", "Descanso", "Consulta con hematólogo"],
        "tratamiento": "Suplementos de hierro, vitamina B12, ácido fólico",
        "solo_mujeres": False
    },
    "Anemia Perniciosa": {
        "sintomas": ["fatiga", "debilidad", "palidez", "mareos", "hormigueo", "dificultad para caminar", "depresión", "confusión"],
        "factores_riesgo": ["deficiencia de B12", "gastritis atrófica", "historia familiar", "edad avanzada", "cirugía gástrica"],
        "especialidad": "Hematología",
        "urgencia": "Media",
        "recomendaciones": ["Suplementos de B12", "Dieta balanceada", "Descanso", "Consulta con hematólogo"],
        "tratamiento": "Inyecciones de B12, suplementos orales",
        "solo_mujeres": False
    },
    "Anemia Hemolítica": {
        "sintomas": ["fatiga", "debilidad", "palidez", "ictericia", "orina oscura", "palpitaciones", "dificultad para respirar"],
        "factores_riesgo": ["enfermedades autoinmunes", "infecciones", "medicamentos", "transfusiones", "historia familiar"],
        "especialidad": "Hematología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR AL MÉDICO URGENTEMENTE", "Tratamiento de la causa", "Suplementos", "Consulta con hematólogo"],
        "tratamiento": "Corticosteroides, inmunosupresores, esplenectomía",
        "solo_mujeres": False
    },
    "Anemia Falciforme": {
        "sintomas": ["fatiga", "dolor", "infecciones frecuentes", "ictericia", "retraso en crecimiento", "dificultad para respirar", "dolor óseo"],
        "factores_riesgo": ["historia familiar", "origen africano", "origen mediterráneo", "origen indio"],
        "especialidad": "Hematología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR AL MÉDICO URGENTEMENTE", "Hidratación", "Suplementos", "Consulta con hematólogo"],
        "tratamiento": "Analgésicos, hidroxiurea, transfusiones",
        "solo_mujeres": False
    },
    
    # === ENFERMEDADES DERMATOLÓGICAS (5) ===
    "Dermatitis Atópica": {
        "sintomas": ["picazón", "enrojecimiento", "piel seca", "descamación", "lesiones cutáneas", "inflamación", "sensibilidad"],
        "factores_riesgo": ["historia familiar", "alergias", "asmática", "estrés", "cambios de temperatura"],
        "especialidad": "Dermatología",
        "urgencia": "Baja",
        "recomendaciones": ["Hidratar la piel", "Evitar irritantes", "Ropa de algodón", "Consulta con dermatólogo"],
        "tratamiento": "Cremas hidratantes, corticosteroides tópicos, antihistamínicos",
        "solo_mujeres": False
    },
    "Psoriasis": {
        "sintomas": ["lesiones cutáneas", "descamación", "enrojecimiento", "picazón", "dolor", "inflamación", "uñas deformadas"],
        "factores_riesgo": ["historia familiar", "estrés", "infecciones", "tabaquismo", "obesidad"],
        "especialidad": "Dermatología",
        "urgencia": "Media",
        "recomendaciones": ["Hidratar la piel", "Evitar estrés", "No rascar", "Consulta con dermatólogo"],
        "tratamiento": "Corticosteroides tópicos, fototerapia, medicamentos sistémicos",
        "solo_mujeres": False
    },
    "Acné": {
        "sintomas": ["comedones", "pústulas", "nódulos", "quistes", "enrojecimiento", "cicatrices", "dolor"],
        "factores_riesgo": ["cambios hormonales", "estrés", "dieta alta en azúcares", "cosméticos", "historia familiar"],
        "especialidad": "Dermatología",
        "urgencia": "Baja",
        "recomendaciones": ["Limpieza facial", "Productos no comedogénicos", "Evitar manipular", "Consulta con dermatólogo"],
        "tratamiento": "Peróxido de benzoilo, retinoides, antibióticos",
        "solo_mujeres": False
    },
    "Rosácea": {
        "sintomas": ["enrojecimiento facial", "pústulas", "vasos sanguíneos visibles", "sensación de ardor", "sequedad", "irritación"],
        "factores_riesgo": ["exposición solar", "estrés", "alcohol", "alimentos picantes", "cambios climáticos"],
        "especialidad": "Dermatología",
        "urgencia": "Media",
        "recomendaciones": ["Protección solar", "Evitar factores desencadenantes", "Limpieza suave", "Consulta con dermatólogo"],
        "tratamiento": "Metronidazol, ivermectina, ácido azelaico",
        "solo_mujeres": False
    },
    "Melanoma": {
        "sintomas": ["lesión cutánea", "cambio en lunar", "asimetría", "bordes irregulares", "color variado", "diámetro > 6mm", "sangrado"],
        "factores_riesgo": ["exposición solar", "historia familiar", "piel clara", "lunares atípicos", "edad avanzada"],
        "especialidad": "Dermatología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR AL MÉDICO URGENTEMENTE", "Protección solar", "Autoexamen", "Consulta con dermatólogo"],
        "tratamiento": "Cirugía, quimioterapia, inmunoterapia",
        "solo_mujeres": False
    },
    
    # === ENFERMEDADES OFTALMOLÓGICAS (5) ===
    "Conjuntivitis": {
        "sintomas": ["enrojecimiento ocular", "picazón", "lagrimeo", "secreción", "sensibilidad a la luz", "visión borrosa"],
        "factores_riesgo": ["contacto con infectados", "alergias", "bajas defensas", "uso de lentes de contacto"],
        "especialidad": "Oftalmología",
        "urgencia": "Media",
        "recomendaciones": ["Lavado de manos frecuente", "No compartir toallas", "No usar lentes de contacto", "Consulta con oftalmólogo"],
        "tratamiento": "Gotas antibióticas, antihistamínicas, compresas frías",
        "solo_mujeres": False
    },
    "Glaucoma": {
        "sintomas": ["visión borrosa", "dolor ocular", "náuseas", "vómitos", "halos alrededor de luces", "pérdida de visión periférica"],
        "factores_riesgo": ["edad avanzada", "historia familiar", "hipertensión", "diabetes", "miopía"],
        "especialidad": "Oftalmología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR AL MÉDICO URGENTEMENTE", "Examen ocular regular", "Medicamentos", "Consulta con oftalmólogo"],
        "tratamiento": "Gotas hipotensoras, láser, cirugía",
        "solo_mujeres": False
    },
    "Cataratas": {
        "sintomas": ["visión borrosa", "visión nublada", "sensibilidad a la luz", "visión doble", "dificultad para ver de noche", "colores desvanecidos"],
        "factores_riesgo": ["edad avanzada", "diabetes", "tabaquismo", "exposición solar", "traumatismos oculares"],
        "especialidad": "Oftalmología",
        "urgencia": "Media",
        "recomendaciones": ["Examen ocular regular", "Protección solar", "Dieta rica en antioxidantes", "Consulta con oftalmólogo"],
        "tratamiento": "Cirugía de catarata, lentes intraoculares",
        "solo_mujeres": False
    },
    "Degeneración Macular": {
        "sintomas": ["visión central borrosa", "pérdida de visión central", "dificultad para leer", "visión distorsionada", "manchas oscuras"],
        "factores_riesgo": ["edad avanzada", "historia familiar", "tabaquismo", "hipertensión", "obesidad"],
        "especialidad": "Oftalmología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR AL MÉDICO URGENTEMENTE", "Suplementos vitamínicos", "Dieta saludable", "Consulta con oftalmólogo"],
        "tratamiento": "Inyecciones intraoculares, fototerapia",
        "solo_mujeres": False
    },
    "Retinopatía Diabética": {
        "sintomas": ["visión borrosa", "manchas flotantes", "dificultad para ver de noche", "pérdida de visión", "visión distorsionada"],
        "factores_riesgo": ["diabetes", "control glucémico deficiente", "hipertensión", "embarazo", "duración de diabetes"],
        "especialidad": "Oftalmología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR AL MÉDICO URGENTEMENTE", "Control de glucosa", "Examen ocular regular", "Consulta con oftalmólogo"],
        "tratamiento": "Láser, inyecciones, control metabólico",
        "solo_mujeres": False
    },
    
    # === ENFERMEDADES GINECOLÓGICAS (SOLO MUJERES - 5) ===
    "Infección Vaginal": {
        "sintomas": ["picazón", "secreción anormal", "olor", "dolor", "ardor", "enrojecimiento", "inflamación"],
        "factores_riesgo": ["antibióticos", "diabetes", "embarazo", "anticonceptivos", "relaciones sexuales"],
        "especialidad": "Ginecología",
        "urgencia": "Media",
        "recomendaciones": ["Higiene adecuada", "Ropa interior de algodón", "Evitar irritantes", "Consulta con ginecólogo"],
        "tratamiento": "Antifúngicos, antibióticos, cremas tópicas",
        "solo_mujeres": True
    },
    "Vaginosis Bacteriana": {
        "sintomas": ["secreción grisácea", "olor a pescado", "picazón", "ardor", "dolor", "irritación"],
        "factores_riesgo": ["relaciones sexuales", "duchas vaginales", "antibióticos", "embarazo", "diabetes"],
        "especialidad": "Ginecología",
        "urgencia": "Media",
        "recomendaciones": ["Higiene adecuada", "Evitar duchas vaginales", "Ropa interior de algodón", "Consulta con ginecólogo"],
        "tratamiento": "Antibióticos tópicos u orales",
        "solo_mujeres": True
    },
    "Candidiasis Vaginal": {
        "sintomas": ["picazón intensa", "secreción blanca", "ardor", "enrojecimiento", "inflamación", "dolor al orinar"],
        "factores_riesgo": ["antibióticos", "diabetes", "embarazo", "anticonceptivos", "sistema inmunológico débil"],
        "especialidad": "Ginecología",
        "urgencia": "Media",
        "recomendaciones": ["Higiene adecuada", "Ropa interior de algodón", "Evitar azúcares", "Consulta con ginecólogo"],
        "tratamiento": "Antifúngicos tópicos u orales",
        "solo_mujeres": True
    },
    "Endometriosis": {
        "sintomas": ["dolor pélvico", "dolor menstrual intenso", "dolor al orinar", "dolor al defecar", "dolor durante relaciones", "infertilidad"],
        "factores_riesgo": ["historia familiar", "ciclos menstruales cortos", "menarquia temprana", "nuliparidad", "edad 25-40"],
        "especialidad": "Ginecología",
        "urgencia": "Alta",
        "recomendaciones": ["Consulta con ginecólogo", "Tratamiento hormonal", "Cirugía", "Manejo del dolor"],
        "tratamiento": "Anticonceptivos, agonistas GnRH, cirugía",
        "solo_mujeres": True
    },
    "Síndrome de Ovario Poliquístico": {
        "sintomas": ["ciclos menstruales irregulares", "hirsutismo", "acné", "aumento de peso", "infertilidad", "insulinorresistencia"],
        "factores_riesgo": ["historia familiar", "obesidad", "sedentarismo", "diabetes", "edad 15-30"],
        "especialidad": "Ginecología",
        "urgencia": "Media",
        "recomendaciones": ["Consulta con ginecólogo", "Pérdida de peso", "Tratamiento hormonal", "Dieta balanceada"],
        "tratamiento": "Anticonceptivos, metformina, cambios en estilo de vida",
        "solo_mujeres": True
    },
    
    # === ENFERMEDADES RENALES (5) ===
    "Insuficiencia Renal Aguda": {
        "sintomas": ["disminución de la orina", "fatiga", "náuseas", "vómitos", "edema", "confusión", "dificultad para respirar"],
        "factores_riesgo": ["deshidratación", "infecciones", "medicamentos", "traumatismos", "cirugía"],
        "especialidad": "Nefrología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR A URGENCIAS INMEDIATAMENTE", "Hidratación", "Medicamentos", "Consulta con nefrólogo"],
        "tratamiento": "Hidratación, diuréticos, diálisis",
        "solo_mujeres": False
    },
    "Insuficiencia Renal Crónica": {
        "sintomas": ["fatiga", "pérdida de apetito", "náuseas", "vómitos", "edema", "hipertensión", "anemia", "prurito"],
        "factores_riesgo": ["diabetes", "hipertensión", "glomerulonefritis", "enfermedad renal poliquística", "edad avanzada"],
        "especialidad": "Nefrología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR AL MÉDICO URGENTEMENTE", "Control de factores de riesgo", "Dieta baja en proteínas", "Consulta con nefrólogo"],
        "tratamiento": "Control de presión arterial, diálisis, trasplante",
        "solo_mujeres": False
    },
    "Glomerulonefritis": {
        "sintomas": ["hematuria", "proteinuria", "edema", "hipertensión", "fatiga", "disminución de la orina"],
        "factores_riesgo": ["infecciones", "enfermedades autoinmunes", "medicamentos", "historia familiar"],
        "especialidad": "Nefrología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR AL MÉDICO URGENTEMENTE", "Control de presión arterial", "Inmunosupresores", "Consulta con nefrólogo"],
        "tratamiento": "Corticosteroides, inmunosupresores, diuréticos",
        "solo_mujeres": False
    },
    "Cálculos Renales": {
        "sintomas": ["dolor lumbar intenso", "dolor abdominal", "náuseas", "vómitos", "hematuria", "dificultad para orinar", "fiebre"],
        "factores_riesgo": ["deshidratación", "dieta rica en oxalato", "hipercalciuria", "infecciones", "historia familiar"],
        "especialidad": "Urología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR AL MÉDICO URGENTEMENTE", "Hidratación", "Analgésicos", "Consulta con urólogo"],
        "tratamiento": "Analgésicos, litotricia, cirugía",
        "solo_mujeres": False
    },
    "Enfermedad Renal Poliquística": {
        "sintomas": ["dolor lumbar", "hematuria", "hipertensión", "infecciones urinarias", "cálculos renales", "insuficiencia renal"],
        "factores_riesgo": ["historia familiar", "mutaciones genéticas", "edad avanzada"],
        "especialidad": "Nefrología",
        "urgencia": "Alta",
        "recomendaciones": ["ACUDIR AL MÉDICO URGENTEMENTE", "Control de presión arterial", "Dieta baja en sal", "Consulta con nefrólogo"],
        "tratamiento": "Control de presión arterial, diuréticos, diálisis, trasplante",
        "solo_mujeres": False
    }
}

# ============================================
# LISTA COMPLETA DE SÍNTOMAS
# ============================================
SINTOMAS_COMPLETOS = [
    "Dolor de cabeza", "Dolor de garganta", "Fiebre", "Tos", "Dolor abdominal",
    "Dolor de espalda", "Náuseas", "Mareos", "Dificultad para respirar",
    "Dolor en el pecho", "Erupción cutánea", "Fatiga", "Sed excesiva",
    "Micción frecuente", "Visión borrosa", "Hambre extrema", "Pérdida de peso",
    "Infecciones frecuentes", "Dolor articular", "Rigidez matutina",
    "Inflamación", "Temblores", "Rigidez muscular", "Bradicinesia",
    "Inestabilidad postural", "Pérdida de memoria", "Confusión",
    "Cambios de humor", "Desorientación", "Palpitaciones", "Sangrado nasal",
    "Congestión nasal", "Estornudos", "Diarrea", "Vómitos",
    "Dolor al orinar", "Orina turbia", "Dolor pélvico", "Zumbido en oídos",
    "Dificultad para concentrarse", "Pérdida de apetito", "Desmayos",
    "Palidez", "Sibilancias", "Producción de moco", "Sensibilidad a la luz",
    "Sensibilidad al sonido", "Aura visual", "Quemazón", "Hormigueo",
    "Entumecimiento", "Debilidad muscular", "Crujidos articulares",
    "Dolor en la nuca", "Dolor en hombros", "Dificultad para mover",
    "Dolor lumbar", "Irradiación a piernas", "Dolor al estar de pie",
    "Dolor al sentarse", "Escalofríos", "Ictericia", "Orina oscura",
    "Inflamación de parótidas", "Dolor al masticar", "Ampollas", "Picazón",
    "Conjuntivitis", "Dolor muscular", "Adormecimiento del labio",
    "Tic nervioso en el ojo", "Parpadeo excesivo", "Contracciones faciales",
    "Movimientos involuntarios", "Debilidad en un lado del cuerpo",
    "Dificultad para hablar", "Pérdida de equilibrio", "Caída de un lado de la cara",
    "Dificultad para sonreír", "Babeo", "Dificultad para cerrar el ojo",
    "Sensación de presión en la cabeza", "Dolor en la mandíbula",
    "Sudoración", "Ansiedad", "Sensación de llenura", "Ardor estomacal",
    "Eructos", "Sangre en heces", "Vómitos con sangre", "Aumento de peso",
    "Sensibilidad al frío", "Piel seca", "Caída de cabello", "Depresión",
    "Estreñimiento", "Intolerancia al calor", "Enrojecimiento", "Descamación",
    "Lesiones cutáneas", "Sensibilidad", "Enrojecimiento ocular", "Lagrimeo",
    "Secreción ocular", "Secreción anormal", "Olor vaginal", "Ardor vaginal",
    "Secreción grisácea", "Secreción blanca", "Visión nublada",
    "Halos alrededor de luces", "Pérdida de visión periférica",
    "Manchas flotantes", "Distorsión visual", "Visión doble",
    "Dificultad para tragar", "Regurgitación", "Ronquera",
    "Distensión abdominal", "Esteatorrea", "Hipoglucemia",
    "Hiperpigmentación", "Xantomas", "Cara redonda", "Estrías",
    "Obesidad abdominal", "Úlceras", "Sangrado", "Hemoptisis",
    "Sudoración nocturna", "Ganglios inflamados", "Dolor testicular",
    "Sangrado entre periodos", "Dolor al defecar", "Hirsutismo",
    "Infertilidad", "Dolor durante relaciones", "Rigidez de cuello",
    "Convulsiones", "Mirada fija", "Dolor quemante", "Pérdida de sensibilidad",
    "Ulceras en pies", "Caída de párpados", "Exoftalmos", "Ronchas",
    "Pústulas", "Quistes", "Nódulos", "Vesículas", "Edema", "Hematuria",
    "Proteinuria", "Hipoalbuminemia", "Hiperlipidemia", "Poliuria",
    "Polidipsia", "Prurito", "Petequias", "Hematomas"
]

# ============================================
# DIRECTORIO DE SALUD
# ============================================
DIRECTORIO_SALUD = [
    {
        "nombre": "Hospital General de Santa Teresa",
        "tipo": "Hospital",
        "direccion": "Av. Principal, Santa Teresa del Tuy, Estado Miranda",
        "telefono": "0212-XXX-XXXX",
        "servicios": ["Emergencias 24h", "Consulta Externa", "Hospitalización", "Cirugía", "Maternidad"],
        "horario": "24 horas",
        "coordenadas": "10.2305° N, 66.6647° W"
    },
    {
        "nombre": "Ambulatorio Urbano I",
        "tipo": "Ambulatorio",
        "direccion": "Barrio El Centro, Santa Teresa del Tuy, Estado Miranda",
        "telefono": "0212-XXX-XXXX",
        "servicios": ["Medicina General", "Pediatría", "Odontología", "Vacunación", "Control de embarazo"],
        "horario": "7:00 AM - 3:00 PM",
        "coordenadas": "10.2280° N, 66.6620° W"
    },
    {
        "nombre": "Ambulatorio Urbano II",
        "tipo": "Ambulatorio",
        "direccion": "Sector La Trinidad, Santa Teresa del Tuy, Estado Miranda",
        "telefono": "0212-XXX-XXXX",
        "servicios": ["Medicina General", "Pediatría", "Odontología", "Vacunación"],
        "horario": "7:00 AM - 3:00 PM",
        "coordenadas": "10.2320° N, 66.6670° W"
    },
    {
        "nombre": "CDI (Centro de Diagnóstico Integral)",
        "tipo": "Centro de Diagnóstico",
        "direccion": "Av. Principal, Santa Teresa del Tuy, Estado Miranda",
        "telefono": "0212-XXX-XXXX",
        "servicios": ["Laboratorio", "Rayos X", "Ecografía", "Electrocardiograma", "Consulta Especializada"],
        "horario": "7:00 AM - 5:00 PM",
        "coordenadas": "10.2310° N, 66.6635° W"
    },
    {
        "nombre": "Farmacia Santa Teresa 24h",
        "tipo": "Farmacia",
        "direccion": "Esquina Bolívar, Santa Teresa del Tuy, Estado Miranda",
        "telefono": "0212-XXX-XXXX",
        "servicios": ["Venta de medicamentos", "Delivery 24h", "Productos de cuidado personal"],
        "horario": "24 horas",
        "coordenadas": "10.2295° N, 66.6650° W"
    },
    {
        "nombre": "Farmacia La Trinidad",
        "tipo": "Farmacia",
        "direccion": "Sector La Trinidad, Santa Teresa del Tuy, Estado Miranda",
        "telefono": "0212-XXX-XXXX",
        "servicios": ["Venta de medicamentos", "Productos naturales", "Cuidado personal"],
        "horario": "8:00 AM - 8:00 PM",
        "coordenadas": "10.2325° N, 66.6665° W"
    },
    {
        "nombre": "Clínica Santa Teresa",
        "tipo": "Clínica Privada",
        "direccion": "Calle 5, Santa Teresa del Tuy, Estado Miranda",
        "telefono": "0212-XXX-XXXX",
        "servicios": ["Consultas Especializadas", "Laboratorio", "Imagenología", "Medicina Interna"],
        "horario": "8:00 AM - 6:00 PM",
        "coordenadas": "10.2300° N, 66.6625° W"
    },
    {
        "nombre": "Módulo de Barrio Adentro",
        "tipo": "Módulo de Salud",
        "direccion": "Urbanización El Samán, Santa Teresa del Tuy, Estado Miranda",
        "telefono": "0212-XXX-XXXX",
        "servicios": ["Medicina General", "Odontología", "Vacunación", "Control de embarazo"],
        "horario": "8:00 AM - 4:00 PM",
        "coordenadas": "10.2340° N, 66.6680° W"
    },
    {
        "nombre": "Farmacia El Samán",
        "tipo": "Farmacia",
        "direccion": "Urbanización El Samán, Santa Teresa del Tuy, Estado Miranda",
        "telefono": "0212-XXX-XXXX",
        "servicios": ["Venta de medicamentos", "Productos de cuidado personal"],
        "horario": "8:00 AM - 7:00 PM",
        "coordenadas": "10.2345° N, 66.6675° W"
    },
    {
        "nombre": "Clínica Odontológica Santa Teresa",
        "tipo": "Clínica Odontológica",
        "direccion": "Av. Principal, Santa Teresa del Tuy, Estado Miranda",
        "telefono": "0212-XXX-XXXX",
        "servicios": ["Odontología General", "Ortodoncia", "Blanqueamiento", "Cirugía Dental"],
        "horario": "8:00 AM - 5:00 PM",
        "coordenadas": "10.2290° N, 66.6640° W"
    }
]

# ============================================
# FUNCIÓN DE CHATBOT PARA PREGUNTA AL DOCTOR
# ============================================
def responder_pregunta_medica(pregunta):
    pregunta_lower = pregunta.lower()
    
    if any(word in pregunta_lower for word in ["dolor de cabeza", "migraña", "cefalea"]):
        return """
        **Posible diagnóstico:** Cefalea o Migraña
        
        **Recomendación:**
        - Descansa en un lugar tranquilo y oscuro
        - Aplica compresas frías en la frente
        - Mantente hidratado
        - Si el dolor es intenso o recurrente, consulta a un neurólogo
        
        ⚠️ **Recuerda:** Esta es solo una guía informativa.
        """
    elif any(word in pregunta_lower for word in ["dolor de garganta", "garganta"]):
        return """
        **Posible diagnóstico:** Faringitis o Amigdalitis
        
        **Recomendación:**
        - Haz gárgaras con agua tibia y sal
        - Bebe líquidos calientes
        - Descansa la voz
        - Si hay fiebre o dura más de 3 días, consulta a un médico
        
        ⚠️ **Recuerda:** Esta es solo una guía informativa.
        """
    elif any(word in pregunta_lower for word in ["fiebre", "temperatura"]):
        return """
        **Posible diagnóstico:** Infección viral o bacteriana
        
        **Recomendación:**
        - Reposo absoluto
        - Bebe abundantes líquidos
        - Toma paracetamol para bajar la fiebre
        - Si la fiebre supera los 38.5°C o dura más de 3 días, consulta a un médico
        
        ⚠️ **Recuerda:** Esta es solo una guía informativa.
        """
    elif any(word in pregunta_lower for word in ["dolor en el pecho", "pecho"]):
        return """
        ⚠️ **ATENCIÓN URGENTE**
        
        **Posible diagnóstico:** Problema cardíaco
        
        **Recomendación:**
        - **ACUDE A URGENCIAS INMEDIATAMENTE O LLAMA AL 911**
        - Reposo absoluto
        - No te automediques
        
        ⚠️ **Recuerda:** ACUDE AL MÉDICO URGENTEMENTE.
        """
    elif any(word in pregunta_lower for word in ["dificultad para respirar", "respirar"]):
        return """
        ⚠️ **ATENCIÓN URGENTE**
        
        **Posible diagnóstico:** Problema respiratorio
        
        **Recomendación:**
        - **ACUDE A URGENCIAS INMEDIATAMENTE O LLAMA AL 911**
        - Siéntate en posición recta
        - Mantén la calma
        
        ⚠️ **Recuerda:** ACUDE AL MÉDICO URGENTEMENTE.
        """
    else:
        return """
        **Análisis preliminar:**
        
        Consulta a un médico para una evaluación completa.
        
        ⚠️ **Recuerda:** Esta es solo una guía informativa.
        """

# ============================================

# FUNCIÓN DE DIAGNÓSTICO
# ============================================
def diagnosticar_enfermedades(sintomas_usuario, condiciones_preexistentes, edad, sexo):
    diagnosticos = []
    
    sintomas_normalizados = []
    for s in sintomas_usuario:
        s_lower = s.lower().strip()
        s_lower = s_lower.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
        sintomas_normalizados.append(s_lower)
    
    for nombre, info in BASE_DATOS_ENFERMEDADES.items():
        if info.get("solo_mujeres", False) and sexo != "Femenino":
            continue
        
        sintomas_coincidentes = []
        factores_riesgo = []
        total_sintomas = len(info["sintomas"])
        
        for sintoma in info["sintomas"]:
            s_lower = sintoma.lower().replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
            if any(s_lower in s_usuario or s_usuario in s_lower for s_usuario in sintomas_normalizados):
                sintomas_coincidentes.append(sintoma)
        
        for factor in info["factores_riesgo"]:
            factor_lower = factor.lower().replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
            for condicion in condiciones_preexistentes:
                cond_lower = condicion.lower().replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u')
                if factor_lower in cond_lower or cond_lower in factor_lower:
                    factores_riesgo.append(factor)
        
        if len(sintomas_coincidentes) >= 2:
            if len(sintomas_coincidentes) >= total_sintomas * 0.6:
                nivel = "Alta"
                color = "#4CAF50"
            elif len(sintomas_coincidentes) >= total_sintomas * 0.3:
                nivel = "Media"
                color = "#FFC107"
            else:
                nivel = "Baja"
                color = "#FF6B6B"
            
            diagnosticos.append({
                "enfermedad": nombre,
                "nivel": nivel,
                "color": color,
                "sintomas_coincidentes": sintomas_coincidentes,
                "factores_riesgo": factores_riesgo,
                "especialidad": info["especialidad"],
                "urgencia": info["urgencia"],
                "recomendaciones": info["recomendaciones"],
                "tratamiento": info["tratamiento"],
                "total_sintomas": total_sintomas
            })
    
    orden_nivel = {"Alta": 0, "Media": 1, "Baja": 2}
    diagnosticos.sort(key=lambda x: (orden_nivel[x["nivel"]], -len(x["sintomas_coincidentes"])))
    
    return diagnosticos[:8]

# ============================================
# FUNCIONES DE ADMINISTRACIÓN DE ENFERMEDADES
# ============================================
def guardar_enfermedad_en_supabase(nombre, info):
    try:
        data = {
            "nombre": nombre,
            "sintomas": info["sintomas"],
            "factores_riesgo": info.get("factores_riesgo", []),
            "especialidad": info["especialidad"],
            "urgencia": info.get("urgencia", "Media"),
            "recomendaciones": info.get("recomendaciones", []),
            "tratamiento": info["tratamiento"],
            "solo_mujeres": info.get("solo_mujeres", False)
        }
        existing = supabase.table("enfermedades").select("*").eq("nombre", nombre).execute()
        if existing.data:
            supabase.table("enfermedades").update(data).eq("nombre", nombre).execute()
        else:
            supabase.table("enfermedades").insert(data).execute()
        return True
    except Exception as e:
        print(f"Error guardando enfermedad: {e}")
        return False

def cargar_enfermedades_de_supabase():
    try:
        response = supabase.table("enfermedades").select("*").execute()
        if response.data:
            for item in response.data:
                nombre = item.pop("nombre")
                BASE_DATOS_ENFERMEDADES[nombre] = item
        return True
    except Exception as e:
        print(f"Error cargando enfermedades: {e}")
        return False

def eliminar_enfermedad_de_supabase(nombre):
    try:
        supabase.table("enfermedades").delete().eq("nombre", nombre).execute()
        if nombre in BASE_DATOS_ENFERMEDADES:
            del BASE_DATOS_ENFERMEDADES[nombre]
        return True
    except Exception as e:
        print(f"Error eliminando enfermedad: {e}")
        return False

# ============================================
# FUNCIONES DE ME GUSTA
# ============================================
def agregar_like_usuario(usuario_id):
    try:
        existing = supabase.table("likes").select("*").eq("usuario_id", usuario_id).eq("es_automatico", False).execute()
        if existing.data:
            return False, "Ya apoyaste esta página anteriormente"
        else:
            data = {
                "usuario_id": usuario_id,
                "fecha": datetime.now(pytz.UTC).isoformat(),
                "activo": True,
                "es_automatico": False
            }
            result = supabase.table("likes").insert(data).execute()
            return True if result.data else False, "Gracias por tu apoyo"
    except Exception as e:
        return False, str(e)

def agregar_likes_automaticos():
    try:
        response = supabase.table("likes").select("usuario_id").eq("es_automatico", True).order("id", desc=True).limit(1).execute()
        if response.data:
            last_id = response.data[0]["usuario_id"]
            match = re.search(r'auto_(\d+)', last_id)
            if match:
                lote = int(match.group(1)) + 1
            else:
                lote = 1
        else:
            lote = 1
        for i in range(2):
            data = {
                "usuario_id": f"auto_{lote}_{i}",
                "fecha": datetime.now(pytz.UTC).isoformat(),
                "activo": True,
                "es_automatico": True
            }
            supabase.table("likes").insert(data).execute()
        return 2
    except Exception as e:
        print(f"Error agregando likes automáticos: {e}")
        return 0

def obtener_total_likes():
    try:
        response = supabase.table("likes").select("*", count="exact").eq("activo", True).execute()
        return response.count if response.count else 0
    except Exception:
        return 0

def obtener_likes_reales():
    try:
        response = supabase.table("likes").select("*", count="exact").eq("activo", True).eq("es_automatico", False).execute()
        return response.count if response.count else 0
    except Exception:
        return 0

def obtener_likes_automaticos():
    try:
        response = supabase.table("likes").select("*", count="exact").eq("activo", True).eq("es_automatico", True).execute()
        return response.count if response.count else 0
    except Exception:
        return 0

def ya_dio_like(usuario_id):
    try:
        response = supabase.table("likes").select("*").eq("usuario_id", usuario_id).eq("es_automatico", False).execute()
        return len(response.data) > 0
    except Exception:
        return False

# ============================================
# FUNCIONES DE VISITAS
# ============================================
def actualizar_visitas():
    try:
        response = supabase.table("visitas").select("conteo").eq("id", 1).execute()
        if response.data:
            conteo_actual = response.data[0]["conteo"]
            nuevo_conteo = conteo_actual + 1
            visitas_procesadas = nuevo_conteo // 20
            visitas_anteriores_procesadas = conteo_actual // 20
            if visitas_procesadas > visitas_anteriores_procesadas:
                likes_agregados = agregar_likes_automaticos()
                if likes_agregados > 0:
                    st.session_state.likes_automaticos_agregados = likes_agregados
            supabase.table("visitas").update({"conteo": nuevo_conteo}).eq("id", 1).execute()
        else:
            supabase.table("visitas").insert({"id": 1, "conteo": 2500}).execute()
    except Exception:
        pass

def get_visitas():
    try:
        response = supabase.table("visitas").select("conteo").eq("id", 1).execute()
        if response.data:
            return int(response.data[0]["conteo"])
        return 2500
    except Exception:
        return 2500

# ============================================
# FUNCIONES DE COMENTARIOS
# ============================================
def get_fecha_hora_venezuela():
    caracas_tz = pytz.timezone('America/Caracas')
    return datetime.now(pytz.UTC).astimezone(caracas_tz)

def agregar_comentario(seccion, item_id, usuario, comentario):
    try:
        ahora = get_fecha_hora_venezuela()
        data = {
            "seccion": seccion,
            "item_id": str(item_id),
            "usuario": usuario if usuario else "Anónimo",
            "comentario": comentario,
            "fecha": ahora.strftime("%d/%m/%Y %H:%M"),
            "aprobado": True
        }
        result = supabase.table("comentarios").insert(data).execute()
        return True if result.data else False
    except Exception as e:
        st.error(f"Error al agregar comentario: {str(e)}")
        return False

def obtener_comentarios(seccion, item_id):
    try:
        response = supabase.table("comentarios").select("*").eq("seccion", seccion).eq("item_id", str(item_id)).eq("aprobado", True).order("id", desc=True).execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def obtener_comentarios_todos(seccion=None):
    try:
        if seccion:
            response = supabase.table("comentarios").select("*").eq("seccion", seccion).order("id", desc=True).execute()
        else:
            response = supabase.table("comentarios").select("*").order("id", desc=True).execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def eliminar_comentario(id_):
    try:
        result = supabase.table("comentarios").delete().eq("id", id_).execute()
        return True
    except Exception as e:
        print(f"Error eliminando comentario: {e}")
        return False

def actualizar_comentario(id_, nuevo_comentario):
    try:
        result = supabase.table("comentarios").update({"comentario": nuevo_comentario}).eq("id", id_).execute()
        return True
    except Exception as e:
        print(f"Error actualizando comentario: {e}")
        return False

def mostrar_seccion_comentarios(seccion, item_id, titulo_item, es_admin=False):
    st.markdown("---")
    st.markdown("### 💬 Comentarios y Opiniones")
    with st.form(key=f"comentario_form_{seccion}_{item_id}"):
        col_nom, col_com = st.columns([1, 3])
        with col_nom:
            nombre_com = st.text_input("Tu nombre", placeholder="Anónimo", key=f"nombre_{seccion}_{item_id}")
        with col_com:
            comentario_text = st.text_area("Escribe tu comentario u opinión", placeholder="Comparte tu opinión sobre este contenido...", key=f"comentario_{seccion}_{item_id}")
        if st.form_submit_button("📝 Enviar comentario"):
            if comentario_text and comentario_text.strip():
                if agregar_comentario(seccion, item_id, nombre_com if nombre_com else "Anónimo", comentario_text):
                    st.success("✅ ¡Comentario enviado correctamente!")
                    st.rerun()
                else:
                    st.error("❌ Error al enviar comentario")
            else:
                st.error("❌ Escribe un comentario antes de enviar")
    comentarios = obtener_comentarios(seccion, item_id)
    if not comentarios.empty:
        st.markdown(f"#### 📌 {len(comentarios)} comentarios")
        for idx, com in comentarios.iterrows():
            with st.container():
                col1, col2 = st.columns([8, 2])
                with col1:
                    st.markdown(f"**👤 {com['usuario']}** *{com['fecha']}*")
                    st.markdown(f"💬 {com['comentario']}")
                with col2:
                    if es_admin:
                        if st.button(f"🛠️", key=f"admin_com_{com['id']}_{seccion}_{item_id}_{idx}", help="Gestionar comentario (solo admin)"):
                            st.session_state.edit_comentario_id = com['id']
                            st.session_state.edit_comentario_text = com['comentario']
                            st.session_state.edit_comentario_seccion = seccion
                            st.session_state.edit_comentario_item = item_id
                            st.rerun()
                st.divider()
    if st.session_state.get('edit_comentario_id') and st.session_state.edit_comentario_id:
        edit_id = st.session_state.edit_comentario_id
        if st.session_state.get('edit_comentario_seccion') == seccion and st.session_state.get('edit_comentario_item') == item_id:
            st.markdown("### ✏️ Editar comentario")
            with st.form(key=f"edit_com_form_{edit_id}_{seccion}_{item_id}"):
                nuevo_texto = st.text_area("Nuevo texto del comentario", value=st.session_state.edit_comentario_text)
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    if st.form_submit_button("💾 Guardar cambios"):
                        if actualizar_comentario(edit_id, nuevo_texto):
                            st.success("✅ Comentario actualizado")
                            del st.session_state.edit_comentario_id
                            if 'edit_comentario_text' in st.session_state:
                                del st.session_state.edit_comentario_text
                            if 'edit_comentario_seccion' in st.session_state:
                                del st.session_state.edit_comentario_seccion
                            if 'edit_comentario_item' in st.session_state:
                                del st.session_state.edit_comentario_item
                            st.rerun()
                with col2:
                    if st.form_submit_button("🗑️ Eliminar"):
                        if eliminar_comentario(edit_id):
                            st.success("✅ Comentario eliminado")
                            del st.session_state.edit_comentario_id
                            if 'edit_comentario_text' in st.session_state:
                                del st.session_state.edit_comentario_text
                            if 'edit_comentario_seccion' in st.session_state:
                                del st.session_state.edit_comentario_seccion
                            if 'edit_comentario_item' in st.session_state:
                                del st.session_state.edit_comentario_item
                            st.rerun()
                with col3:
                    if st.form_submit_button("❌ Cancelar"):
                        del st.session_state.edit_comentario_id
                        if 'edit_comentario_text' in st.session_state:
                            del st.session_state.edit_comentario_text
                        if 'edit_comentario_seccion' in st.session_state:
                            del st.session_state.edit_comentario_seccion
                        if 'edit_comentario_item' in st.session_state:
                            del st.session_state.edit_comentario_item
                        st.rerun()

# ============================================
# FUNCIONES DE OPTIMIZACIÓN DE IMÁGENES
# ============================================
def optimizar_imagen(file, max_width=1024, quality=75):
    try:
        if file is None: return None
        img = Image.open(file)
        if img.mode in ("RGBA", "P"): img = img.convert("RGB")
        if img.width > max_width:
            ratio = max_width / img.width
            img = img.resize((max_width, int(img.height * ratio)), Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality, optimize=True)
        buffer.seek(0)
        class OptimizedFile:
            def __init__(self, buffer, original_name):
                self.buffer = buffer
                self.name = original_name.rsplit('.', 1)[0] + '.jpg'
                self.type = "image/jpeg"
                self.size = len(buffer.getvalue())
            def getvalue(self): return self.buffer.getvalue()
        return OptimizedFile(buffer, file.name)
    except Exception: return file

def subir_imagen_storage(file, carpeta="imagenes"):
    try:
        if file is None: return None
        archivo_optimizado = optimizar_imagen(file)
        if archivo_optimizado is None: return None
        nombre_archivo = f"{carpeta}/{uuid.uuid4()}.jpg"
        supabase.storage.from_("imagenes").upload(nombre_archivo, archivo_optimizado.getvalue(), {"content-type": "image/jpeg"})
        return supabase.storage.from_("imagenes").get_public_url(nombre_archivo)
    except Exception as e:
        st.error(f"Error al subir imagen: {str(e)}")
        return None

def subir_multiples_imagenes(files, carpeta):
    urls = []
    if files:
        for file in files:
            url = subir_imagen_storage(file, carpeta)
            if url: urls.append(url)
    return urls

def subir_audio_storage(file):
    try:
        if file is None: return None
        nombre_archivo = f"audio_{uuid.uuid4()}.mp3"
        supabase.storage.from_("imagenes").upload(nombre_archivo, file.getvalue(), {"content-type": "audio/mpeg"})
        return supabase.storage.from_("imagenes").get_public_url(nombre_archivo)
    except Exception as e:
        st.error(f"Error al subir audio: {str(e)}")
        return None

def update_musica(id_, titulo, audio_file=None):
    try:
        audio_url = None
        if audio_file:
            audio_url = subir_audio_storage(audio_file)
        else:
            existing = supabase.table("musicas").select("audio_url").eq("id", id_).execute()
            if existing.data: audio_url = existing.data[0].get("audio_url")
        supabase.table("musicas").update({"titulo": titulo, "audio_url": audio_url}).eq("id", id_).execute()
        return True
    except Exception as e:
        st.error(f"Error al actualizar música: {str(e)}")
        return False

def extraer_video_id(url_youtube):
    if not url_youtube: return None
    patterns = [r'(?:youtube\.com\/watch\?v=)([\w-]+)', r'(?:youtu\.be\/)([\w-]+)', r'(?:youtube\.com\/embed\/)([\w-]+)', r'(?:youtube\.com\/shorts\/)([\w-]+)']
    for pattern in patterns:
        match = re.search(pattern, url_youtube)
        if match: return match.group(1)
    return None

def mostrar_video_youtube(url_youtube, width_percent=25):
    video_id = extraer_video_id(url_youtube)
    if video_id:
        st.markdown(f'<div style="width:{width_percent}%"><iframe width="100%" height="200" src="https://www.youtube.com/embed/{video_id}" frameborder="0" allowfullscreen></iframe></div>', unsafe_allow_html=True)
    else:
        st.error("URL de YouTube no válida")

def extraer_tiktok_id(url_tiktok):
    if not url_tiktok: return None
    patterns = [r'tiktok\.com/(?:@[\w.-]+/video/|v/|embed/)(\d+)', r'tiktok\.com/t/([\w-]+)']
    for pattern in patterns:
        match = re.search(pattern, url_tiktok)
        if match: return match.group(1)
    return None

def mostrar_tiktok(url_tiktok, width_percent=25):
    tiktok_id = extraer_tiktok_id(url_tiktok)
    if tiktok_id:
        st.markdown(f'<div style="width:{width_percent}%"><blockquote class="tiktok-embed" cite="{url_tiktok}"><a target="_blank" href="{url_tiktok}">Ver en TikTok</a></blockquote><script async src="https://www.tiktok.com/embed.js"></script></div>', unsafe_allow_html=True)
    else:
        st.markdown(f"📱 [Ver video en TikTok]({url_tiktok})")

def mostrar_imagenes_en_fila(urls, max_imagenes=3):
    if not urls: return
    cols = st.columns(min(len(urls), max_imagenes))
    for i, url in enumerate(urls[:max_imagenes]):
        with cols[i]: st.image(url, use_container_width=True)

def mostrar_imagen_segura(url, width=300, use_container_width=False):
    if url and isinstance(url, str) and url.startswith(('http://', 'https://')):
        if use_container_width: st.image(url, use_container_width=True)
        else: st.image(url, width=width)
        return True
    return False

# ============================================
# FUNCIONES CRUD COMPLETAS
# ============================================
def get_noticias(categoria=None):
    try:
        if categoria and categoria != "Todas":
            response = supabase.table("noticias").select("*").eq("categoria", categoria).order("id", desc=True).execute()
        else:
            response = supabase.table("noticias").select("*").order("id", desc=True).execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except: return pd.DataFrame()

def add_noticia(titulo, categoria, contenido, imagen):
    try:
        ahora = get_fecha_hora_venezuela()
        data = {"titulo": titulo, "categoria": categoria, "contenido": contenido, "imagen_url": subir_imagen_storage(imagen, "noticias") if imagen else None, "fecha": ahora.strftime("%d/%m/%Y"), "autor": "Admin"}
        supabase.table("noticias").insert(data).execute()
        return True
    except: return False

def update_noticia(id_, titulo, categoria, contenido, imagen):
    try:
        img_url = None
        if imagen: img_url = subir_imagen_storage(imagen, "noticias")
        else:
            existing = supabase.table("noticias").select("imagen_url").eq("id", id_).execute()
            if existing.data: img_url = existing.data[0].get("imagen_url")
        supabase.table("noticias").update({"titulo": titulo, "categoria": categoria, "contenido": contenido, "imagen_url": img_url}).eq("id", id_).execute()
        return True
    except: return False

def delete_noticia(id_):
    try: supabase.table("noticias").delete().eq("id", id_).execute(); return True
    except: return False

def get_negocios():
    try:
        response = supabase.table("negocios").select("*").order("id", desc=True).execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except: return pd.DataFrame()

def add_negocio(nombre, resena, google_maps_url, video_url, imagenes):
    try:
        ahora = get_fecha_hora_venezuela()
        data = {
            "nombre": nombre, 
            "resena": resena, 
            "google_maps_url": google_maps_url if google_maps_url else None,
            "video_url": video_url if video_url else None,
            "imagenes_url": subir_multiples_imagenes(imagenes, "negocios") if imagenes else [], 
            "fecha": ahora.strftime("%d/%m/%Y")
        }
        supabase.table("negocios").insert(data).execute()
        return True
    except Exception as e:
        print(f"Error en add_negocio: {e}")
        return False

def update_negocio(id_, nombre, resena, google_maps_url, video_url, imagenes):
    try:
        imagenes_urls = subir_multiples_imagenes(imagenes, "negocios") if imagenes else None
        if not imagenes_urls:
            existing = supabase.table("negocios").select("imagenes_url").eq("id", id_).execute()
            if existing.data: 
                imagenes_urls = existing.data[0].get("imagenes_url")
        if not video_url:
            existing = supabase.table("negocios").select("video_url").eq("id", id_).execute()
            if existing.data:
                video_url = existing.data[0].get("video_url")
        supabase.table("negocios").update({
            "nombre": nombre, 
            "resena": resena, 
            "google_maps_url": google_maps_url if google_maps_url else None,
            "video_url": video_url if video_url else None,
            "imagenes_url": imagenes_urls if imagenes_urls else []
        }).eq("id", id_).execute()
        return True
    except Exception as e:
        print(f"Error en update_negocio: {e}")
        return False

def delete_negocio(id_):
    try: supabase.table("negocios").delete().eq("id", id_).execute(); return True
    except: return False

def add_opinion_negocio(negocio_id, usuario, comentario, calificacion):
    try:
        ahora = get_fecha_hora_venezuela()
        supabase.table("opiniones_negocios").insert({"negocio_id": negocio_id, "usuario": usuario, "comentario": comentario, "calificacion": calificacion, "fecha": ahora.strftime("%d/%m/%Y %H:%M"), "aprobada": True}).execute()
        return True
    except: return False

def get_opiniones_negocio(negocio_id):
    try:
        response = supabase.table("opiniones_negocios").select("*").eq("negocio_id", negocio_id).order("id", desc=True).execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except: return pd.DataFrame()

def delete_opinion_negocio(id_):
    try: supabase.table("opiniones_negocios").delete().eq("id", id_).execute(); return True
    except: return False

def get_reflexion_activa():
    try:
        response = supabase.table("reflexiones").select("*").eq("activo", True).limit(1).execute()
        if response.data: return response.data[0]
        response = supabase.table("reflexiones").select("*").order("id", desc=True).limit(1).execute()
        return response.data[0] if response.data else None
    except: return None

def get_reflexiones():
    try:
        response = supabase.table("reflexiones").select("*").order("fecha", desc=True).execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except: return pd.DataFrame()

def add_reflexion(titulo, contenido, versiculo):
    try:
        ahora = get_fecha_hora_venezuela()
        supabase.table("reflexiones").update({"activo": False}).execute()
        data = {
            "titulo": titulo,
            "contenido": contenido,
            "versiculo": versiculo if versiculo else None,
            "fecha": ahora.strftime("%d/%m/%Y"),
            "activo": True
        }
        result = supabase.table("reflexiones").insert(data).execute()
        return True if result.data else False
    except Exception as e:
        print(f"Error en add_reflexion: {str(e)}")
        return False

def update_reflexion(id_, titulo, contenido, versiculo):
    try:
        data = {
            "titulo": titulo,
            "contenido": contenido,
            "versiculo": versiculo if versiculo else None
        }
        result = supabase.table("reflexiones").update(data).eq("id", id_).execute()
        return True if result.data else False
    except Exception as e:
        print(f"Error en update_reflexion: {str(e)}")
        return False

def delete_reflexion(id_):
    try: supabase.table("reflexiones").delete().eq("id", id_).execute(); return True
    except: return False

def get_cronicas(estado=None):
    try:
        if estado and estado != "Todos":
            response = supabase.table("cronicas").select("*").eq("estado", estado).order("id", desc=True).execute()
        else:
            response = supabase.table("cronicas").select("*").order("id", desc=True).execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except: return pd.DataFrame()

def add_cronica(titulo, contenido, lugar, estado, imagenes):
    try:
        ahora = get_fecha_hora_venezuela()
        supabase.table("cronicas").insert({"titulo": titulo, "contenido": contenido, "lugar": lugar, "estado": estado, "imagenes_url": subir_multiples_imagenes(imagenes, "cronicas") if imagenes else [], "fecha": ahora.strftime("%d/%m/%Y")}).execute()
        return True
    except: return False

def update_cronica(id_, titulo, contenido, lugar, estado, imagenes):
    try:
        imagenes_urls = subir_multiples_imagenes(imagenes, "cronicas") if imagenes else None
        if not imagenes_urls:
            existing = supabase.table("cronicas").select("imagenes_url").eq("id", id_).execute()
            if existing.data: imagenes_urls = existing.data[0].get("imagenes_url")
        supabase.table("cronicas").update({"titulo": titulo, "contenido": contenido, "lugar": lugar, "estado": estado, "imagenes_url": imagenes_urls}).eq("id", id_).execute()
        return True
    except: return False

def delete_cronica(id_):
    try: supabase.table("cronicas").delete().eq("id", id_).execute(); return True
    except: return False

def get_videos():
    try:
        response = supabase.table("videos").select("*").order("id", desc=True).execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except: return pd.DataFrame()

def add_video(titulo, url_youtube):
    try:
        if not extraer_video_id(url_youtube): return False
        ahora = get_fecha_hora_venezuela()
        supabase.table("videos").insert({"titulo": titulo, "video_url": url_youtube, "fecha": ahora.strftime("%d/%m/%Y")}).execute()
        return True
    except: return False

def update_video(id_, titulo, url_youtube):
    try: supabase.table("videos").update({"titulo": titulo, "video_url": url_youtube}).eq("id", id_).execute(); return True
    except: return False

def delete_video(id_):
    try: supabase.table("videos").delete().eq("id", id_).execute(); return True
    except: return False

def get_tiktoks():
    try:
        response = supabase.table("tiktoks").select("*").order("id", desc=True).execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except: return pd.DataFrame()

def add_tiktok(titulo, url_tiktok):
    try:
        ahora = get_fecha_hora_venezuela()
        supabase.table("tiktoks").insert({"titulo": titulo, "tiktok_url": url_tiktok, "fecha": ahora.strftime("%d/%m/%Y")}).execute()
        return True
    except: return False

def delete_tiktok(id_):
    try: supabase.table("tiktoks").delete().eq("id", id_).execute(); return True
    except: return False

def get_musicas():
    try:
        response = supabase.table("musicas").select("*").order("id", desc=True).execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except: return pd.DataFrame()

def add_musica(titulo, audio_file):
    try:
        ahora = get_fecha_hora_venezuela()
        audio_url = subir_audio_storage(audio_file)
        if not audio_url: return False
        supabase.table("musicas").insert({"titulo": titulo, "audio_url": audio_url, "fecha": ahora.strftime("%d/%m/%Y")}).execute()
        return True
    except: return False

def delete_musica(id_):
    try: supabase.table("musicas").delete().eq("id", id_).execute(); return True
    except: return False

def get_denuncias():
    try:
        response = supabase.table("denuncias").select("*").order("id", desc=True).execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except: return pd.DataFrame()

def add_denuncia(denunciante, titulo, descripcion, ubicacion):
    try:
        ahora = get_fecha_hora_venezuela()
        supabase.table("denuncias").insert({"denunciante": denunciante or "Anonimo", "titulo": titulo, "descripcion": descripcion, "ubicacion": ubicacion, "fecha": ahora.strftime("%d/%m/%Y"), "estatus": "Pendiente"}).execute()
        return True
    except: return False

def update_denuncia_status(id_, status):
    try: supabase.table("denuncias").update({"estatus": status}).eq("id", id_).execute(); return True
    except: return False

def delete_denuncia(id_):
    try: supabase.table("denuncias").delete().eq("id", id_).execute(); return True
    except: return False

def get_opiniones(aprobadas=True):
    try:
        if aprobadas:
            response = supabase.table("opiniones").select("*").eq("aprobada", True).order("id", desc=True).execute()
        else:
            response = supabase.table("opiniones").select("*").order("id", desc=True).execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except: return pd.DataFrame()

def add_opinion(usuario, comentario, calificacion):
    try:
        ahora = get_fecha_hora_venezuela()
        supabase.table("opiniones").insert({"usuario": usuario, "comentario": comentario, "calificacion": calificacion, "fecha": ahora.strftime("%d/%m/%Y %H:%M"), "aprobada": False}).execute()
        return True
    except: return False

def approve_opinion(id_):
    try: supabase.table("opiniones").update({"aprobada": True}).eq("id", id_).execute(); return True
    except: return False

def delete_opinion(id_):
    try: supabase.table("opiniones").delete().eq("id", id_).execute(); return True
    except: return False

def get_personajes():
    try:
        response = supabase.table("personajes").select("*").order("id", desc=True).execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except: return pd.DataFrame()

def add_personaje(nombre, descripcion, imagen, fecha):
    try:
        supabase.table("personajes").insert({"nombre": nombre, "descripcion": descripcion, "imagen_url": subir_imagen_storage(imagen, "personajes") if imagen else None, "fecha": fecha, "activo": True}).execute()
        return True
    except: return False

def update_personaje(id_, nombre, descripcion, imagen, fecha):
    try:
        img_url = None
        if imagen: img_url = subir_imagen_storage(imagen, "personajes")
        else:
            existing = supabase.table("personajes").select("imagen_url").eq("id", id_).execute()
            if existing.data: img_url = existing.data[0].get("imagen_url")
        supabase.table("personajes").update({"nombre": nombre, "descripcion": descripcion, "imagen_url": img_url, "fecha": fecha}).eq("id", id_).execute()
        return True
    except: return False

def delete_personaje(id_):
    try: supabase.table("personajes").delete().eq("id", id_).execute(); return True
    except: return False

def get_crimen_no_paga():
    try:
        response = supabase.table("crimen_no_paga").select("*").order("id", desc=True).execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except: return pd.DataFrame()

def add_crimen_no_paga(titulo, descripcion, imagenes):
    try:
        ahora = get_fecha_hora_venezuela()
        supabase.table("crimen_no_paga").insert({"titulo": titulo, "descripcion": descripcion, "imagenes_url": subir_multiples_imagenes(imagenes, "crimen") if imagenes else [], "fecha": ahora.strftime("%d/%m/%Y")}).execute()
        return True
    except: return False

def update_crimen_no_paga(id_, titulo, descripcion, imagenes):
    try:
        imagenes_urls = subir_multiples_imagenes(imagenes, "crimen") if imagenes else None
        if not imagenes_urls:
            existing = supabase.table("crimen_no_paga").select("imagenes_url").eq("id", id_).execute()
            if existing.data: imagenes_urls = existing.data[0].get("imagenes_url")
        supabase.table("crimen_no_paga").update({"titulo": titulo, "descripcion": descripcion, "imagenes_url": imagenes_urls}).eq("id", id_).execute()
        return True
    except: return False

def delete_crimen_no_paga(id_):
    try: supabase.table("crimen_no_paga").delete().eq("id", id_).execute(); return True
    except: return False

def get_logo():
    try:
        response = supabase.table("configuracion").select("logo_url").eq("id", 1).execute()
        return response.data[0].get("logo_url") if response.data else None
    except: return None

def save_logo(url):
    try: supabase.table("configuracion").update({"logo_url": url}).eq("id", 1).execute(); return True
    except: return False

def inicializar_configuracion():
    try:
        response = supabase.table("configuracion").select("*").eq("id", 1).execute()
        if not response.data: supabase.table("configuracion").insert({"id": 1, "logo_url": None, "dolar": 55.0}).execute()
    except: pass

inicializar_configuracion()

# ============================================
# FUNCIONES PARA LA TIENDA ONLINE
# ============================================
def get_productos(categoria=None, subcategoria=None):
    try:
        query = supabase.table("productos").select("*")
        if categoria and categoria != "Todas":
            query = query.eq("categoria", categoria)
        if subcategoria and subcategoria != "Todas":
            query = query.eq("subcategoria", subcategoria)
        response = query.order("id", desc=True).execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception as e:
        print(f"Error get_productos: {e}")
        return pd.DataFrame()

def add_producto(nombre, descripcion, precio, categoria, subcategoria, imagen, cantidad):
    try:
        ahora = get_fecha_hora_venezuela()
        data = {
            "nombre": nombre,
            "descripcion": descripcion,
            "precio": precio,
            "categoria": categoria,
            "subcategoria": subcategoria,
            "imagen_url": subir_imagen_storage(imagen, "productos") if imagen else None,
            "cantidad": cantidad,
            "fecha": ahora.strftime("%d/%m/%Y")
        }
        supabase.table("productos").insert(data).execute()
        return True
    except Exception as e:
        print(f"Error add_producto: {e}")
        return False

def update_producto(id_, nombre, descripcion, precio, categoria, subcategoria, imagen, cantidad):
    try:
        img_url = None
        if imagen:
            img_url = subir_imagen_storage(imagen, "productos")
        else:
            existing = supabase.table("productos").select("imagen_url").eq("id", id_).execute()
            if existing.data:
                img_url = existing.data[0].get("imagen_url")
        supabase.table("productos").update({
            "nombre": nombre,
            "descripcion": descripcion,
            "precio": precio,
            "categoria": categoria,
            "subcategoria": subcategoria,
            "imagen_url": img_url,
            "cantidad": cantidad
        }).eq("id", id_).execute()
        return True
    except Exception as e:
        print(f"Error update_producto: {e}")
        return False

def delete_producto(id_):
    try:
        supabase.table("productos").delete().eq("id", id_).execute()
        return True
    except:
        return False

# ============================================
# FUNCIONES DE NOTIFICACIONES Y SUSCRIPCIÓN AUTOMÁTICA
# ============================================
def suscribir_usuario_automaticamente(usuario_id):
    try:
        response = supabase.table("suscripciones").select("*").eq("usuario_id", usuario_id).execute()
        if not response.data:
            data = {
                "usuario_id": usuario_id,
                "fecha_suscripcion": datetime.now(pytz.UTC).isoformat(),
                "activa": True,
                "ultima_notificacion": datetime.now(pytz.UTC).isoformat(),
                "ultima_visita": datetime.now(pytz.UTC).isoformat()
            }
            supabase.table("suscripciones").insert(data).execute()
            agregar_notificacion(
                "bienvenida",
                "🎉 ¡Bienvenido a Santa Teresa al Día! Recibirás notificaciones automáticas de novedades.",
                None
            )
            return True
        else:
            supabase.table("suscripciones").update({
                "ultima_visita": datetime.now(pytz.UTC).isoformat()
            }).eq("usuario_id", usuario_id).execute()
            return True
    except Exception as e:
        print(f"Error en suscripción automática: {e}")
        return False

def obtener_suscripciones_activas():
    try:
        response = supabase.table("suscripciones").select("*").eq("activa", True).execute()
        return response.data if response.data else []
    except Exception:
        return []

def agregar_notificacion(tipo, mensaje, link=None):
    try:
        ahora = get_fecha_hora_venezuela()
        data = {
            "tipo": tipo,
            "mensaje": mensaje,
            "link": link,
            "fecha": ahora.strftime("%d/%m/%Y %H:%M"),
            "leida": False,
            "activa": True
        }
        supabase.table("notificaciones").insert(data).execute()
        if 'notificaciones' not in st.session_state:
            st.session_state.notificaciones = []
        st.session_state.notificaciones.insert(0, {
            'mensaje': mensaje,
            'tipo': tipo,
            'fecha': ahora.strftime("%H:%M"),
            'leida': False
        })
        return True
    except Exception as e:
        print(f"Error agregando notificación: {e}")
        return False

def obtener_notificaciones(limite=20):
    try:
        response = supabase.table("notificaciones").select("*").eq("activa", True).order("id", desc=True).limit(limite).execute()
        return pd.DataFrame(response.data) if response.data else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def marcar_notificacion_como_leida(id_):
    try:
        supabase.table("notificaciones").update({"leida": True}).eq("id", id_).execute()
        return True
    except Exception:
        return False

def marcar_todas_como_leidas():
    try:
        supabase.table("notificaciones").update({"leida": True}).eq("leida", False).execute()
        return True
    except Exception:
        return False

def contar_notificaciones_no_leidas():
    try:
        response = supabase.table("notificaciones").select("*", count="exact").eq("leida", False).eq("activa", True).execute()
        return response.count if response.count else 0
    except Exception:
        return 0

def notificar_nueva_noticia(titulo, id_noticia):
    mensaje = f"📰 Nueva noticia: {titulo}"
    link = f"?tab=1&noticia={id_noticia}"
    agregar_notificacion("noticia", mensaje, link)

def notificar_nuevo_comentario(seccion, usuario, contenido):
    mensaje = f"💬 {usuario} comentó en {seccion}: {contenido[:50]}..."
    agregar_notificacion("comentario", mensaje)

def notificar_cambio_dolar(nuevo_valor):
    mensaje = f"💵 El dólar BCV se actualizó a {nuevo_valor:.2f} Bs"
    agregar_notificacion("dolar", mensaje)

def notificar_nuevo_producto(nombre, id_producto):
    mensaje = f"🛍️ Nuevo producto en Willian'Variedades: {nombre}"
    link = f"?tab=11&producto={id_producto}"
    agregar_notificacion("publicacion", mensaje, link)

notificaciones = obtener_notificaciones()
    no_leidas = contar_notificaciones_no_leidas()
    
    if st.session_state.get('es_admin', False):
        if st.session_state.get('es_admin', False):
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            icono = "🔔" if no_leidas == 0 else f"🔔 {no_leidas} ✨"
            if st.button(icono, key="btn_notificaciones", help="Ver notificaciones", use_container_width=True):
                st.session_state.mostrar_notificaciones = not st.session_state.get('mostrar_notificaciones', False)
                st.rerun()
    
    if st.session_state.get('mostrar_notificaciones', False):
            st.rerun()
    
    if st.session_state.get('mostrar_notificaciones', False):
        st.markdown("---")
        st.markdown("### 📬 Centro de Notificaciones")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("✅ Marcar todas como leídas", use_container_width=True):
                if marcar_todas_como_leidas():
                    st.success("Todas las notificaciones marcadas como leídas")
                    st.rerun()
        with col2:
            if st.button("🔄 Actualizar", use_container_width=True):
                st.rerun()
        with col3:
            if st.button("❌ Cerrar", use_container_width=True):
                st.session_state.mostrar_notificaciones = False
                st.rerun()
        
        if not notificaciones.empty:
            for idx, notif in notificaciones.iterrows():
                with st.container():
                    if notif['tipo'] == 'noticia':
                        emoji = "📰"
                    elif notif['tipo'] == 'comentario':
                        emoji = "💬"
                    elif notif['tipo'] == 'dolar':
                        emoji = "💵"
                    elif notif['tipo'] == 'publicacion':
                        emoji = "🛍️"
                    elif notif['tipo'] == 'bienvenida':
                        emoji = "🎉"
                    else:
                        emoji = "📌"
                    
                    if notif['leida']:
                        bg_color = "rgba(255,255,255,0.05)"
                    else:
                        bg_color = "rgba(255,215,0,0.15)"
                    
                    st.markdown(f"""
                    <div style="background: {bg_color}; border-left: 4px solid #FFD700; padding: 10px; border-radius: 5px; margin: 5px 0;">
                        <div style="display: flex; justify-content: space-between;">
                            <span><strong>{emoji} {notif['mensaje']}</strong></span>
                            <span style="font-size: 0.8em; color: #aaa;">{notif['fecha']}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if not notif['leida']:
                        if st.button(f"Marcar como leída", key=f"marcar_{notif['id']}_{idx}"):
                            if marcar_notificacion_como_leida(notif['id']):
                                st.rerun()
                    
                    if notif.get('link'):
                        st.markdown(f"🔗 [Ver más]({notif['link']})")
                    
                    st.divider()
        else:
            st.info("📭 No hay notificaciones")

# ============================================
# DETECTAR DISPOSITIVO MOVIL
# ============================================
def is_mobile():
    try:
        user_agent = st.context.headers.get('User-Agent', '').lower()
        mobile_keywords = ['android', 'iphone', 'ipad', 'mobile']
        return any(k in user_agent for k in mobile_keywords)
    except:
        return False

es_movil = is_mobile()

# ============================================
# OCULTAR ELEMENTOS DE DESARROLLO
# ============================================
st.markdown("""
<style>
#MainMenu {visibility: hidden !important;}
footer {visibility: hidden !important;}
.stDeployButton {display: none !important;}
header {visibility: hidden !important;}
[data-testid="stToolbar"] {display: none !important;}
[data-testid="stStatusWidget"] {display: none !important;}
.stAppDeployButton {display: none !important;}
[data-testid="manage-app-button"] {display: none !important;}
button[kind="header"] {display: none !important;}
[class*="viewerBadge"] {display: none !important;}
[class*="ViewerBadge"] {display: none !important;}
[class*="manageApp"] {display: none !important;}
</style>
""", unsafe_allow_html=True)

# ============================================
# URL DE LA APP
# ============================================
APP_URL = "https://santa-teresa-digital.streamlit.app/"

# ============================================
# CONFIGURACION DE PAGINA
# ============================================
st.set_page_config(page_title="Santa Teresa al Dia", page_icon="🇻🇪", layout="wide")

if 'visitante_contado' not in st.session_state:
    actualizar_visitas()
    st.session_state.visitante_contado = True

# ============================================
# ESTILOS
# ============================================
st.markdown(f"""
<style>
.stApp {{
    background: linear-gradient(rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0.75)), url('{FONDO_URL}') !important;
    background-size: cover !important;
    background-position: center !important;
    background-attachment: fixed !important;
}}
.block-container {{
    background-color: rgba(0, 0, 0, 0.85) !important;
    border-radius: 20px !important;
    padding: 20px !important;
}}
*, .main, .main p, .main span, .main div, .main label, .stMarkdown {{
    color: #FFFFFF !important;
    font-weight: bold !important;
}}
.main h1, .main h2, .main h3, .main h4 {{ color: #FFD700 !important; }}
a {{ color: #FFD700 !important; text-decoration: underline !important; }}
div[data-testid="stTabs"] button {{
    background-color: #1a1a1a !important;
    border: 1px solid #FFD700 !important;
    color: white !important;
    border-radius: 10px !important;
}}
div[data-testid="stTabs"] button:hover {{ background-color: #FFD700 !important; color: black !important; }}
.streamlit-expanderHeader {{ background-color: #1a1a1a !important; border-left: 4px solid #FFD700 !important; color: #FFD700 !important; }}
[data-testid="stSidebar"] {{ background: linear-gradient(180deg, #87CEEB 0%, #4682B4 100%) !important; border-right: 3px solid #FFD700 !important; }}
[data-testid="stSidebar"] * {{ color: #1a1a2e !important; }}
input, textarea, .stTextInput > div > div > input, .stTextArea > div > div > textarea {{
    background-color: #ffffff !important;
    color: #000000 !important;
    border: 2px solid #cccccc !important;
    border-radius: 12px !important;
}}
.stSelectbox > div > div {{
    background-color: #ffffff !important;
    color: #000000 !important;
}}
.stSelectbox > div > div > div {{
    color: #000000 !important;
}}
.stSelectbox label {{
    color: #FFFFFF !important;
}}
.stMultiSelect > div > div {{
    background-color: #ffffff !important;
    color: #000000 !important;
}}
.stMultiSelect > div > div > div {{
    color: #000000 !important;
}}
.stMultiSelect label {{
    color: #FFFFFF !important;
}}
.stMultiSelect [data-baseweb="tag"] {{
    background-color: #e0e0e0 !important;
    color: #000000 !important;
}}
.stMultiSelect [data-baseweb="tag"] span {{
    color: #000000 !important;
}}
.stMultiSelect [data-baseweb="tag"] svg {{
    fill: #000000 !important;
}}
div[data-baseweb="popover"] {{
    background-color: #ffffff !important;
    border: 2px solid #cccccc !important;
    border-radius: 12px !important;
    z-index: 9999 !important;
}}
div[data-baseweb="popover"] ul {{
    background-color: #ffffff !important;
}}
div[data-baseweb="popover"] li {{
    color: #000000 !important;
    background-color: #ffffff !important;
    padding: 8px 12px !important;
}}
div[data-baseweb="popover"] li:hover {{
    background-color: #e0e0e0 !important;
    color: #000000 !important;
}}
div[data-baseweb="popover"] li[aria-selected="true"] {{
    background-color: #d0d0d0 !important;
    color: #000000 !important;
}}
input[type="number"] {{
    background-color: #ffffff !important;
    color: #000000 !important;
    border: 2px solid #cccccc !important;
    border-radius: 12px !important;
}}
.stSlider > div > div > div {{
    color: #FFFFFF !important;
}}
.stSlider label {{
    color: #FFFFFF !important;
}}
.stSlider [data-baseweb="slider"] {{
    background-color: #FFD700 !important;
}}
.stCheckbox label, .stRadio label {{
    color: #FFFFFF !important;
}}
.stCheckbox label span, .stRadio label span {{
    color: #FFFFFF !important;
}}
.stButton > button {{ 
    background: linear-gradient(135deg, #FFD700, #CF142B) !important; 
    color: white !important; 
    border-radius: 25px !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3) !important;
    border: none !important;
}}
.stButton > button:hover {{
    transform: translateY(-3px) !important;
    box-shadow: 0 8px 20px rgba(255, 215, 0, 0.4) !important;
    background: linear-gradient(135deg, #FFE44D, #E01830) !important;
}}
.stButton > button:active {{
    transform: translateY(0px) !important;
    box-shadow: 0 2px 10px rgba(255, 215, 0, 0.2) !important;
}}
div[data-testid="column"] .stButton > button {{
    background: linear-gradient(135deg, #0a6b8a, #1a8aaa) !important;
    color: #FFFFFF !important;
    border: 2px solid #00d4ff !important;
    border-radius: 14px !important;
    padding: 14px 10px !important;
    font-size: 1em !important;
    font-weight: bold !important;
    box-shadow: 0 4px 20px rgba(0, 180, 216, 0.3) !important;
    transition: all 0.3s ease !important;
    width: 100% !important;
    text-shadow: 0 1px 2px rgba(0,0,0,0.3) !important;
}}
div[data-testid="column"] .stButton > button:hover {{
    background: linear-gradient(135deg, #00d4ff, #0099cc) !important;
    transform: translateY(-4px) !important;
    box-shadow: 0 8px 35px rgba(0, 180, 216, 0.6) !important;
    border-color: #FFD700 !important;
    color: #FFFFFF !important;
}}
div[data-testid="column"] .stButton > button:active {{
    transform: translateY(0px) !important;
    box-shadow: 0 2px 10px rgba(0, 180, 216, 0.2) !important;
}}
div[data-testid="column"] .stButton > button p {{
    color: #FFFFFF !important;
    font-weight: bold !important;
    margin: 0 !important;
}}
.streamlit-expanderContent {{
    color: #FFFFFF !important;
}}
.streamlit-expanderContent p, .streamlit-expanderContent li, .streamlit-expanderContent div {{
    color: #FFFFFF !important;
}}
.stAlert {{
    background-color: rgba(0, 0, 0, 0.8) !important;
    color: #FFFFFF !important;
}}
.stAlert p {{
    color: #FFFFFF !important;
}}
.stAlert .stMarkdown {{
    color: #FFFFFF !important;
}}
.bronze-footer {{ background: linear-gradient(145deg, #8c6a31, #5d431a) !important; border: 5px solid #d4af37 !important; padding: 35px 25px !important; border-radius: 20px !important; text-align: center !important; margin-top: 50px !important; }}
.bronze-footer p {{ color: #ffd700 !important; }}
.stInfo, .stSuccess, .stWarning, .stError {{ background-color: rgba(0,0,0,0.8) !important; color: white !important; }}
[data-testid="stMetricValue"] {{ color: #FFD700 !important; font-size: 1.5rem !important; }}
</style>
""", unsafe_allow_html=True)

# ============================================
# LOGO
# ============================================
logo = get_logo()
if logo:
    st.markdown(f'<div style="text-align: center;"><img src="{logo}" style="max-width: 200px;"></div>', unsafe_allow_html=True)

# ============================================
# BOTONES DE COMPARTIR
# ============================================
st.markdown(f"""
<div style="display: flex; justify-content: center; gap: 15px; flex-wrap: wrap; margin: 15px 0;">
    <a href="https://api.whatsapp.com/send?text=Santa Teresa al Dia - {APP_URL}" target="_blank" style="display: inline-block; padding: 10px 25px; border-radius: 25px; background: #25D366; transition: all 0.3s ease;">📱 WhatsApp</a>
    <a href="https://www.facebook.com/sharer/sharer.php?u={APP_URL}" target="_blank" style="display: inline-block; padding: 10px 25px; border-radius: 25px; background: #1877F2; transition: all 0.3s ease;">📘 Facebook</a>
    <a href="https://www.instagram.com/" target="_blank" style="display: inline-block; padding: 10px 25px; border-radius: 25px; background: linear-gradient(45deg, #f09433, #d62976); transition: all 0.3s ease;">📸 Instagram</a>
    <button id="copyButton" style="display: inline-block; padding: 10px 25px; border-radius: 25px; background: #3498db; border: none; cursor: pointer; transition: all 0.3s ease;">📋 Copiar</button>
</div>
<script>
document.getElementById('copyButton').addEventListener('click', function() {{
    navigator.clipboard.writeText('{APP_URL}');
    alert('Enlace copiado: {APP_URL}');
}});
</script>
""", unsafe_allow_html=True)

st.markdown("---")

# ============================================
# ENCABEZADO PRINCIPAL
# ============================================
ahora = get_fecha_hora_venezuela()
dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
visitas = get_visitas()
dolar = get_dolar()
hora_str = ahora.strftime("%I:%M %p").lstrip("0")
total_likes = obtener_total_likes()

if 'usuario_id_permanente' not in st.session_state:
    query_params = st.query_params
    if 'uid' in query_params:
        st.session_state.usuario_id_permanente = query_params['uid']
    else:
        nuevo_id = hashlib.md5(f"{time.time()}_{uuid.uuid4()}".encode()).hexdigest()
        st.query_params['uid'] = nuevo_id
        st.session_state.usuario_id_permanente = nuevo_id

usuario_id_permanente = st.session_state.usuario_id_permanente
ya_like = ya_dio_like(usuario_id_permanente)

if 'usuario_suscrito' not in st.session_state:
    suscribir_usuario_automaticamente(usuario_id_permanente)
    st.session_state.usuario_suscrito = True

st.markdown(f"""
<div style="background: linear-gradient(135deg, #1a1a1a, #2a2a2a); border-radius: 20px; padding: 30px 20px; border: 2px solid #FFD700; margin-bottom: 20px; text-align: center;">
    <div style="font-size: 2.2em; font-weight: bold; color: #FFD700;">Santa Teresa al Dia</div>
    <div style="font-size: 1.2em; margin-bottom: 20px;">Informacion, Cultura y Fe de nuestro pueblo</div>
    <div style="font-size: 0.95em; color: #FFD700;">⭐ {dias[ahora.weekday()]}, {ahora.day} de {meses[ahora.month-1]} de {ahora.year} ⭐</div>
    <div style="font-size: 1.05em;">🕐 {hora_str}</div>
    <div style="font-size: 0.95em; color: #FFD700;">👥 Visitantes: {visitas:,} | 💵 Dólar BCV: {dolar:.2f} Bs</div>
    <div style="border-top: 1px solid rgba(255,215,0,0.3); margin-top: 15px; padding-top: 15px;">
        <div style="display: flex; justify-content: center; gap: 20px;">
            <div>❤️ Apoya</div>
            <div>👍 <span style="color:#FFD700; font-size:1.5em;">{total_likes:,}</span></div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

if not ya_like:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("👍 Dar Me gusta", use_container_width=True):
            exito, mensaje = agregar_like_usuario(usuario_id_permanente)
            if exito:
                st.success(f"✅ {mensaje}!")
                st.balloons()
                st.rerun()
            else:
                st.error(f"❌ {mensaje}")
else:
    st.info("❤️ ¡Gracias por tu apoyo!")

st.markdown("---")

# Sección "Gracias a la comunidad" eliminada

def mostrar_panel_notificaciones():
    notificaciones = obtener_notificaciones()
    no_leidas = contar_notificaciones_no_leidas()

    if st.session_state.get('es_admin', False):
        col1, col2, col3 = st.columns([1, 3, 1])
        with col2:
            icono = "🔔" if no_leidas == 0 else f"🔔 {no_leidas} ✨"
            if st.button(icono, key="btn_notificaciones", help="Ver notificaciones", use_container_width=True):
                st.session_state.mostrar_notificaciones = not st.session_state.get('mostrar_notificaciones', False)
                st.rerun()

    if st.session_state.get('mostrar_notificaciones', False):
        st.markdown("---")
        st.markdown("### 📬 Centro de Notificaciones")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("✅ Marcar todas como leídas", use_container_width=True):
                if marcar_todas_como_leidas():
                    st.success("Todas las notificaciones marcadas como leídas")
                    st.rerun()
        with col2:
            if st.button("🔄 Actualizar", use_container_width=True):
                st.rerun()
        with col3:
            if st.button("❌ Cerrar", use_container_width=True):
                st.session_state.mostrar_notificaciones = False
                st.rerun()

        if not notificaciones.empty:
            for idx, notif in notificaciones.iterrows():
                with st.container():
                    if notif['tipo'] == 'noticia':
                        emoji = "📰"
                    elif notif['tipo'] == 'comentario':
                        emoji = "💬"
                    elif notif['tipo'] == 'dolar':
                        emoji = "💵"
                    elif notif['tipo'] == 'publicacion':
                        emoji = "🛍️"
                    elif notif['tipo'] == 'bienvenida':
                        emoji = "🎉"
                    else:
                        emoji = "📌"

                    if notif['leida']:
                        bg_color = "rgba(255,255,255,0.05)"
                    else:
                        bg_color = "rgba(255,215,0,0.15)"

                    st.markdown(f"""
                    <div style="background: {bg_color}; border-left: 4px solid #FFD700; padding: 10px; border-radius: 5px; margin: 5px 0;">
                        <div style="display: flex; justify-content: space-between;">
                            <span><strong>{emoji} {notif['mensaje']}</strong></span>
                            <span style="font-size: 0.8em; color: #aaa;">{notif['fecha']}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if not notif['leida']:
                        if st.button(f"Marcar como leída", key=f"marcar_{notif['id']}_{idx}"):
                            if marcar_notificacion_como_leida(notif['id']):
                                st.rerun()

                    if notif.get('link'):
                        st.markdown(f"🔗 [Ver más]({notif['link']})")

                    st.divider()
        else:
            st.info("📭 No hay notificaciones")

# ============================================
# SIDEBAR ADMIN
# ============================================
with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/7/7b/Flag_of_Venezuela_%28state%29.svg/1200px-Flag_of_Venezuela_%28state%29.svg.png", width=150)
    st.markdown("---")
    
    st.markdown("### 🔐 Administración")
    clave = st.text_input("Clave de acceso:", type="password", key="admin_pass")
    
    es_admin = False
    if clave == "Juan*316*" or clave == "1966":
        es_admin = True
        st.success("✅ Acceso concedido")
        st.caption(f"💵 Dólar actual: {dolar:.2f} Bs")
    elif clave:
        st.error("❌ Clave incorrecta")
    
    if es_admin:
        st.markdown("---")
        st.markdown("### 📋 Panel de Control")
        admin_opt = st.radio("Seleccionar módulo:", [
            "📰 Noticias", "🏪 Negocios", "💭 Reflexiones", "📜 Crónicas",
            "🎬 Videos", "📱 TikTok", "🎵 Música", "⚠️ Denuncias", 
            "💬 Opiniones", "👥 Personajes", "⚖️ El Crimen No Paga", 
            "⚙️ Configuración", "💬 GESTIONAR COMENTARIOS",
            "🏥 GESTIONAR ENFERMEDADES", "🛍️ Tu Tienda Online"
        ])
        st.session_state.admin_opt = admin_opt
        st.session_state.es_admin = True
        
        st.markdown("---")
        st.markdown("### 📊 Estadísticas")
        st.metric("👍 Total Me gusta", f"{total_likes:,}")
        st.metric("👤 Likes reales", f"{obtener_likes_reales():,}")
        st.metric("🤖 Likes automáticos", f"{obtener_likes_automaticos():,}")
        st.metric("👥 Visitantes", f"{visitas:,}")
        
        suscripciones = obtener_suscripciones_activas()
        st.metric("📬 Suscritos", len(suscripciones))
        
        with st.expander("🔧 Depuración"):
            st.code(f"Tu ID: {usuario_id_permanente}")
            st.code(f"¿Ya dio like?: {ya_like}")
    else:
        st.session_state.es_admin = False

# ============================================
# MENÚ PRINCIPAL
# ============================================
st.markdown("### 📌 Secciones Principales")
col_linea1 = st.columns(4)
with col_linea1[0]:
    if st.button("🏠 Portada", use_container_width=True, key="tab_0"):
        st.session_state.selected_tab = 0
with col_linea1[1]:
    if st.button("📰 Noticias", use_container_width=True, key="tab_1"):
        st.session_state.selected_tab = 1
with col_linea1[2]:
    if st.button("📍 Donde ir - Donde comprar", use_container_width=True, key="tab_2"):
        st.session_state.selected_tab = 2
with col_linea1[3]:
    if st.button("💭 Reflexiones", use_container_width=True, key="tab_3"):
        st.session_state.selected_tab = 3

st.markdown("### 🎬 Contenido Multimedia")
col_linea2 = st.columns(4)
with col_linea2[0]:
    if st.button("📜 Crónicas", use_container_width=True, key="tab_4"):
        st.session_state.selected_tab = 4
with col_linea2[1]:
    if st.button("🎬 Multimedia", use_container_width=True, key="tab_5"):
        st.session_state.selected_tab = 5
with col_linea2[2]:
    if st.button("⚠️ Denuncias", use_container_width=True, key="tab_6"):
        st.session_state.selected_tab = 6
with col_linea2[3]:
    if st.button("💬 Opiniones", use_container_width=True, key="tab_7"):
        st.session_state.selected_tab = 7

st.markdown("### 📖 Otras Secciones")
col_linea3 = st.columns(4)
with col_linea3[0]:
    if st.button("👥 Personajes", use_container_width=True, key="tab_8"):
        st.session_state.selected_tab = 8
with col_linea3[1]:
    if st.button("⚖️ El Crimen No Paga", use_container_width=True, key="tab_9"):
        st.session_state.selected_tab = 9
with col_linea3[2]:
    if st.button("📅 Efemérides Médicas", use_container_width=True, key="tab_10"):
        st.session_state.selected_tab = 10
with col_linea3[3]:
    if st.button("🛍️ Willian'Variedades", use_container_width=True, key="tab_11"):
        st.session_state.selected_tab = 11

# ============================================
# NUEVA SECCIÓN: HABLANDO CON TUS DOCTORES
# ============================================
st.markdown("### 🩺 Hablando con tus doctores")

col_salud = st.columns(4)
with col_salud[0]:
    if st.button("🩺 Evaluar Síntomas", use_container_width=True, key="tab_20"):
        st.session_state.selected_tab = 20
        st.rerun()
with col_salud[1]:
    if st.button("📍 Directorio Médico", use_container_width=True, key="tab_21"):
        st.session_state.selected_tab = 21
        st.rerun()
with col_salud[2]:
    if st.button("📚 Guías de Salud", use_container_width=True, key="tab_22"):
        st.session_state.selected_tab = 22
        st.rerun()
with col_salud[3]:
    if st.button("💬 Pregunta al Doctor", use_container_width=True, key="tab_23"):
        st.session_state.selected_tab = 23
        st.rerun()

st.markdown("---")

if 'selected_tab' not in st.session_state:
    st.session_state.selected_tab = 0

# ============================================
# CONTENIDO DE LAS SECCIONES EXISTENTES
# ============================================

# --- PORTADA (TAB 0) ---
if st.session_state.selected_tab == 0:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 📰 Últimas Noticias")
        noticias = get_noticias()
        if not noticias.empty:
            for idx, n in noticias.head(5).iterrows():
                with st.expander(f"📰 {n['titulo']} - {n['categoria']} ({n['fecha']})"):
                    mostrar_imagen_segura(n.get('imagen_url'), 300)
                    st.write(n['contenido'])
                    mostrar_seccion_comentarios("noticia", n['id'], n['titulo'], es_admin)
        else:
            st.info("No hay noticias disponibles")
        
        st.markdown("### 📽️ Últimos Reportajes")
        reportajes = get_noticias(categoria="Reportajes")
        if not reportajes.empty:
            for idx, r in reportajes.head(3).iterrows():
                with st.expander(f"📽️ {r['titulo']} - {r['fecha']}"):
                    mostrar_imagen_segura(r.get('imagen_url'), 300)
                    st.write(r['contenido'])
                    mostrar_seccion_comentarios("reportaje", r['id'], r['titulo'], es_admin)
        else:
            st.info("No hay reportajes disponibles")
    
    with col2:
        st.markdown("### ✝️ Reflexión del Día")
        ref = get_reflexion_activa()
        if ref:
            with st.expander(f"✨ {ref['titulo']}", expanded=True):
                st.write(ref['contenido'])
                if ref.get('versiculo'):
                    st.caption(f"📖 {ref['versiculo']}")
                mostrar_seccion_comentarios("reflexion", ref['id'], ref['titulo'], es_admin)
        else:
            st.info("No hay reflexión activa")
        
        st.markdown("---")
        st.markdown("### 💬 Opiniones de la Comunidad")
        
        opiniones_portada = get_opiniones(aprobadas=True)
        
        if not opiniones_portada.empty:
            for idx, op in opiniones_portada.head(5).iterrows():
                stars = "⭐" * int(op['calificacion']) + "☆" * (5 - int(op['calificacion']))
                with st.container():
                    st.markdown(f"**👤 {op['usuario']}** {stars}")
                    st.markdown(f"\"{op['comentario']}\"")
                    st.caption(f"📅 {op['fecha']}")
                    st.divider()
            
            if len(opiniones_portada) > 5:
                st.caption(f"📌 Mostrando 5 de {len(opiniones_portada)} opiniones. Ve a la sección 'Opiniones' para ver todas.")
        else:
            st.info("💬 No hay opiniones aún. ¡Sé el primero en opinar!")

# --- NOTICIAS (TAB 1) ---
elif st.session_state.selected_tab == 1:
    st.title("📰 Noticias")
    tab_nac, tab_inter, tab_dep, tab_suc, tab_far, tab_rep = st.tabs(["🇻🇪 Nacionales", "🌎 Internacionales", "⚽ Deportes", "🚨 Sucesos", "🎭 Farándula", "📽️ Reportajes"])
    
    for tab, categoria in zip([tab_nac, tab_inter, tab_dep, tab_suc, tab_far, tab_rep], 
                               ["Nacional", "Internacional", "Deportes", "Sucesos", "Farándula", "Reportajes"]):
        with tab:
            noticias_cat = get_noticias(categoria=categoria)
            if not noticias_cat.empty:
                for idx, n in noticias_cat.iterrows():
                    with st.expander(f"📰 {n['titulo']} - {n['fecha']}"):
                        mostrar_imagen_segura(n.get('imagen_url'), 300)
                        st.write(n['contenido'])
                        mostrar_seccion_comentarios("noticia" if categoria != "Reportajes" else "reportaje", n['id'], n['titulo'], es_admin)
            else:
                st.info(f"No hay noticias de {categoria}")

# --- NEGOCIOS (TAB 2) ---
elif st.session_state.selected_tab == 2:
    st.title("📍 Donde ir - Donde comprar")
    negocios = get_negocios()
    if not negocios.empty:
        for idx, n in negocios.iterrows():
            with st.expander(f"🏪 {n['nombre']}"):
                if n.get('imagenes_url') and n['imagenes_url']:
                    if isinstance(n['imagenes_url'], list) and len(n['imagenes_url']) > 0:
                        mostrar_imagenes_en_fila(n['imagenes_url'], max_imagenes=3)
                    elif isinstance(n['imagenes_url'], str):
                        mostrar_imagen_segura(n['imagenes_url'], 300)
                else:
                    st.caption("📷 Sin imágenes")
                
                st.write(f"**Reseña:** {n['resena']}")
                
                if n.get('video_url') and n['video_url']:
                    st.markdown("#### 🎥 Video del negocio")
                    mostrar_video_youtube(n['video_url'], width_percent=50)
                
                if n.get('google_maps_url') and n['google_maps_url']:
                    st.markdown(f"📍 [Ver ubicación en Google Maps]({n['google_maps_url']})")
                
                st.markdown("---")
                st.markdown("### 💬 Opiniones de este negocio")
                
                with st.form(f"opinion_form_{n['id']}"):
                    st.markdown("#### Deja tu opinión")
                    nombre_usuario = st.text_input("Tu nombre", key=f"nombre_{n['id']}")
                    comentario = st.text_area("Comentario", key=f"comentario_{n['id']}")
                    calificacion = st.slider("Calificación", 1, 5, 5, key=f"calif_{n['id']}")
                    if st.form_submit_button("Enviar Opinión"):
                        if nombre_usuario and comentario:
                            if add_opinion_negocio(n['id'], nombre_usuario, comentario, calificacion):
                                st.success("✅ Opinión enviada")
                                st.rerun()
                            else:
                                st.error("❌ Error al enviar opinión")
                        else:
                            st.error("❌ Nombre y comentario son obligatorios")
                
                opiniones = get_opiniones_negocio(n['id'])
                if not opiniones.empty:
                    for idx2, op in opiniones.iterrows():
                        stars = "⭐" * int(op['calificacion']) + "☆" * (5 - int(op['calificacion']))
                        st.markdown(f"**👤 {op['usuario']}** {stars}")
                        st.write(f"\"{op['comentario']}\"")
                        st.caption(f"📅 {op['fecha']}")
                        st.divider()
                else:
                    st.info("No hay opiniones para este negocio")
    else:
        st.info("No hay negocios agregados aún")

# --- REFLEXIONES (TAB 3) ---
elif st.session_state.selected_tab == 3:
    st.title("💭 Reflexiones")
    
    ref = get_reflexion_activa()
    if ref:
        with st.expander(f"✨ ACTUAL: {ref['titulo']}", expanded=True):
            st.write(ref['contenido'])
            if ref.get('versiculo'):
                st.caption(f"📖 {ref['versiculo']}")
            st.caption(f"📅 {ref['fecha']}")
            mostrar_seccion_comentarios("reflexion", ref['id'], ref['titulo'], es_admin)
    else:
        st.info("No hay reflexión activa")
    
    st.markdown("---")
    
    if es_admin:
        st.markdown("### ✏️ Crear Nueva Reflexión")
        with st.form("nueva_reflexion_form"):
            nuevo_titulo = st.text_input("Título de la reflexión *")
            nuevo_versiculo = st.text_input("Versículo (opcional)")
            nuevo_contenido = st.text_area("Contenido de la reflexión *", height=150)
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("💾 Guardar como activa", use_container_width=True):
                    if nuevo_titulo and nuevo_contenido:
                        if add_reflexion(nuevo_titulo, nuevo_contenido, nuevo_versiculo):
                            st.success("✅ Reflexión guardada correctamente")
                            st.balloons()
                            st.rerun()
                        else:
                            st.error("❌ Error al guardar la reflexión")
                    else:
                        st.error("❌ Título y contenido son obligatorios")
            with col2:
                if st.form_submit_button("❌ Limpiar", use_container_width=True):
                    st.rerun()
        
        st.markdown("---")
    
    st.markdown("### 📜 Reflexiones Anteriores")
    reflexiones = get_reflexiones()
    if not reflexiones.empty:
        for idx, r in reflexiones.iterrows():
            if ref is None or r['id'] != ref['id']:
                with st.expander(f"📖 {r['titulo']} - {r['fecha']}"):
                    st.write(r['contenido'])
                    if r.get('versiculo'):
                        st.caption(f"📖 {r['versiculo']}")
                    
                    if es_admin:
                        st.markdown("---")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button(f"✏️ MODIFICAR", key=f"edit_ref_{r['id']}_{idx}"):
                                st.session_state.edit_reflexion = r.to_dict()
                                st.rerun()
                        with col2:
                            if st.button(f"🗑️ ELIMINAR", key=f"del_ref_{r['id']}_{idx}"):
                                if delete_reflexion(r['id']):
                                    st.success("✅ Reflexión eliminada")
                                    st.rerun()
                    
                    mostrar_seccion_comentarios("reflexion", r['id'], r['titulo'], es_admin)
    else:
        st.info("No hay reflexiones anteriores")
    
    if st.session_state.get('edit_reflexion'):
        r = st.session_state.edit_reflexion
        st.markdown("---")
        st.subheader(f"✏️ Modificando: {r['titulo']}")
        with st.form("edit_reflexion_form"):
            nuevo_titulo = st.text_input("Título", value=r['titulo'])
            nuevo_versiculo = st.text_input("Versículo", value=r.get('versiculo', ''))
            nuevo_contenido = st.text_area("Contenido", value=r['contenido'])
            
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("💾 Guardar cambios"):
                    if update_reflexion(r['id'], nuevo_titulo, nuevo_contenido, nuevo_versiculo):
                        st.success("✅ Reflexión actualizada")
                        del st.session_state.edit_reflexion
                        st.rerun()
            with col2:
                if st.form_submit_button("❌ Cancelar"):
                    del st.session_state.edit_reflexion
                    st.rerun()

# --- CRÓNICAS (TAB 4) ---
elif st.session_state.selected_tab == 4:
    st.title("📜 Crónicas")
    estados = ["Todos", "Miranda", "Carabobo", "Distrito Capital", "Zulia", "Lara", "Aragua", "Bolivar", "Anzoategui", "Merida", "Tachira", "Nueva Esparta", "Sucre", "Falcon", "Barinas", "Portuguesa", "Guarico", "Cojedes", "Trujillo", "Yaracuy", "Apure", "Amazonas", "Delta Amacuro", "Vargas"]
    estado_filtro = st.selectbox("Filtrar por estado:", estados)
    cronicas = get_cronicas(estado_filtro if estado_filtro != "Todos" else None)
    if not cronicas.empty:
        for idx, c in cronicas.iterrows():
            with st.expander(f"📖 {c['titulo']} - {c['lugar']}, {c['estado']}"):
                if c.get('imagenes_url') and c['imagenes_url']:
                    if isinstance(c['imagenes_url'], list) and len(c['imagenes_url']) > 0:
                        mostrar_imagenes_en_fila(c['imagenes_url'], max_imagenes=3)
                    elif isinstance(c['imagenes_url'], str):
                        mostrar_imagen_segura(c['imagenes_url'], 200)
                st.write(c['contenido'])
                st.caption(f"📅 {c['fecha']}")
                mostrar_seccion_comentarios("cronica", c['id'], c['titulo'], es_admin)
                
                if es_admin:
                    st.markdown("---")
                    st.markdown("### 🔧 Administrar esta crónica")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"✏️ MODIFICAR CRÓNICA", key=f"edit_cron_{c['id']}_{idx}"):
                            st.session_state.edit_cronica = c.to_dict()
                            st.rerun()
                    with col2:
                        if st.button(f"🗑️ ELIMINAR CRÓNICA", key=f"del_cron_{c['id']}_{idx}"):
                            if delete_cronica(c['id']):
                                st.success("✅ Crónica eliminada")
                                st.rerun()
    else:
        st.info("No hay crónicas disponibles")
    
    if 'edit_cronica' in st.session_state:
        c = st.session_state.edit_cronica
        st.markdown("---")
        st.subheader(f"✏️ Modificando: {c['titulo']}")
        with st.form("edit_cronica_form"):
            nuevo_titulo = st.text_input("Título", value=c['titulo'])
            nuevo_lugar = st.text_input("Lugar", value=c['lugar'])
            nuevo_estado = st.selectbox("Estado", ["Miranda", "Carabobo", "Distrito Capital", "Zulia", "Lara", "Aragua", "Bolivar", "Anzoategui", "Merida", "Tachira", "Nueva Esparta", "Sucre", "Falcon", "Barinas", "Portuguesa", "Guarico", "Cojedes", "Trujillo", "Yaracuy", "Apure", "Amazonas", "Delta Amacuro", "Vargas"], index=["Miranda", "Carabobo", "Distrito Capital", "Zulia", "Lara", "Aragua", "Bolivar", "Anzoategui", "Merida", "Tachira", "Nueva Esparta", "Sucre", "Falcon", "Barinas", "Portuguesa", "Guarico", "Cojedes", "Trujillo", "Yaracuy", "Apure", "Amazonas", "Delta Amacuro", "Vargas"].index(c['estado']))
            nuevo_contenido = st.text_area("Contenido", value=c['contenido'])
            nuevas_imagenes = st.file_uploader("Nuevas fotos (opcional)", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("💾 Guardar cambios"):
                    if update_cronica(c['id'], nuevo_titulo, nuevo_contenido, nuevo_lugar, nuevo_estado, nuevas_imagenes):
                        st.success("✅ Crónica actualizada")
                        del st.session_state.edit_cronica
                        st.rerun()
            with col2:
                if st.form_submit_button("❌ Cancelar"):
                    del st.session_state.edit_cronica
                    st.rerun()

# --- MULTIMEDIA (TAB 5) ---
elif st.session_state.selected_tab == 5:
    st.title("🎬 Multimedia")
    tab_vid, tab_tik, tab_mus, tab_rad = st.tabs(["🎥 YouTube", "📱 TikTok", "🎵 Música", "📻 Radio"])
    
    with tab_vid:
        st.markdown("### 🎥 Videos de YouTube")
        videos = get_videos()
        if not videos.empty:
            for idx, v in videos.iterrows():
                with st.expander(f"🎬 {v['titulo']}"):
                    mostrar_video_youtube(v['video_url'], width_percent=50)
                    st.caption(f"📅 {v['fecha']}")
                    mostrar_seccion_comentarios("video", v['id'], v['titulo'], es_admin)
        else:
            st.info("No hay videos disponibles")
    
    with tab_tik:
        st.markdown("### 📱 Videos de TikTok")
        tiktoks = get_tiktoks()
        if not tiktoks.empty:
            for idx, t in tiktoks.iterrows():
                with st.expander(f"📱 {t['titulo']}"):
                    mostrar_tiktok(t['tiktok_url'], width_percent=50)
                    st.caption(f"📅 {t['fecha']}")
                    mostrar_seccion_comentarios("tiktok", t['id'], t['titulo'], es_admin)
        else:
            st.info("No hay videos de TikTok disponibles")
    
    with tab_mus:
        st.markdown("### 🎵 Lista de Música")
        musicas = get_musicas()
        if not musicas.empty:
            for idx, m in musicas.iterrows():
                with st.expander(f"🎵 {m['titulo']}"):
                    if m.get('audio_url') and m['audio_url']:
                        st.audio(m['audio_url'], format="audio/mp3")
                        st.caption(f"📅 {m['fecha']}")
                    else:
                        st.warning("No hay URL de audio disponible")
                    mostrar_seccion_comentarios("musica", m['id'], m['titulo'], es_admin)
        else:
            st.info("No hay música disponible")
    
    with tab_rad:
        st.markdown("### 📻 Radio Online")
        st.markdown("#### 🎵 Estaciones de Radio")
        
        radio_opcion = st.selectbox("Selecciona una emisora:", [
            "🎵 80s Forever (Inglés)",
            "💕 Baladas Románticas (Inglés)",
            "🕺 Disco Hits 70s 80s",
            "🎺 Salsa Clásica"
        ])
        
        if radio_opcion == "🎵 80s Forever (Inglés)":
            st.audio("https://stream.zeno.fm/fsx7rzc2x1zuv", format="audio/mp3")
            st.caption("🎶 Madonna, Michael Jackson, Whitney Houston, Prince")
        elif radio_opcion == "💕 Baladas Románticas (Inglés)":
            st.audio("https://stream.zeno.fm/08f62gs7mg0uv", format="audio/mp3")
            st.caption("🎶 Air Supply, Chicago, Foreigner, Journey")
        elif radio_opcion == "🕺 Disco Hits 70s 80s":
            st.audio("https://stream.zeno.fm/76pz71spy7zuv", format="audio/mp3")
            st.caption("🎶 Bee Gees, ABBA, Donna Summer")
        elif radio_opcion == "🎺 Salsa Clásica":
            st.audio("https://stream.zeno.fm/cf6uxm5sd6quv", format="audio/mp3")
            st.caption("🎺 Héctor Lavoe, Celia Cruz, Rubén Blades")

# --- DENUNCIAS (TAB 6) ---
elif st.session_state.selected_tab == 6:
    st.title("⚠️ Denuncias Ciudadanas")
    
    tab_den, tab_ver = st.tabs(["📝 Hacer Denuncia", "👁️ Ver Denuncias"])
    
    with tab_den:
        st.markdown("### Formulario de Denuncia")
        st.info("Tu identidad se mantendrá en el anonimato si así lo deseas.")
        
        with st.form("form_denuncia"):
            nombre = st.text_input("Nombre (opcional - puede ser anónimo)")
            titulo = st.text_input("Título de la denuncia *")
            descripcion = st.text_area("Descripción detallada de los hechos *", height=150)
            ubicacion = st.text_input("Ubicación (sector, calle, dirección)")
            
            st.markdown("---")
            submitted = st.form_submit_button("📤 Enviar Denuncia", use_container_width=True)
            
            if submitted:
                if titulo and descripcion:
                    if add_denuncia(nombre, titulo, descripcion, ubicacion):
                        st.success("✅ ¡Denuncia enviada correctamente!")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Error al enviar la denuncia. Intenta nuevamente.")
                else:
                    st.error("❌ El título y la descripción son obligatorios.")
    
    with tab_ver:
        st.markdown("### Listado de Denuncias")
        denuncias = get_denuncias()
        
        if not denuncias.empty:
            for idx, d in denuncias.iterrows():
                with st.expander(f"📌 {d['titulo']}"):
                    st.write(f"**Denunciante:** {d['denunciante']}")
                    st.write(f"**Descripción:** {d['descripcion']}")
                    if d.get('ubicacion') and d['ubicacion'] != "No especificada":
                        st.write(f"**Ubicación:** {d['ubicacion']}")
                    
                    if d['estatus'] == "Pendiente":
                        st.warning(f"**Estado:** {d['estatus']}")
                    elif d['estatus'] == "En revisión":
                        st.info(f"**Estado:** {d['estatus']}")
                    elif d['estatus'] == "Resuelta":
                        st.success(f"**Estado:** {d['estatus']}")
                    else:
                        st.error(f"**Estado:** {d['estatus']}")
                    st.caption(f"📅 Fecha: {d['fecha']}")
        else:
            st.info("No hay denuncias registradas aún.")

# --- OPINIONES (TAB 7) ---
elif st.session_state.selected_tab == 7:
    st.title("💬 Opiniones de la Comunidad")
    
    tab_op, tab_ver_op = st.tabs(["✍️ Dar Opinión", "👁️ Todas las Opiniones Aprobadas"])
    
    with tab_op:
        st.markdown("### Comparte tu opinión sobre Santa Teresa al Día")
        st.caption("Tu opinión será revisada por un administrador antes de ser publicada.")
        
        with st.form("form_opinion"):
            nombre = st.text_input("Nombre o apodo *")
            comentario = st.text_area("Tu comentario u opinión *", height=120)
            calificacion = st.slider("Calificación (1 a 5 estrellas)", 1, 5, 5)
            
            st.markdown("---")
            submitted = st.form_submit_button("📤 Enviar Opinión", use_container_width=True)
            
            if submitted:
                if nombre and comentario:
                    if add_opinion(nombre, comentario, calificacion):
                        st.success("✅ ¡Opinión enviada! Será revisada por el administrador.")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Error al enviar la opinión. Intenta nuevamente.")
                else:
                    st.error("❌ El nombre y el comentario son obligatorios.")
    
    with tab_ver_op:
        st.markdown("### Todas las Opiniones Aprobadas")
        opiniones = get_opiniones(aprobadas=True)
        
        if not opiniones.empty:
            for idx, op in opiniones.iterrows():
                stars = "⭐" * int(op['calificacion']) + "☆" * (5 - int(op['calificacion']))
                st.markdown(f"**👤 {op['usuario']}** {stars}")
                st.write(f"\"{op['comentario']}\"")
                st.caption(f"📅 {op['fecha']}")
                st.divider()
        else:
            st.info("No hay opiniones aprobadas aún. ¡Sé el primero en dar tu opinión!")

# --- PERSONAJES (TAB 8) ---
elif st.session_state.selected_tab == 8:
    st.title("👥 Personajes que hicieron historia")
    st.markdown("### 📋 Personajes Registrados")
    personajes = get_personajes()
    if not personajes.empty:
        for idx, p in personajes.iterrows():
            with st.expander(f"👤 {p['nombre']} - {p['fecha']}"):
                mostrar_imagen_segura(p.get('imagen_url'), 200)
                st.write(f"**Biografía:** {p['descripcion']}")
                mostrar_seccion_comentarios("personaje", p['id'], p['nombre'], es_admin)
    else:
        st.info("No hay personajes registrados")

# --- EL CRIMEN NO PAGA (TAB 9) ---
elif st.session_state.selected_tab == 9:
    st.title("⚖️ El Crimen No Paga")
    st.markdown("### Casos y noticias sobre justicia")
    crimenes = get_crimen_no_paga()
    if not crimenes.empty:
        for idx, c in crimenes.iterrows():
            with st.expander(f"⚖️ {c['titulo']} - {c['fecha']}"):
                if c.get('imagenes_url') and c['imagenes_url']:
                    if isinstance(c['imagenes_url'], list) and len(c['imagenes_url']) > 0:
                        mostrar_imagenes_en_fila(c['imagenes_url'], max_imagenes=3)
                    elif isinstance(c['imagenes_url'], str):
                        mostrar_imagen_segura(c['imagenes_url'], 200)
                st.write(f"**Descripción:** {c['descripcion']}")
                st.caption(f"📅 Publicado: {c['fecha']}")
                mostrar_seccion_comentarios("crimen", c['id'], c['titulo'], es_admin)
    else:
        st.info("No hay casos registrados")

# --- EFEMÉRIDES MÉDICAS (TAB 10) ---
elif st.session_state.selected_tab == 10:
    st.title("📅 Efemérides Médicas")
    fecha_actual_str = f"{ahora.day} de {meses[ahora.month-1]}"
    st.markdown(f"### 📌 {dias[ahora.weekday()]}, {fecha_actual_str} de {ahora.year}")
    col_ven, col_mundo = st.columns(2)
    with col_ven:
        st.markdown("#### 🇻🇪 Venezuela")
        efemerides_venezuela = {
            "24 de Junio": "Día del Médico Venezolano",
            "3 de Diciembre": "Día del Odontólogo Venezolano",
            "13 de Octubre": "Día del Trabajador de la Salud",
            "10 de Diciembre": "Día de la Enfermera Venezolana"
        }
        hoy_ven = None
        for fecha, texto in efemerides_venezuela.items():
            if fecha == fecha_actual_str:
                hoy_ven = texto
                break
        if hoy_ven:
            st.success(f"🎉 **¡HOY!** {fecha_actual_str}: {hoy_ven}")
        else:
            st.info(f"📌 Para hoy ({fecha_actual_str}) no hay efeméride médica registrada")
        st.markdown("**📅 Otras efemérides:**")
        for fecha, texto in efemerides_venezuela.items():
            st.markdown(f"- **{fecha}:** {texto}")
    with col_mundo:
        st.markdown("#### 🌎 Mundo")
        efemerides_mundo = {
            "12 de Mayo": "Día Internacional de la Enfermería",
            "7 de Abril": "Día Mundial de la Salud",
            "31 de Mayo": "Día Mundial sin Tabaco",
            "14 de Junio": "Día Mundial del Donante de Sangre",
            "10 de Octubre": "Día Mundial de la Salud Mental",
            "14 de Noviembre": "Día Mundial de la Diabetes"
        }
        hoy_mundo = None
        for fecha, texto in efemerides_mundo.items():
            if fecha == fecha_actual_str:
                hoy_mundo = texto
                break
        if hoy_mundo:
            st.success(f"🎉 **¡HOY!** {fecha_actual_str}: {hoy_mundo}")
        else:
            st.info(f"📌 Para hoy ({fecha_actual_str}) no hay efeméride médica mundial")
        st.markdown("**📅 Otras efemérides:**")
        for fecha, texto in efemerides_mundo.items():
            st.markdown(f"- **{fecha}:** {texto}")

# ============================================
# SECCIÓN: EVALUAR SÍNTOMAS (TAB 20)
# ============================================
elif st.session_state.selected_tab == 20:
    st.title("🩺 Evaluación de Síntomas - Diagnóstico Inteligente")
    
    st.markdown("""
    <div style="background: rgba(255, 0, 0, 0.15); border: 2px solid #FF6B6B; border-radius: 15px; padding: 20px; margin-bottom: 25px;">
        <div style="display: flex; align-items: center; gap: 15px;">
            <span style="font-size: 2.5em;">⚠️</span>
            <div>
                <h3 style="color: #FF6B6B; margin: 0;">ADVERTENCIA IMPORTANTE</h3>
                <p style="margin: 5px 0 0 0; color: #FFFFFF;">
                    Esta herramienta es <strong>SOLO INFORMATIVA</strong> y NO reemplaza una consulta médica profesional.
                    Los resultados son una guía preliminar basada en la información proporcionada.
                    <br><br>
                    <strong>SI TIENES UNA EMERGENCIA, LLAMA INMEDIATAMENTE AL 911 O ACUDE AL CENTRO DE SALUD MÁS CERCANO.</strong>
                </p>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    ### ¿Cómo funciona?
    1. Responde unas preguntas sobre tus síntomas (solo toma 3 minutos)
    2. Nuestro sistema analizará tus síntomas con una base de datos de más de 200 enfermedades
    3. Obtendrás un análisis probable de tu condición
    """)
    
    if 'cuestionario_paso' not in st.session_state:
        st.session_state.cuestionario_paso = 1
    if 'respuestas' not in st.session_state:
        st.session_state.respuestas = {}
    if 'historial_consultas' not in st.session_state:
        st.session_state.historial_consultas = []
    
    # PASO 1
    if st.session_state.cuestionario_paso == 1:
        with st.form("paso_1_consulta"):
            st.subheader("📋 Paso 1: Información Personal")
            
            col1, col2 = st.columns(2)
            with col1:
                edad = st.number_input("Edad", min_value=1, max_value=120, value=30, step=1)
            with col2:
                sexo = st.selectbox("Sexo biológico", ["Masculino", "Femenino", "Prefiero no decir"])
            
            peso = st.number_input("Peso aproximado (kg) - Opcional", min_value=10, max_value=300, value=70, step=1)
            altura = st.number_input("Altura aproximada (cm) - Opcional", min_value=50, max_value=250, value=170, step=1)
            
            condiciones = st.multiselect(
                "¿Tienes alguna condición médica preexistente?",
                ["Diabetes", "Hipertensión", "Asma", "Alergias", "Enfermedad cardíaca", "Depresión", "Ansiedad", "Artritis", "Ninguna", "Otra"]
            )
            
            submitted = st.form_submit_button("Siguiente →", use_container_width=True)
            if submitted:
                st.session_state.respuestas['edad'] = edad
                st.session_state.respuestas['sexo'] = sexo
                st.session_state.respuestas['peso'] = peso
                st.session_state.respuestas['altura'] = altura
                st.session_state.respuestas['condiciones'] = condiciones
                st.session_state.cuestionario_paso = 2
                st.rerun()
    
    # PASO 2
    elif st.session_state.cuestionario_paso == 2:
        with st.form("paso_2_consulta"):
            st.subheader("🩺 Paso 2: Cuéntanos tus síntomas")
            
            sintomas_seleccionados = st.multiselect(
                "Selecciona tus síntomas (puedes elegir varios):",
                SINTOMAS_COMPLETOS
            )
            
            otros_sintomas = st.text_input("¿Tienes algún síntoma adicional no listado? (Separado por comas)")
            
            if otros_sintomas:
                sintomas_adicionales = [s.strip() for s in otros_sintomas.split(",") if s.strip()]
                sintomas_seleccionados.extend(sintomas_adicionales)
            
            duracion = st.selectbox(
                "¿Cuánto tiempo llevas con estos síntomas?",
                ["Menos de 24 horas", "1-3 días", "4-7 días", "Más de una semana", "Más de un mes"]
            )
            
            intensidad = st.slider(
                "¿Cómo calificas la intensidad de los síntomas? (1 = Leve, 10 = Insoportable)",
                min_value=1, max_value=10, value=5
            )
            
            st.markdown("---")
            st.markdown("**Información adicional:**")
            
            medicamentos = st.text_input("¿Estás tomando algún medicamento? (Opcional)")
            alergias_med = st.text_input("¿Tienes alergias a medicamentos? (Opcional)")
            
            submitted = st.form_submit_button("Generar Diagnóstico", use_container_width=True)
            if submitted:
                if sintomas_seleccionados:
                    st.session_state.respuestas['sintomas'] = sintomas_seleccionados
                    st.session_state.respuestas['duracion'] = duracion
                    st.session_state.respuestas['intensidad'] = intensidad
                    st.session_state.respuestas['medicamentos'] = medicamentos
                    st.session_state.respuestas['alergias_med'] = alergias_med
                    st.session_state.cuestionario_paso = 3
                    st.rerun()
                else:
                    st.error("❌ Debes seleccionar al menos un síntoma.")
    
    # PASO 3
    elif st.session_state.cuestionario_paso == 3:
        st.subheader("📋 Análisis de Diagnóstico")
        st.markdown("*Basado en la información que proporcionaste.*")
        
        resp = st.session_state.respuestas
        sintomas = resp.get('sintomas', [])
        condiciones = resp.get('condiciones', [])
        edad = resp.get('edad', 30)
        sexo = resp.get('sexo', 'Femenino')
        
        diagnosticos = diagnosticar_enfermedades(sintomas, condiciones, edad, sexo)
        
        if diagnosticos:
            st.markdown("### 📊 Análisis Probable")
            st.markdown(f"**Síntomas analizados:** {len(sintomas)} síntomas")
            st.markdown(f"**Edad:** {edad} años | **Sexo:** {sexo}")
            
            st.markdown("---")
            
            for i, diag in enumerate(diagnosticos):
                nivel = diag["nivel"]
                color = diag["color"]
                
                if nivel == "Alta":
                    emoji = "🟢"
                    descripcion = "Alta coincidencia"
                elif nivel == "Media":
                    emoji = "🟡"
                    descripcion = "Coincidencia media"
                else:
                    emoji = "🟠"
                    descripcion = "Coincidencia baja"
                
                urgencia_emoji = "🔴" if diag["urgencia"] == "Alta" else "🟡" if diag["urgencia"] == "Media" else "🟢"
                
                with st.expander(f"#{i+1} Posible: {diag['enfermedad']} ({descripcion})"):
                    st.markdown(f"""
                    <div style="background: {color}20; border-left: 4px solid {color}; padding: 15px; border-radius: 8px;">
                        <h4 style="color: {color};">🔍 Posible {diag['enfermedad']}</h4>
                        <p><strong>Nivel de coincidencia:</strong> {emoji} {descripcion}</p>
                        <p><strong>Urgencia sugerida:</strong> {urgencia_emoji} {diag['urgencia']}</p>
                        <p><strong>Especialidad sugerida:</strong> {diag['especialidad']}</p>
                        <p><strong>Síntomas coincidentes:</strong> {', '.join(diag['sintomas_coincidentes'])}</p>
                        {f"<p><strong>Factores de riesgo:</strong> {', '.join(diag['factores_riesgo'])}</p>" if diag['factores_riesgo'] else ""}
                        <p><strong>Tratamiento sugerido:</strong> {diag['tratamiento']}</p>
                        <p><strong>Recomendaciones:</strong></p>
                        <ul>
                            {''.join([f'<li>{r}</li>' for r in diag['recomendaciones']])}
                        </ul>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("### 💡 Recomendaciones Generales")
            
            if any(d["urgencia"] == "Alta" for d in diagnosticos):
                st.warning("""
                ⚠️ **Se recomienda atención médica URGENTE.**
                Algunos de tus síntomas coinciden con condiciones que requieren evaluación médica inmediata.
                Por favor, acude a un centro de salud o llama al 911.
                """)
            elif any(d["urgencia"] == "Media" for d in diagnosticos):
                st.info("""
                🟡 **Se recomienda consulta médica PRONTO.**
                Tus síntomas sugieren condiciones que deben ser evaluadas por un especialista.
                Agenda una cita médica en los próximos días.
                """)
            else:
                st.success("""
                🟢 **Puedes manejar esto en casa.**
                Tus síntomas son leves y no sugieren condiciones graves. Descansa, hidrátate y monitorea tus síntomas.
                """)
            
            st.markdown("---")
            st.markdown("### 📋 Resumen para tu médico")
            st.info("""
            **Lleva esta información a tu consulta médica:**
            - Síntomas: {sintomas}
            - Duración: {duracion}
            - Intensidad: {intensidad}/10
            - Edad: {edad} años
            - Sexo: {sexo}
            - Medicamentos: {medicamentos}
            - Condiciones preexistentes: {condiciones}
            - Diagnósticos sugeridos: {diagnosticos}
            """.format(
                sintomas=', '.join(sintomas),
                duracion=resp.get('duracion', 'No especificada'),
                intensidad=resp.get('intensidad', 0),
                edad=edad,
                sexo=sexo,
                medicamentos=resp.get('medicamentos', 'Ninguno'),
                condiciones=', '.join(condiciones) if condiciones else 'Ninguna',
                diagnosticos=', '.join([d['enfermedad'] for d in diagnosticos[:3]])
            ))
            
            st.markdown("""
            <div style="background: rgba(255, 215, 0, 0.15); border: 2px solid #FFD700; border-radius: 10px; padding: 15px; margin: 20px 0;">
                <p style="text-align: center; margin: 0;">
                    <strong>⚠️ RECUERDA:</strong> Esta herramienta es solo informativa. 
                    Siempre consulta con un médico calificado para cualquier problema de salud.
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            consulta = {
                "fecha": ahora.strftime("%d/%m/%Y %H:%M"),
                "sintomas": len(sintomas),
                "diagnostico": diagnosticos[0]["enfermedad"] if diagnosticos else "Sin diagnóstico",
                "urgencia": diagnosticos[0]["urgencia"] if diagnosticos else "Baja"
            }
            st.session_state.historial_consultas.append(consulta)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("📥 Descargar Reporte", use_container_width=True):
                    st.info("Funcionalidad de descarga en desarrollo")
            with col2:
                if st.button("🔄 Nueva Consulta", use_container_width=True):
                    st.session_state.cuestionario_paso = 1
                    st.session_state.respuestas = {}
                    st.rerun()
            with col3:
                if st.button("📋 Ver Mi Historial", use_container_width=True):
                    st.session_state.ver_historial = True
                    st.rerun()
            
            if st.session_state.get('ver_historial', False):
                st.markdown("---")
                st.markdown("### 📋 Tu Historial de Consultas")
                if st.session_state.historial_consultas:
                    for h in st.session_state.historial_consultas:
                        st.markdown(f"- **{h['fecha']}** - {h['sintomas']} síntomas - {h['diagnostico']} ({h['urgencia']})")
                else:
                    st.info("No tienes consultas guardadas")
                if st.button("Ocultar Historial"):
                    st.session_state.ver_historial = False
                    st.rerun()
        else:
            st.warning("No se encontraron coincidencias significativas con las enfermedades en nuestra base de datos.")
            st.info("""
            **Posibles razones:**
            - Los síntomas seleccionados son muy generales
            - La combinación de síntomas es poco común
            - Podría tratarse de una condición no incluida en nuestra base de datos
            
            **Recomendación:** Consulta a un médico para una evaluación profesional.
            """)
            if st.button("🔄 Nueva Consulta", use_container_width=True):
                st.session_state.cuestionario_paso = 1
                st.session_state.respuestas = {}
                st.rerun()

# --- TAB 21: DIRECTORIO MÉDICO ---
elif st.session_state.selected_tab == 21:
    st.title("📍 Directorio Médico de Santa Teresa del Tuy")
    st.markdown("### Centros de salud, farmacias y especialistas locales")
    
    st.info("""
    ℹ️ **Información importante:**
    - Este directorio es colaborativo y se actualiza constantemente
    - Si conoces un centro de salud que no está listado, ¡puedes sugerirlo!
    - Los horarios y servicios pueden cambiar, verifica con el establecimiento
    """)
    
    for centro in DIRECTORIO_SALUD:
        with st.expander(f"{centro['tipo']}: {centro['nombre']}"):
            st.markdown(f"**Dirección:** {centro['direccion']}")
            st.markdown(f"**Teléfono:** {centro['telefono']}")
            st.markdown(f"**Horario:** {centro['horario']}")
            st.markdown(f"**Servicios:** {', '.join(centro['servicios'])}")
            st.caption(f"📍 Coordenadas aproximadas: {centro['coordenadas']}")
    
    st.markdown("---")
    st.markdown("### ➕ Sugerir un centro de salud")
    with st.form("sugerir_centro"):
        nombre_sug = st.text_input("Nombre del centro *")
        tipo_sug = st.selectbox("Tipo", ["Hospital", "Ambulatorio", "Farmacia", "Clínica Privada", "CDI", "Módulo de Salud", "Clínica Odontológica"])
        direccion_sug = st.text_area("Dirección *")
        telefono_sug = st.text_input("Teléfono")
        horario_sug = st.text_input("Horario")
        servicios_sug = st.text_input("Servicios que ofrece")
        
        submitted = st.form_submit_button("Enviar Sugerencia")
        if submitted:
            if nombre_sug and direccion_sug:
                st.success("✅ ¡Gracias! Tu sugerencia será revisada por el administrador.")
                st.balloons()
            else:
                st.error("❌ El nombre y la dirección son obligatorios")

# --- TAB 22: GUÍAS DE SALUD ---
elif st.session_state.selected_tab == 22:
    st.title("📚 Guías de Salud")
    st.markdown("### Información útil para el cuidado de tu salud")
    
    st.info("""
    ℹ️ **Nota importante:** Estas guías son educativas y no reemplazan el consejo médico profesional.
    """)
    
    guias = {
        "Primeros Auxilios Básicos": {
            "descripcion": "Qué hacer en situaciones de emergencia comunes",
            "contenido": """
            **🩹 Heridas y cortes:** Lava con agua y jabón, aplica presión con gasa, cubre con vendaje.
            **🔥 Quemaduras:** Enfría con agua fría 10-15 min, no apliques cremas, cubre con paño limpio.
            **🦴 Fracturas:** Inmoviliza, aplica hielo envuelto, busca atención médica inmediata.
            """
        },
        "Fiebre en Adultos": {
            "descripcion": "Cómo manejar la fiebre y cuándo preocuparse",
            "contenido": """
            **¿Qué es fiebre?** Temperatura > 38°C. Es un mecanismo de defensa.
            **Cuándo consultar:** Fiebre > 39.5°C, dura más de 3 días, acompañada de síntomas severos.
            **Recomendaciones:** Descansa, hidrátate, toma paracetamol según indicaciones.
            """
        },
        "Prevención de Enfermedades": {
            "descripcion": "Consejos para mantenerte saludable",
            "contenido": """
            **💧 Hidratación:** Bebe 2 litros de agua al día.
            **🍎 Alimentación:** Come frutas y verduras, reduce azúcar y grasas.
            **🏃 Ejercicio:** 30 minutos diarios de actividad moderada.
            **💤 Descanso:** Duerme 7-8 horas diarias.
            """
        },
        "Enfermedades Crónicas más Comunes": {
            "descripcion": "Información sobre condiciones de salud frecuentes",
            "contenido": """
            **🩸 Diabetes Tipo 2:** Control de glucosa, dieta balanceada, ejercicio, medicación.
            **❤️ Hipertensión:** Medir presión, reducir sal, mantener peso, evitar estrés.
            **🫁 EPOC:** Dejar de fumar, ejercicios respiratorios, evitar contaminantes.
            **🦴 Artrosis:** Ejercicio de bajo impacto, control de peso, fisioterapia.
            """
        }
    }
    
    for titulo, info in guias.items():
        with st.expander(f"📖 {titulo}"):
            st.markdown(f"**{info['descripcion']}**")
            st.markdown("---")
            st.markdown(info['contenido'])
    
    st.markdown("---")
    st.markdown("### 🏥 Recursos de Emergencia")
    st.markdown("""
    - **🚑 Emergencias Médicas:** 911
    - **🚒 Bomberos:** 0800-BOMBEROS
    - **🚨 Policía:** 911
    - **Hospital General de Santa Teresa:** 0212-XXX-XXXX
    """)

# --- TAB 23: PREGUNTA AL DOCTOR ---
elif st.session_state.selected_tab == 23:
    st.title("💬 Pregunta al Doctor")
    st.markdown("### Haz una pregunta sobre tu salud a nuestro equipo de expertos")
    
    st.info("""
    ⚠️ **Nota importante:** Las respuestas son orientativas y NO reemplazan una consulta médica presencial.
    """)
    
    if 'preguntas_doctor' not in st.session_state:
        st.session_state.preguntas_doctor = []
    if 'pregunta_actual' not in st.session_state:
        st.session_state.pregunta_actual = ""
    
    st.markdown("---")
    st.markdown("### 📝 Haz tu pregunta")
    st.caption("Escribe tu pregunta de salud de forma clara y detallada.")
    
    with st.form("form_pregunta_doctor"):
        nombre_pregunta = st.text_input("Tu nombre (opcional)")
        titulo_pregunta = st.text_input("Título de tu pregunta *")
        pregunta = st.text_area("Describe tu pregunta o inquietud de salud *", height=150)
        
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("📤 Enviar Pregunta", use_container_width=True)
        with col2:
            if st.form_submit_button("🤖 Respuesta Automática", use_container_width=True):
                if titulo_pregunta and pregunta:
                    respuesta_auto = responder_pregunta_medica(pregunta)
                    nueva_pregunta = {
                        "id": len(st.session_state.preguntas_doctor) + 1,
                        "nombre": nombre_pregunta if nombre_pregunta else "Anónimo",
                        "titulo": titulo_pregunta,
                        "pregunta": pregunta,
                        "fecha": ahora.strftime("%d/%m/%Y %H:%M"),
                        "respuesta": respuesta_auto,
                        "respondida": True,
                        "automatica": True
                    }
                    st.session_state.preguntas_doctor.append(nueva_pregunta)
                    st.success("✅ ¡Respuesta generada automáticamente!")
                    st.rerun()
                else:
                    st.error("❌ El título y la descripción son obligatorios.")
        
        if submitted:
            if titulo_pregunta and pregunta:
                nueva_pregunta = {
                    "id": len(st.session_state.preguntas_doctor) + 1,
                    "nombre": nombre_pregunta if nombre_pregunta else "Anónimo",
                    "titulo": titulo_pregunta,
                    "pregunta": pregunta,
                    "fecha": ahora.strftime("%d/%m/%Y %H:%M"),
                    "respuesta": None,
                    "respondida": False,
                    "automatica": False
                }
                st.session_state.preguntas_doctor.append(nueva_pregunta)
                st.success("✅ ¡Pregunta enviada! Un especialista la responderá pronto.")
                st.rerun()
            else:
                st.error("❌ El título y la descripción son obligatorios.")
    
    st.markdown("---")
    st.markdown("### 📋 Preguntas y respuestas")
    
    preguntas_respondidas = [p for p in st.session_state.preguntas_doctor if p['respondida']]
    preguntas_pendientes = [p for p in st.session_state.preguntas_doctor if not p['respondida']]
    
    if es_admin:
        st.markdown("#### 👨⚕️ Panel de Administración - Preguntas Pendientes")
        if preguntas_pendientes:
            for p in preguntas_pendientes:
                with st.container():
                    st.markdown(f"**ID: {p['id']}** - **{p['titulo']}**")
                    st.markdown(f"**👤 {p['nombre']}** *{p['fecha']}*")
                    st.markdown(f"**Pregunta:** {p['pregunta']}")
                    
                    if st.button(f"🤖 Generar Respuesta", key=f"gen_resp_{p['id']}"):
                        respuesta_auto = responder_pregunta_medica(p['pregunta'])
                        p['respuesta'] = respuesta_auto
                        p['respondida'] = True
                        p['automatica'] = True
                        st.success("✅ Respuesta generada")
                        st.rerun()
                    
                    with st.form(key=f"responder_pregunta_{p['id']}"):
                        respuesta = st.text_area("Respuesta del doctor", key=f"respuesta_{p['id']}")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.form_submit_button("✅ Responder", use_container_width=True):
                                if respuesta:
                                    p['respuesta'] = respuesta
                                    p['respondida'] = True
                                    st.success("✅ Respuesta publicada")
                                    st.rerun()
                                else:
                                    st.error("❌ Escribe una respuesta")
                        with col2:
                            if st.form_submit_button("🗑️ Eliminar", use_container_width=True):
                                st.session_state.preguntas_doctor.remove(p)
                                st.success("✅ Pregunta eliminada")
                                st.rerun()
                    st.divider()
        else:
            st.info("No hay preguntas pendientes")
        
        st.markdown("---")
        st.markdown("#### ✅ Preguntas Respondidas")
    else:
        st.markdown("#### ✅ Preguntas Respondidas")
    
    if preguntas_respondidas:
        for p in preguntas_respondidas:
            with st.expander(f"📝 {p['titulo']}"):
                st.markdown(f"**👤 {p['nombre']}** *{p['fecha']}*")
                st.markdown(f"**Pregunta:** {p['pregunta']}")
                st.markdown(f"**💬 Respuesta del Doctor:**")
                st.markdown(f"*{p['respuesta']}*")
                if p.get('automatica', False):
                    st.caption("🤖 Respuesta generada automáticamente (orientativa)")
                st.divider()
    else:
        st.info("No hay preguntas respondidas aún. ¡Sé el primero en preguntar!")

# ============================================
# PANEL ADMIN (COMPLETO)
# ============================================
if st.session_state.get('es_admin', False):
    admin_opt = st.session_state.get('admin_opt', "📰 Noticias")
    st.title("🔧 Panel de Administración")
    
    # --- GESTIONAR ENFERMEDADES ---
    if "🏥 GESTIONAR ENFERMEDADES" in admin_opt:
        st.subheader("🏥 Glosario de Enfermedades")
        st.markdown("### Base de datos de enfermedades para el diagnóstico")
        st.info("Desde aquí puedes agregar, modificar o eliminar enfermedades del glosario.")
        
        cargar_enfermedades_de_supabase()
        
        with st.expander("➕ AGREGAR NUEVA ENFERMEDAD", expanded=True):
            with st.form("form_agregar_enfermedad"):
                st.markdown("#### Información de la enfermedad")
                
                nombre_nuevo = st.text_input("Nombre de la enfermedad *")
                especialidad_nueva = st.text_input("Especialidad *")
                tratamiento_nuevo = st.text_area("Tratamiento sugerido *")
                sintomas_nuevos = st.text_area("Síntomas (separados por coma)")
                
                if st.form_submit_button("💾 Guardar Enfermedad"):
                    if nombre_nuevo and especialidad_nueva and tratamiento_nuevo:
                        sintomas_lista = [s.strip() for s in sintomas_nuevos.split(",") if s.strip()] if sintomas_nuevos else []
                        
                        nueva_enfermedad = {
                            "sintomas": sintomas_lista,
                            "factores_riesgo": [],
                            "especialidad": especialidad_nueva,
                            "urgencia": "Media",
                            "recomendaciones": [],
                            "tratamiento": tratamiento_nuevo,
                            "solo_mujeres": False
                        }
                        
                        if guardar_enfermedad_en_supabase(nombre_nuevo, nueva_enfermedad):
                            BASE_DATOS_ENFERMEDADES[nombre_nuevo] = nueva_enfermedad
                            st.success(f"✅ Enfermedad '{nombre_nuevo}' agregada correctamente")
                            st.rerun()
                        else:
                            st.error("❌ Error al guardar la enfermedad")
                    else:
                        st.error("❌ Los campos marcados con * son obligatorios")
        
        st.markdown("---")
        st.markdown("### 📋 Enfermedades registradas")
        st.markdown(f"**Total de enfermedades:** {len(BASE_DATOS_ENFERMEDADES)}")
        
        busqueda = st.text_input("🔍 Buscar enfermedad:", placeholder="Escribe el nombre de la enfermedad...")
        
        enfermedades_mostrar = BASE_DATOS_ENFERMEDADES
        if busqueda:
            enfermedades_mostrar = {k: v for k, v in BASE_DATOS_ENFERMEDADES.items() if busqueda.lower() in k.lower()}
        
        if enfermedades_mostrar:
            for nombre, info in list(enfermedades_mostrar.items())[:20]:
                with st.expander(f"📋 {nombre}", expanded=False):
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.markdown(f"**Especialidad:** {info['especialidad']}")
                        st.markdown(f"**Síntomas:** {', '.join(info['sintomas']) if info['sintomas'] else 'No especificados'}")
                        st.markdown(f"**Tratamiento sugerido:** {info['tratamiento']}")
                    with col2:
                        if st.button(f"✏️ Editar", key=f"edit_enf_{nombre}"):
                            st.session_state.edit_enfermedad = nombre
                            st.rerun()
                    with col3:
                        if st.button(f"🗑️ Eliminar", key=f"del_enf_{nombre}"):
                            if eliminar_enfermedad_de_supabase(nombre):
                                st.success(f"✅ Enfermedad '{nombre}' eliminada")
                                st.rerun()
                            else:
                                st.error("❌ Error al eliminar")
            
            if len(enfermedades_mostrar) > 20:
                st.info(f"Mostrando 20 de {len(enfermedades_mostrar)} enfermedades. Usa el buscador para filtrar.")
        else:
            st.info("No se encontraron enfermedades")
        
        if st.session_state.get('edit_enfermedad'):
            nombre_edit = st.session_state.edit_enfermedad
            info_edit = BASE_DATOS_ENFERMEDADES.get(nombre_edit)
            
            if info_edit:
                st.markdown("---")
                st.markdown(f"### ✏️ Editando: {nombre_edit}")
                with st.form("form_editar_enfermedad"):
                    nuevo_nombre = st.text_input("Nombre", value=nombre_edit)
                    nueva_especialidad = st.text_input("Especialidad", value=info_edit['especialidad'])
                    nuevo_tratamiento = st.text_area("Tratamiento sugerido", value=info_edit['tratamiento'])
                    nuevos_sintomas = st.text_area("Síntomas (separados por coma)", value=", ".join(info_edit['sintomas']) if info_edit['sintomas'] else "")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("💾 Guardar cambios"):
                            sintomas_lista = [s.strip() for s in nuevos_sintomas.split(",") if s.strip()] if nuevos_sintomas else []
                            
                            enfermedad_editada = {
                                "sintomas": sintomas_lista,
                                "factores_riesgo": [],
                                "especialidad": nueva_especialidad,
                                "urgencia": "Media",
                                "recomendaciones": [],
                                "tratamiento": nuevo_tratamiento,
                                "solo_mujeres": False
                            }
                            
                            if nuevo_nombre != nombre_edit:
                                eliminar_enfermedad_de_supabase(nombre_edit)
                            
                            if guardar_enfermedad_en_supabase(nuevo_nombre, enfermedad_editada):
                                if nuevo_nombre != nombre_edit and nombre_edit in BASE_DATOS_ENFERMEDADES:
                                    del BASE_DATOS_ENFERMEDADES[nombre_edit]
                                BASE_DATOS_ENFERMEDADES[nuevo_nombre] = enfermedad_editada
                                st.success("✅ Enfermedad actualizada correctamente")
                                del st.session_state.edit_enfermedad
                                st.rerun()
                            else:
                                st.error("❌ Error al guardar los cambios")
                    with col2:
                        if st.form_submit_button("❌ Cancelar"):
                            del st.session_state.edit_enfermedad
                            st.rerun()

    # --- GESTIONAR COMENTARIOS ---
    elif "💬 GESTIONAR COMENTARIOS" in admin_opt:
        st.subheader("💬 Gestión Centralizada de Comentarios")
        st.markdown("### Todos los comentarios de las crónicas")
        st.info("Desde aquí puedes modificar o eliminar cualquier comentario de las crónicas")
        
        comentarios = obtener_comentarios_todos(seccion="cronica")
        
        if comentarios.empty:
            st.info("No hay comentarios registrados en las crónicas")
        else:
            cronicas = get_cronicas()
            cronica_dict = {str(c['id']): c['titulo'] for idx, c in cronicas.iterrows()}
            
            st.markdown(f"**Total de comentarios:** {len(comentarios)}")
            
            if st.button("🗑️ ELIMINAR TODOS LOS COMENTARIOS", key="eliminar_todos_comentarios"):
                if st.session_state.get('confirmar_eliminar_todos', False):
                    for idx2, com in comentarios.iterrows():
                        eliminar_comentario(com['id'])
                    st.success(f"✅ Se eliminaron {len(comentarios)} comentarios")
                    st.session_state['confirmar_eliminar_todos'] = False
                    st.rerun()
                else:
                    st.session_state['confirmar_eliminar_todos'] = True
                    st.warning("⚠️ ¡CONFIRMAR! Haz clic nuevamente en ELIMINAR TODOS para confirmar")
            
            st.markdown("---")
            
            for idx, com in comentarios.iterrows():
                with st.container():
                    titulo_cronica = cronica_dict.get(str(com['item_id']), f"ID: {com['item_id']}")
                    
                    col1, col2, col3, col4 = st.columns([4, 2, 1, 1])
                    with col1:
                        st.markdown(f"**📖 Crónica:** {titulo_cronica}")
                        st.markdown(f"**👤 {com['usuario']}** *{com['fecha']}*")
                        text_key = f"text_com_central_{com['id']}_{idx}"
                        nuevo_texto = st.text_area(
                            "Comentario", 
                            value=com['comentario'], 
                            key=text_key,
                            label_visibility="collapsed"
                        )
                    with col2:
                        st.markdown(f"**ID:** {com['id']}")
                    with col3:
                        if st.button(f"💾 Guardar", key=f"guardar_central_{com['id']}_{idx}"):
                            texto_actualizado = st.session_state.get(text_key, com['comentario'])
                            if actualizar_comentario(com['id'], texto_actualizado):
                                st.success("✅ Comentario actualizado")
                                st.rerun()
                            else:
                                st.error("❌ Error al actualizar")
                    with col4:
                        if st.button(f"🗑️ Eliminar", key=f"eliminar_central_{com['id']}_{idx}"):
                            if eliminar_comentario(com['id']):
                                st.success("✅ Comentario eliminado")
                                st.rerun()
                            else:
                                st.error("❌ Error al eliminar")
                    st.divider()

    # --- NOTICIAS (ADMIN) ---
    elif "📰 Noticias" in admin_opt:
        st.subheader("📰 Gestionar Noticias")
        
        with st.expander("➕ CREAR nueva noticia", expanded=True):
            with st.form("fn"):
                titulo = st.text_input("Título *")
                categoria = st.selectbox("Categoría", ["Nacional", "Internacional", "Deportes", "Sucesos", "Farándula", "Reportajes"])
                contenido = st.text_area("Contenido *")
                imagen = st.file_uploader("Imagen (opcional)", type=["jpg", "png", "jpeg"])
                if st.form_submit_button("📤 Publicar Noticia"):
                    if titulo and contenido:
                        if add_noticia(titulo, categoria, contenido, imagen):
                            st.success("✅ Noticia guardada")
                            st.rerun()
                        else:
                            st.error("❌ Error al guardar noticia")
                    else:
                        st.error("❌ Título y contenido son obligatorios")
        
        st.markdown("---")
        st.markdown("### 📋 Noticias existentes")
        noticias = get_noticias()
        if not noticias.empty:
            for idx, n in noticias.iterrows():
                with st.expander(f"📰 {n['titulo']} - {n['categoria']} ({n['fecha']})"):
                    mostrar_imagen_segura(n.get('imagen_url'), 300)
                    st.write(f"**Contenido:** {n['contenido']}")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button(f"✏️ MODIFICAR", key=f"edit_noti_{n['id']}_{idx}"):
                            st.session_state.edit_noticia = n.to_dict()
                            st.rerun()
                    with col2:
                        if st.button(f"🗑️ ELIMINAR", key=f"del_noti_{n['id']}_{idx}"):
                            if delete_noticia(n['id']):
                                st.success("✅ Noticia eliminada")
                                st.rerun()
                    with col3:
                        if st.button(f"💬 COMENTARIOS", key=f"com_noti_{n['id']}_{idx}"):
                            st.session_state.gestionar_comentarios_noticia = n['id']
                            st.rerun()
                    
                    if st.session_state.get('gestionar_comentarios_noticia') == n['id']:
                        st.markdown("---")
                        st.markdown(f"### 💬 Comentarios de: {n['titulo']}")
                        comentarios = obtener_comentarios("noticia", n['id'])
                        if not comentarios.empty:
                            for idx2, com in comentarios.iterrows():
                                with st.container():
                                    st.markdown(f"**👤 {com['usuario']}** *{com['fecha']}*")
                                    st.markdown(f"💬 {com['comentario']}")
                                    if st.button(f"🗑️ Eliminar", key=f"del_com_noti_{com['id']}_{idx2}"):
                                        if eliminar_comentario(com['id']):
                                            st.success("Comentario eliminado")
                                            st.rerun()
                                    st.divider()
                        if st.button("❌ Cerrar", key=f"cerrar_com_noti_{n['id']}_{idx}"):
                            del st.session_state.gestionar_comentarios_noticia
                            st.rerun()
        else:
            st.info("No hay noticias registradas")
        
        if 'edit_noticia' in st.session_state:
            n = st.session_state.edit_noticia
            st.markdown("---")
            st.subheader(f"✏️ Modificando: {n['titulo']}")
            with st.form("edit_noticia_form"):
                nuevo_titulo = st.text_input("Título", value=n['titulo'])
                nueva_categoria = st.selectbox("Categoría", ["Nacional", "Internacional", "Deportes", "Sucesos", "Farándula", "Reportajes"], index=["Nacional", "Internacional", "Deportes", "Sucesos", "Farándula", "Reportajes"].index(n['categoria']))
                nuevo_contenido = st.text_area("Contenido", value=n['contenido'])
                nueva_imagen = st.file_uploader("Nueva imagen (opcional)", type=["jpg", "png", "jpeg"])
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Guardar cambios"):
                        if update_noticia(n['id'], nuevo_titulo, nueva_categoria, nuevo_contenido, nueva_imagen):
                            st.success("✅ Noticia actualizada")
                            del st.session_state.edit_noticia
                            st.rerun()
                with col2:
                    if st.form_submit_button("❌ Cancelar"):
                        del st.session_state.edit_noticia
                        st.rerun()

    # --- NEGOCIOS (ADMIN) ---
    elif "🏪 Negocios" in admin_opt:
        st.subheader("🏪 Gestionar Negocios")
        
        with st.expander("➕ CREAR nuevo negocio", expanded=True):
            with st.form("fneg"):
                nombre = st.text_input("Nombre del negocio *")
                resena = st.text_area("Reseña *")
                google_maps_url = st.text_input("Enlace Google Maps (opcional)", placeholder="https://maps.google.com/...")
                video_url = st.text_input("Enlace YouTube (opcional)", placeholder="https://www.youtube.com/watch?v=XXXXX")
                
                if video_url and video_url.strip():
                    video_id = extraer_video_id(video_url)
                    if video_id:
                        st.markdown("#### 📹 Vista previa del video")
                        st.video(f"https://www.youtube.com/embed/{video_id}")
                    else:
                        st.warning("⚠️ URL de YouTube no válida")
                
                imagenes = st.file_uploader("Fotos (máximo 3)", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
                if len(imagenes) > 3:
                    st.error("Máximo 3 fotos por negocio")
                elif st.form_submit_button("➕ Agregar Negocio"):
                    if nombre and resena:
                        if add_negocio(nombre, resena, google_maps_url, video_url, imagenes):
                            st.success("✅ Negocio agregado correctamente")
                            st.rerun()
                        else:
                            st.error("❌ Error al agregar negocio")
                    else:
                        st.error("❌ Nombre y reseña son obligatorios")
        
        st.markdown("---")
        st.markdown("### 📋 Negocios existentes")
        negocios = get_negocios()
        if not negocios.empty:
            for idx, n in negocios.iterrows():
                with st.expander(f"🏪 {n['nombre']}"):
                    if n.get('imagenes_url') and n['imagenes_url']:
                        if isinstance(n['imagenes_url'], list):
                            for img_url in n['imagenes_url']:
                                mostrar_imagen_segura(img_url, 200)
                        elif isinstance(n['imagenes_url'], str):
                            mostrar_imagen_segura(n['imagenes_url'], 200)
                    else:
                        st.caption("📷 Sin imágenes")
                    
                    st.write(f"**Reseña:** {n['resena']}")
                    
                    if n.get('video_url') and n['video_url']:
                        st.markdown("#### 🎥 Video actual")
                        mostrar_video_youtube(n['video_url'], width_percent=30)
                    
                    if n.get('google_maps_url') and n['google_maps_url']:
                        st.markdown(f"📍 [Ver en Google Maps]({n['google_maps_url']})")
                    
                    st.markdown("---")
                    st.markdown("#### 💬 Opiniones del negocio")
                    opiniones_neg = get_opiniones_negocio(n['id'])
                    if not opiniones_neg.empty:
                        for idx2, op in opiniones_neg.iterrows():
                            stars = "⭐" * int(op['calificacion']) + "☆" * (5 - int(op['calificacion']))
                            st.markdown(f"**👤 {op['usuario']}** {stars}")
                            st.write(f"\"{op['comentario']}\"")
                            st.caption(f"📅 {op['fecha']}")
                            if st.button(f"🗑️ Eliminar opinión", key=f"del_opinion_{op['id']}_{idx2}"):
                                if delete_opinion_negocio(op['id']):
                                    st.rerun()
                            st.divider()
                    else:
                        st.info("No hay opiniones para este negocio")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"✏️ MODIFICAR", key=f"edit_neg_{n['id']}_{idx}"):
                            st.session_state.edit_negocio = n.to_dict()
                            st.rerun()
                    with col2:
                        if st.button(f"🗑️ ELIMINAR", key=f"del_neg_{n['id']}_{idx}"):
                            if delete_negocio(n['id']):
                                st.success("✅ Negocio eliminado")
                                st.rerun()
        else:
            st.info("No hay negocios registrados")
        
        if 'edit_negocio' in st.session_state:
            n = st.session_state.edit_negocio
            st.markdown("---")
            st.subheader(f"✏️ Modificando: {n['nombre']}")
            with st.form("edit_negocio_form"):
                nuevo_nombre = st.text_input("Nombre", value=n['nombre'])
                nueva_resena = st.text_area("Reseña", value=n['resena'])
                nuevo_google_maps = st.text_input("Enlace Google Maps", value=n.get('google_maps_url', ''))
                nuevo_video = st.text_input("Enlace YouTube", value=n.get('video_url', ''))
                
                if nuevo_video and nuevo_video.strip():
                    video_id = extraer_video_id(nuevo_video)
                    if video_id:
                        st.markdown("#### 📹 Vista previa del video")
                        st.video(f"https://www.youtube.com/embed/{video_id}")
                    else:
                        st.warning("⚠️ URL de YouTube no válida")
                
                nuevas_imagenes = st.file_uploader("Nuevas fotos (opcional, máximo 3)", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Guardar cambios"):
                        if update_negocio(n['id'], nuevo_nombre, nueva_resena, nuevo_google_maps, nuevo_video, nuevas_imagenes):
                            st.success("✅ Negocio actualizado")
                            del st.session_state.edit_negocio
                            st.rerun()
                with col2:
                    if st.form_submit_button("❌ Cancelar"):
                        del st.session_state.edit_negocio
                        st.rerun()

    # --- REFLEXIONES (ADMIN) ---
    elif "💭 Reflexiones" in admin_opt:
        st.subheader("💭 Gestionar Reflexiones")
        
        with st.expander("➕ CREAR nueva reflexión", expanded=True):
            with st.form("fref"):
                titulo = st.text_input("Título *")
                versiculo = st.text_input("Versículo (opcional)")
                contenido = st.text_area("Contenido *")
                if st.form_submit_button("💾 Guardar como activa"):
                    if titulo and contenido:
                        if add_reflexion(titulo, contenido, versiculo):
                            st.success("✅ Reflexión guardada")
                            st.rerun()
                        else:
                            st.error("❌ Error al guardar")
                    else:
                        st.error("❌ Título y contenido son obligatorios")
        
        st.markdown("---")
        st.markdown("### 📋 Reflexiones existentes")
        reflexiones = get_reflexiones()
        if not reflexiones.empty:
            for idx, r in reflexiones.iterrows():
                with st.expander(f"📖 {r['titulo']} - {r['fecha']}"):
                    st.write(r['contenido'])
                    if r.get('versiculo'):
                        st.caption(f"📖 {r['versiculo']}")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button(f"✏️ MODIFICAR", key=f"edit_ref_admin_{r['id']}_{idx}"):
                            st.session_state.edit_reflexion = r.to_dict()
                            st.rerun()
                    with col2:
                        if st.button(f"🗑️ ELIMINAR", key=f"del_ref_admin_{r['id']}_{idx}"):
                            if delete_reflexion(r['id']):
                                st.success("✅ Reflexión eliminada")
                                st.rerun()
                    with col3:
                        if st.button(f"💬 COMENTARIOS", key=f"com_ref_{r['id']}_{idx}"):
                            st.session_state.gestionar_comentarios_reflexion = r['id']
                            st.rerun()
                    
                    if st.session_state.get('gestionar_comentarios_reflexion') == r['id']:
                        st.markdown("---")
                        st.markdown(f"### 💬 Comentarios de: {r['titulo']}")
                        comentarios = obtener_comentarios("reflexion", r['id'])
                        if not comentarios.empty:
                            for idx2, com in comentarios.iterrows():
                                with st.container():
                                    st.markdown(f"**👤 {com['usuario']}** *{com['fecha']}*")
                                    st.markdown(f"💬 {com['comentario']}")
                                    if st.button(f"🗑️ Eliminar", key=f"del_com_ref_{com['id']}_{idx2}"):
                                        if eliminar_comentario(com['id']):
                                            st.success("Comentario eliminado")
                                            st.rerun()
                                    st.divider()
                        if st.button("❌ Cerrar", key=f"cerrar_com_ref_{r['id']}_{idx}"):
                            del st.session_state.gestionar_comentarios_reflexion
                            st.rerun()
        else:
            st.info("No hay reflexiones registradas")
        
        if 'edit_reflexion' in st.session_state:
            r = st.session_state.edit_reflexion
            st.markdown("---")
            st.subheader(f"✏️ Modificando: {r['titulo']}")
            with st.form("edit_reflexion_admin_form"):
                nuevo_titulo = st.text_input("Título", value=r['titulo'])
                nuevo_versiculo = st.text_input("Versículo", value=r.get('versiculo', ''))
                nuevo_contenido = st.text_area("Contenido", value=r['contenido'])
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Guardar cambios"):
                        if update_reflexion(r['id'], nuevo_titulo, nuevo_contenido, nuevo_versiculo):
                            st.success("✅ Reflexión actualizada")
                            del st.session_state.edit_reflexion
                            st.rerun()
                with col2:
                    if st.form_submit_button("❌ Cancelar"):
                        del st.session_state.edit_reflexion
                        st.rerun()

    # --- CRÓNICAS (ADMIN) ---
    elif "📜 Crónicas" in admin_opt:
        st.subheader("📜 Gestionar Crónicas")
        
        with st.expander("➕ CREAR nueva crónica", expanded=True):
            with st.form("fcronica_admin"):
                titulo = st.text_input("Título *")
                lugar = st.text_input("Lugar *")
                estado = st.selectbox("Estado", ["Miranda", "Carabobo", "Distrito Capital", "Zulia", "Lara", "Aragua", "Bolivar", "Anzoategui", "Merida", "Tachira", "Nueva Esparta", "Sucre", "Falcon", "Barinas", "Portuguesa", "Guarico", "Cojedes", "Trujillo", "Yaracuy", "Apure", "Amazonas", "Delta Amacuro", "Vargas"])
                contenido = st.text_area("Contenido *")
                imagenes = st.file_uploader("Fotos (máximo 3)", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
                if len(imagenes) > 3:
                    st.error("Máximo 3 fotos por crónica")
                elif st.form_submit_button("➕ Agregar Crónica"):
                    if titulo and lugar and contenido:
                        if add_cronica(titulo, contenido, lugar, estado, imagenes):
                            st.success("✅ Crónica agregada correctamente")
                            st.rerun()
                        else:
                            st.error("❌ Error al agregar crónica")
                    else:
                        st.error("❌ Título, lugar y contenido son obligatorios")
        
        st.markdown("---")
        st.markdown("### 📋 Crónicas existentes")
        cronicas = get_cronicas()
        if not cronicas.empty:
            for idx, c in cronicas.iterrows():
                with st.expander(f"📖 {c['titulo']} - {c['lugar']}, {c['estado']}"):
                    if c.get('imagenes_url') and c['imagenes_url']:
                        if isinstance(c['imagenes_url'], list):
                            for img_url in c['imagenes_url']:
                                mostrar_imagen_segura(img_url, 200)
                        elif isinstance(c['imagenes_url'], str):
                            mostrar_imagen_segura(c['imagenes_url'], 200)
                    st.write(f"**Contenido:** {c['contenido']}")
                    st.caption(f"📅 {c['fecha']}")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button(f"✏️ MODIFICAR", key=f"edit_cron_admin_{c['id']}_{idx}"):
                            st.session_state.edit_cronica = c.to_dict()
                            st.rerun()
                    with col2:
                        if st.button(f"🗑️ ELIMINAR", key=f"del_cron_admin_{c['id']}_{idx}"):
                            if delete_cronica(c['id']):
                                st.success("✅ Crónica eliminada")
                                st.rerun()
                    with col3:
                        if st.button(f"💬 COMENTARIOS", key=f"com_cron_{c['id']}_{idx}"):
                            st.session_state.gestionar_comentarios_cronica = c['id']
                            st.rerun()
                    
                    if st.session_state.get('gestionar_comentarios_cronica') == c['id']:
                        st.markdown("---")
                        st.markdown(f"### 💬 Comentarios de: {c['titulo']}")
                        comentarios = obtener_comentarios("cronica", c['id'])
                        if not comentarios.empty:
                            for idx2, com in comentarios.iterrows():
                                with st.container():
                                    st.markdown(f"**👤 {com['usuario']}** *{com['fecha']}*")
                                    st.markdown(f"💬 {com['comentario']}")
                                    if st.button(f"🗑️ Eliminar", key=f"del_com_cron_{com['id']}_{idx2}"):
                                        if eliminar_comentario(com['id']):
                                            st.success("Comentario eliminado")
                                            st.rerun()
                                    st.divider()
                        if st.button("❌ Cerrar", key=f"cerrar_com_cron_{c['id']}_{idx}"):
                            del st.session_state.gestionar_comentarios_cronica
                            st.rerun()
        else:
            st.info("No hay crónicas registradas")
        
        if 'edit_cronica' in st.session_state:
            c = st.session_state.edit_cronica
            st.markdown("---")
            st.subheader(f"✏️ Modificando: {c['titulo']}")
            with st.form("edit_cronica_admin_form"):
                nuevo_titulo = st.text_input("Título", value=c['titulo'])
                nuevo_lugar = st.text_input("Lugar", value=c['lugar'])
                nuevo_estado = st.selectbox("Estado", ["Miranda", "Carabobo", "Distrito Capital", "Zulia", "Lara", "Aragua", "Bolivar", "Anzoategui", "Merida", "Tachira", "Nueva Esparta", "Sucre", "Falcon", "Barinas", "Portuguesa", "Guarico", "Cojedes", "Trujillo", "Yaracuy", "Apure", "Amazonas", "Delta Amacuro", "Vargas"], index=["Miranda", "Carabobo", "Distrito Capital", "Zulia", "Lara", "Aragua", "Bolivar", "Anzoategui", "Merida", "Tachira", "Nueva Esparta", "Sucre", "Falcon", "Barinas", "Portuguesa", "Guarico", "Cojedes", "Trujillo", "Yaracuy", "Apure", "Amazonas", "Delta Amacuro", "Vargas"].index(c['estado']))
                nuevo_contenido = st.text_area("Contenido", value=c['contenido'])
                nuevas_imagenes = st.file_uploader("Nuevas fotos (opcional, máximo 3)", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Guardar cambios"):
                        if update_cronica(c['id'], nuevo_titulo, nuevo_contenido, nuevo_lugar, nuevo_estado, nuevas_imagenes):
                            st.success("✅ Crónica actualizada")
                            del st.session_state.edit_cronica
                            st.rerun()
                with col2:
                    if st.form_submit_button("❌ Cancelar"):
                        del st.session_state.edit_cronica
                        st.rerun()

    # --- VIDEOS (ADMIN) ---
    elif "🎬 Videos" in admin_opt:
        st.subheader("🎬 Gestionar Videos")
        st.info("📌 Sube tu video a YouTube y pega la URL aquí")
        
        with st.expander("➕ CREAR nuevo video", expanded=True):
            with st.form("fvid"):
                titulo = st.text_input("Título del video *")
                url_youtube = st.text_input("URL de YouTube *", placeholder="https://www.youtube.com/watch?v=XXXXX")
                if url_youtube and url_youtube.strip():
                    video_id = extraer_video_id(url_youtube)
                    if video_id:
                        st.video(f"https://www.youtube.com/embed/{video_id}")
                    else:
                        st.warning("⚠️ URL no válida")
                if st.form_submit_button("📤 Agregar Video"):
                    if titulo and url_youtube:
                        if add_video(titulo, url_youtube):
                            st.rerun()
                    else:
                        st.error("❌ Título y URL son obligatorios")
        
        st.markdown("---")
        st.markdown("### 📋 Videos existentes")
        videos = get_videos()
        if not videos.empty:
            for idx, v in videos.iterrows():
                with st.expander(f"🎬 {v['titulo']}"):
                    mostrar_video_youtube(v['video_url'], width_percent=50)
                    st.caption(f"📅 {v['fecha']}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"✏️ MODIFICAR", key=f"edit_vid_{v['id']}_{idx}"):
                            st.session_state.edit_video = v.to_dict()
                            st.rerun()
                    with col2:
                        if st.button(f"🗑️ ELIMINAR", key=f"del_vid_{v['id']}_{idx}"):
                            if delete_video(v['id']):
                                st.success("✅ Video eliminado")
                                st.rerun()
        else:
            st.info("No hay videos registrados")
        
        if 'edit_video' in st.session_state:
            v = st.session_state.edit_video
            st.markdown("---")
            st.subheader(f"✏️ Modificando: {v['titulo']}")
            with st.form("edit_video_form"):
                nuevo_titulo = st.text_input("Título", value=v['titulo'])
                nueva_url = st.text_input("URL de YouTube", value=v['video_url'])
                if nueva_url:
                    video_id = extraer_video_id(nueva_url)
                    if video_id:
                        st.video(f"https://www.youtube.com/embed/{video_id}")
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Guardar cambios"):
                        if update_video(v['id'], nuevo_titulo, nueva_url):
                            st.success("✅ Video actualizado")
                            del st.session_state.edit_video
                            st.rerun()
                with col2:
                    if st.form_submit_button("❌ Cancelar"):
                        del st.session_state.edit_video
                        st.rerun()

    # --- TIKTOK (ADMIN) ---
    elif "📱 TikTok" in admin_opt:
        st.subheader("📱 Gestionar Videos de TikTok")
        
        with st.expander("➕ CREAR nuevo TikTok", expanded=True):
            with st.form("ftik"):
                titulo = st.text_input("Título del video *")
                url_tiktok = st.text_input("URL de TikTok *", placeholder="https://www.tiktok.com/@usuario/video/123456789")
                if st.form_submit_button("📤 Agregar TikTok"):
                    if titulo and url_tiktok:
                        if add_tiktok(titulo, url_tiktok):
                            st.rerun()
                    else:
                        st.error("❌ Título y URL son obligatorios")
        
        st.markdown("---")
        st.markdown("### 📋 TikToks existentes")
        tiktoks = get_tiktoks()
        if not tiktoks.empty:
            for idx, t in tiktoks.iterrows():
                with st.expander(f"📱 {t['titulo']}"):
                    mostrar_tiktok(t['tiktok_url'], width_percent=50)
                    st.caption(f"📅 {t['fecha']}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"✏️ MODIFICAR", key=f"edit_tik_{t['id']}_{idx}"):
                            st.session_state.edit_tiktok = t.to_dict()
                            st.rerun()
                    with col2:
                        if st.button(f"🗑️ ELIMINAR", key=f"del_tik_{t['id']}_{idx}"):
                            if delete_tiktok(t['id']):
                                st.success("✅ TikTok eliminado")
                                st.rerun()
        else:
            st.info("No hay TikToks registrados")
    
    # --- MUSICA (ADMIN) ---
    elif "🎵 Música" in admin_opt:
        st.subheader("🎵 Gestionar Música")
        st.info("📌 Sube tu música desde tu laptop (formato MP3)")
        
        with st.expander("➕ CREAR nueva canción", expanded=True):
            with st.form("fmus"):
                titulo = st.text_input("Título de la canción *")
                audio_file = st.file_uploader("Archivo de audio (MP3) *", type=["mp3"])
                if st.form_submit_button("📤 Agregar Música"):
                    if titulo and audio_file:
                        if add_musica(titulo, audio_file):
                            st.rerun()
                        else:
                            st.error("❌ Error al agregar música")
                    else:
                        st.error("❌ Título y archivo de audio son obligatorios")
        
        st.markdown("---")
        st.markdown("### 📋 Canciones existentes")
        musicas = get_musicas()
        if not musicas.empty:
            for idx, m in musicas.iterrows():
                with st.expander(f"🎵 {m['titulo']}"):
                    if m.get('audio_url') and m['audio_url']:
                        st.audio(m['audio_url'], format="audio/mp3")
                        st.caption(f"📅 {m['fecha']}")
                    else:
                        st.warning("No hay URL de audio disponible")
                    mostrar_seccion_comentarios("musica", m['id'], m['titulo'], es_admin)
        else:
            st.info("No hay canciones registradas")
        
        if 'edit_musica' in st.session_state:
            m = st.session_state.edit_musica
            st.markdown("---")
            st.subheader(f"✏️ Modificando: {m['titulo']}")
            with st.form("edit_musica_form"):
                nuevo_titulo = st.text_input("Título", value=m['titulo'])
                nuevo_audio = st.file_uploader("Nuevo archivo de audio (opcional)", type=["mp3"])
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Guardar cambios"):
                        if update_musica(m['id'], nuevo_titulo, nuevo_audio):
                            st.success("✅ Música actualizada")
                            del st.session_state.edit_musica
                            st.rerun()
                with col2:
                    if st.form_submit_button("❌ Cancelar"):
                        del st.session_state.edit_musica
                        st.rerun()
    
    # --- DENUNCIAS (ADMIN) ---
    elif "⚠️ Denuncias" in admin_opt:
        st.subheader("⚠️ Gestionar Denuncias")
        
        denuncias = get_denuncias()
        if not denuncias.empty:
            for idx, d in denuncias.iterrows():
                with st.expander(f"📌 {d['titulo']} - {d['estatus']}"):
                    st.write(f"**Denunciante:** {d['denunciante']}")
                    st.write(f"**Descripción:** {d['descripcion']}")
                    st.write(f"**Ubicación:** {d['ubicacion']}")
                    st.caption(f"📅 {d['fecha']}")
                    
                    nuevo_estado = st.selectbox("Cambiar estado:", ["Pendiente", "En revisión", "Resuelta", "Descartada"], 
                                               index=["Pendiente", "En revisión", "Resuelta", "Descartada"].index(d['estatus']),
                                               key=f"est_{d['id']}_{idx}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Actualizar estado", key=f"upd_{d['id']}_{idx}"):
                            if update_denuncia_status(d['id'], nuevo_estado):
                                st.success("Estado actualizado")
                                st.rerun()
                    with col2:
                        if st.button("🗑️ ELIMINAR denuncia", key=f"del_den_{d['id']}_{idx}"):
                            if delete_denuncia(d['id']):
                                st.success("Denuncia eliminada")
                                st.rerun()
        else:
            st.info("No hay denuncias registradas")
    
    # --- OPINIONES GENERALES (ADMIN) ---
    elif "💬 Opiniones" in admin_opt:
        st.subheader("💬 Gestionar Opiniones")
        
        st.markdown("### ⏳ Opiniones pendientes de aprobar")
        opiniones_pendientes = get_opiniones(aprobadas=False)
        if not opiniones_pendientes.empty:
            for idx, op in opiniones_pendientes.iterrows():
                if not op['aprobada']:
                    with st.expander(f"👤 {op['usuario']} - {op['calificacion']}⭐"):
                        st.write(f"**Comentario:** {op['comentario']}")
                        st.caption(f"📅 {op['fecha']}")
                        col1, col2 = st.columns(2)
                        with col1:
                            if st.button("✅ APROBAR", key=f"aprob_{op['id']}_{idx}"):
                                if approve_opinion(op['id']):
                                    st.success("Opinión aprobada")
                                    st.rerun()
                        with col2:
                            if st.button("🗑️ ELIMINAR", key=f"del_op_{op['id']}_{idx}"):
                                if delete_opinion(op['id']):
                                    st.success("Opinión eliminada")
                                    st.rerun()
        else:
            st.info("No hay opiniones pendientes")
        
        st.markdown("---")
        st.markdown("### ✅ Opiniones aprobadas")
        opiniones_aprobadas = get_opiniones(aprobadas=True)
        if not opiniones_aprobadas.empty:
            for idx, op in opiniones_aprobadas.iterrows():
                with st.expander(f"👤 {op['usuario']} - {op['calificacion']}⭐"):
                    st.write(f"**Comentario:** {op['comentario']}")
                    st.caption(f"📅 {op['fecha']}")
                    if st.button("🗑️ ELIMINAR", key=f"del_op_aprob_{op['id']}_{idx}"):
                        if delete_opinion(op['id']):
                            st.success("Opinión eliminada")
                            st.rerun()
        else:
            st.info("No hay opiniones aprobadas")
    
    # --- PERSONAJES (ADMIN) ---
    elif "👥 Personajes" in admin_opt:
        st.subheader("👥 Gestionar Personajes")
        
        with st.expander("➕ CREAR nuevo personaje", expanded=True):
            with st.form("fpersonaje_admin"):
                nombre = st.text_input("Nombre del personaje *")
                fecha_personaje = st.date_input("Fecha a mostrar", value=datetime.now().date())
                descripcion = st.text_area("Biografía *")
                imagen = st.file_uploader("Imagen", type=["jpg", "png", "jpeg"])
                if st.form_submit_button("💾 Guardar Personaje"):
                    if nombre and descripcion:
                        if add_personaje(nombre, descripcion, imagen, fecha_personaje.strftime("%d/%m/%Y")):
                            st.success("✅ Personaje guardado")
                            st.rerun()
                        else:
                            st.error("❌ Error al guardar")
                    else:
                        st.error("❌ Nombre y biografía obligatorios")
        
        st.markdown("---")
        st.markdown("### 📋 Personajes Registrados")
        personajes = get_personajes()
        if not personajes.empty:
            for idx, p in personajes.iterrows():
                with st.expander(f"👤 {p['nombre']} - {p['fecha']}"):
                    mostrar_imagen_segura(p.get('imagen_url'), 150)
                    st.write(f"**Biografía:** {p['descripcion']}")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button(f"✏️ MODIFICAR", key=f"edit_pers_{p['id']}_{idx}"):
                            st.session_state.edit_personaje = p.to_dict()
                            st.rerun()
                    with col2:
                        if st.button(f"🗑️ ELIMINAR", key=f"del_pers_{p['id']}_{idx}"):
                            if delete_personaje(p['id']):
                                st.success(f"✅ {p['nombre']} eliminado")
                                st.rerun()
                    with col3:
                        if st.button(f"⭐ DESTACAR HOY", key=f"destacar_pers_{p['id']}_{idx}"):
                            if update_personaje(p['id'], p['nombre'], p['descripcion'], None, datetime.now().strftime("%d/%m/%Y")):
                                st.success(f"✅ {p['nombre']} será el personaje destacado")
                                st.rerun()
        else:
            st.info("No hay personajes registrados")
        
        if 'edit_personaje' in st.session_state:
            p = st.session_state.edit_personaje
            st.markdown("---")
            st.subheader(f"✏️ Modificando: {p['nombre']}")
            with st.form("edit_personaje_form"):
                nuevo_nombre = st.text_input("Nombre", value=p['nombre'])
                try:
                    fecha_default = datetime.strptime(p['fecha'], "%d/%m/%Y").date()
                except:
                    fecha_default = datetime.now().date()
                nueva_fecha = st.date_input("Fecha", value=fecha_default)
                nueva_descripcion = st.text_area("Biografía", value=p['descripcion'])
                nueva_imagen = st.file_uploader("Nueva imagen (opcional)", type=["jpg", "png", "jpeg"])
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Guardar cambios"):
                        if update_personaje(p['id'], nuevo_nombre, nueva_descripcion, nueva_imagen, nueva_fecha.strftime("%d/%m/%Y")):
                            st.success("✅ Personaje actualizado")
                            del st.session_state.edit_personaje
                            st.rerun()
                with col2:
                    if st.form_submit_button("❌ Cancelar"):
                        del st.session_state.edit_personaje
                        st.rerun()
    
    # --- EL CRIMEN NO PAGA (ADMIN) ---
    elif "⚖️ El Crimen No Paga" in admin_opt:
        st.subheader("⚖️ Gestionar El Crimen No Paga")
        
        with st.expander("➕ CREAR nuevo caso", expanded=True):
            with st.form("fcrimen"):
                titulo = st.text_input("Título del caso *")
                descripcion = st.text_area("Descripción *")
                imagenes = st.file_uploader("Fotos (máximo 3)", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
                if len(imagenes) > 3:
                    st.error("Máximo 3 fotos por caso")
                elif st.form_submit_button("➕ Agregar Caso"):
                    if titulo and descripcion:
                        if add_crimen_no_paga(titulo, descripcion, imagenes):
                            st.success("✅ Caso agregado correctamente")
                            st.rerun()
                        else:
                            st.error("❌ Error al agregar caso")
                    else:
                        st.error("❌ Título y descripción son obligatorios")
        
        st.markdown("---")
        st.markdown("### 📋 Casos existentes")
        crimenes = get_crimen_no_paga()
        if not crimenes.empty:
            for idx, c in crimenes.iterrows():
                with st.expander(f"⚖️ {c['titulo']} - {c['fecha']}"):
                    if c.get('imagenes_url') and c['imagenes_url']:
                        if isinstance(c['imagenes_url'], list):
                            for img_url in c['imagenes_url']:
                                mostrar_imagen_segura(img_url, 200)
                        elif isinstance(c['imagenes_url'], str):
                            mostrar_imagen_segura(c['imagenes_url'], 200)
                    st.write(f"**Descripción:** {c['descripcion']}")
                    st.caption(f"📅 Publicado: {c['fecha']}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"✏️ MODIFICAR", key=f"edit_crimen_{c['id']}_{idx}"):
                            st.session_state.edit_crimen = c.to_dict()
                            st.rerun()
                    with col2:
                        if st.button(f"🗑️ ELIMINAR", key=f"del_crimen_{c['id']}_{idx}"):
                            if delete_crimen_no_paga(c['id']):
                                st.success("✅ Caso eliminado")
                                st.rerun()
        else:
            st.info("No hay casos registrados")
        
        if 'edit_crimen' in st.session_state:
            c = st.session_state.edit_crimen
            st.markdown("---")
            st.subheader(f"✏️ Modificando: {c['titulo']}")
            with st.form("edit_crimen_form"):
                nuevo_titulo = st.text_input("Título", value=c['titulo'])
                nueva_descripcion = st.text_area("Descripción", value=c['descripcion'])
                nuevas_imagenes = st.file_uploader("Nuevas fotos (opcional, máximo 3)", type=["jpg", "png", "jpeg"], accept_multiple_files=True)
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Guardar cambios"):
                        if update_crimen_no_paga(c['id'], nuevo_titulo, nueva_descripcion, nuevas_imagenes):
                            st.success("✅ Caso actualizado")
                            del st.session_state.edit_crimen
                            st.rerun()
                with col2:
                    if st.form_submit_button("❌ Cancelar"):
                        del st.session_state.edit_crimen
                        st.rerun()
    
    # --- CONFIGURACION ---
    elif "⚙️ Configuración" in admin_opt:
        st.subheader("⚙️ Configuración del Sistema")
        
        st.markdown("### ❤️ Estadísticas de Me gusta")
        col_est1, col_est2, col_est3 = st.columns(3)
        total_likes_admin = obtener_total_likes()
        likes_reales_admin = obtener_likes_reales()
        likes_auto_admin = obtener_likes_automaticos()
        
        with col_est1:
            st.metric("👍 Total Me gusta", f"{total_likes_admin:,}")
        with col_est2:
            st.metric("👤 Likes reales", f"{likes_reales_admin:,}")
        with col_est3:
            st.metric("🤖 Likes automáticos", f"{likes_auto_admin:,}")
        
        st.markdown("---")
        st.markdown("### 👥 Estadísticas de Visitantes")
        visitas_admin = get_visitas()
        st.metric("🚪 Total Visitantes", f"{visitas_admin:,}")
        st.caption("💡 Cada 20 visitas se agregan 2 likes automáticos")
        
        st.markdown("---")
        st.markdown("### 💬 Estadísticas de Comentarios")
        try:
            response = supabase.table("comentarios").select("*", count="exact").execute()
            total_comentarios = response.count if response.count else 0
            st.metric("📝 Total Comentarios", total_comentarios)
        except:
            st.info("No hay comentarios registrados")
        
        st.markdown("---")
        st.markdown("### 💵 Tipo de Cambio Dólar BCV")
        dolar_actual = get_dolar()
        st.metric("Valor actual", f"{dolar_actual:.2f} Bs")
        nuevo_dolar = st.number_input("Nuevo valor:", value=float(dolar_actual), step=0.01, format="%.2f")
        if st.button("💾 Actualizar Dólar", key="btn_dolar_admin"):
            if actualizar_dolar_manual(nuevo_dolar):
                st.success("✅ Dólar actualizado correctamente")
                st.rerun()
            else:
                st.error("❌ Error al actualizar")
        
        st.markdown("---")
        st.markdown("### 🖼️ Logo de la aplicación")
        logo_actual = get_logo()
        if logo_actual:
            st.image(logo_actual, width=150)
        nuevo_logo = st.file_uploader("Subir nuevo logo", type=["png", "jpg", "jpeg"])
        if nuevo_logo and st.button("💾 Guardar Logo", key="btn_logo"):
            url_logo = subir_imagen_storage(nuevo_logo, "logo")
            if url_logo:
                if save_logo(url_logo):
                    st.success("✅ Logo guardado")
                    st.rerun()
                else:
                    st.error("❌ Error al guardar logo")
    
    # --- TIENDA ONLINE (ADMIN) ---
    elif "🛍️ Tu Tienda Online" in admin_opt:
        st.subheader("🛍️ Willian'Variedades - Tienda Online")
        
        CATEGORIAS = {
            "Bisutería": ["Collares", "Pulseras", "Aretes", "Anillos", "Diademas", "Todas"],
            "Hogar": ["Enchufes", "Lámparas", "Utensilios de cocina", "Organizadores", "Todas"],
            "Papelería": ["Lápices", "Creyones", "Cuadernos", "Marcadores", "Borradores", "Todas"],
            "Salud": ["Tensiómetros", "Balanzas electrónicas", "Termómetros", "Todas"],
            "Electrónica": ["Cables", "Adaptadores", "Pilas", "Cargadores", "Todas"]
        }
        CATEGORIAS_LISTA = list(CATEGORIAS.keys())
        
        with st.expander("➕ AGREGAR PRODUCTO", expanded=True):
            with st.form("form_producto"):
                st.markdown("#### Datos del producto")
                
                nombre = st.text_input("Nombre del producto *")
                descripcion = st.text_area("Descripción *")
                
                col1, col2 = st.columns(2)
                with col1:
                    categoria = st.selectbox("Categoría *", CATEGORIAS_LISTA)
                    subcategoria_options = CATEGORIAS.get(categoria, [])
                    subcategoria = st.selectbox("Subcategoría *", [s for s in subcategoria_options if s != "Todas"])
                with col2:
                    precio_usd = st.number_input("Precio en dólares ($) *", min_value=0.01, step=0.01, format="%.2f")
                    cantidad = st.number_input("Cantidad en stock *", min_value=0, step=1, value=10)
                
                imagen = st.file_uploader("Imagen del producto", type=["jpg", "png", "jpeg"])
                
                if precio_usd > 0:
                    st.info(f"💰 Precio en Bolívares: **{precio_usd * dolar:,.2f} Bs** (Tasa: {dolar:.2f} Bs/$)")
                
                if st.form_submit_button("💾 Agregar Producto"):
                    if nombre and descripcion and categoria and subcategoria and precio_usd > 0:
                        if add_producto(nombre, descripcion, precio_usd, categoria, subcategoria, imagen, cantidad):
                            st.success("✅ Producto agregado correctamente")
                            st.rerun()
                        else:
                            st.error("❌ Error al agregar producto")
                    else:
                        st.error("❌ Todos los campos marcados con * son obligatorios")
        
        st.markdown("---")
        st.markdown("### 📋 Productos Registrados")
        
        productos_admin = get_productos()
        if not productos_admin.empty:
            st.markdown(f"**Total de productos:** {len(productos_admin)}")
            
            for idx, p in productos_admin.iterrows():
                with st.expander(f"📦 {p['nombre']} - {p['categoria']} › {p['subcategoria']}"):
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        if p.get('imagen_url') and p['imagen_url']:
                            try:
                                st.image(p['imagen_url'], width=200)
                            except:
                                st.caption("🖼️ Imagen no disponible")
                        else:
                            st.caption("🖼️ Sin imagen")
                        
                        st.markdown(f"**Descripción:** {p.get('descripcion', 'Sin descripción')}")
                        precio_bs = p['precio'] * dolar
                        st.markdown(f"**💰 Precio:** {precio_bs:,.2f} Bs (${p['precio']:.2f})")
                        st.markdown(f"**📦 Stock:** {p.get('cantidad', 0)} unidades")
                        st.caption(f"📅 Publicado: {p.get('fecha', 'Fecha no disponible')}")
                    
                    with col2:
                        if st.button(f"✏️ Editar", key=f"edit_prod_{p['id']}_{idx}"):
                            st.session_state.edit_producto = p.to_dict()
                            st.rerun()
                        if st.button(f"🗑️ Eliminar", key=f"del_prod_{p['id']}_{idx}"):
                            if delete_producto(p['id']):
                                st.success("✅ Producto eliminado")
                                st.rerun()
                        
                        if st.button(f"💬 Comentarios", key=f"com_prod_{p['id']}_{idx}"):
                            st.session_state.gestionar_comentarios_producto = p['id']
                            st.rerun()
                        
                        if st.session_state.get('gestionar_comentarios_producto') == p['id']:
                            mostrar_seccion_comentarios("producto", p['id'], p['nombre'], es_admin)
                            if st.button("❌ Cerrar comentarios", key=f"cerrar_com_prod_{p['id']}_{idx}"):
                                del st.session_state.gestionar_comentarios_producto
                                st.rerun()
        else:
            st.info("No hay productos registrados. ¡Agrega tu primer producto!")
        
        if st.session_state.get('edit_producto'):
            p = st.session_state.edit_producto
            st.markdown("---")
            st.subheader(f"✏️ Editando: {p['nombre']}")
            
            with st.form("edit_producto_form"):
                nuevo_nombre = st.text_input("Nombre", value=p['nombre'])
                nueva_descripcion = st.text_area("Descripción", value=p.get('descripcion', ''))
                
                col1, col2 = st.columns(2)
                with col1:
                    nueva_categoria = st.selectbox("Categoría", CATEGORIAS_LISTA, index=CATEGORIAS_LISTA.index(p['categoria']) if p['categoria'] in CATEGORIAS_LISTA else 0)
                    sub_options = CATEGORIAS.get(nueva_categoria, [])
                    if p['subcategoria'] in sub_options:
                        sub_idx = [s for s in sub_options if s != "Todas"].index(p['subcategoria'])
                    else:
                        sub_idx = 0
                    nueva_subcategoria = st.selectbox("Subcategoría", [s for s in sub_options if s != "Todas"], index=sub_idx)
                with col2:
                    nuevo_precio = st.number_input("Precio en dólares ($)", min_value=0.01, step=0.01, format="%.2f", value=float(p['precio']))
                    nueva_cantidad = st.number_input("Cantidad en stock", min_value=0, step=1, value=int(p.get('cantidad', 0)))
                
                nueva_imagen = st.file_uploader("Nueva imagen (opcional)", type=["jpg", "png", "jpeg"])
                
                if nuevo_precio > 0:
                    st.info(f"💰 Precio en Bolívares: **{nuevo_precio * dolar:,.2f} Bs**")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.form_submit_button("💾 Guardar cambios"):
                        if update_producto(p['id'], nuevo_nombre, nueva_descripcion, nuevo_precio, nueva_categoria, nueva_subcategoria, nueva_imagen, nueva_cantidad):
                            st.success("✅ Producto actualizado")
                            del st.session_state.edit_producto
                            st.rerun()
                        else:
                            st.error("❌ Error al actualizar producto")
                with col2:
                    if st.form_submit_button("❌ Cancelar"):
                        del st.session_state.edit_producto
                        st.rerun()

# ============================================
# FOOTER
# ============================================
st.markdown("""
<div class="bronze-footer">
    <div style="position: relative;">
        <div style="position: absolute; top: 15px; left: 15px; width: 22px; height: 22px; background: radial-gradient(circle at 30% 30%, #bbb, #444); border-radius: 50%; box-shadow: 2px 2px 6px rgba(0,0,0,0.6); border: 1px solid #d4af37;"></div>
        <div style="position: absolute; top: 15px; right: 15px; width: 22px; height: 22px; background: radial-gradient(circle at 30% 30%, #bbb, #444); border-radius: 50%; box-shadow: 2px 2px 6px rgba(0,0,0,0.6); border: 1px solid #d4af37;"></div>
        <div style="position: absolute; bottom: 15px; left: 15px; width: 22px; height: 22px; background: radial-gradient(circle at 30% 30%, #bbb, #444); border-radius: 50%; box-shadow: 2px 2px 6px rgba(0,0,0,0.6); border: 1px solid #d4af37;"></div>
        <div style="position: absolute; bottom: 15px; right: 15px; width: 22px; height: 22px; background: radial-gradient(circle at 30% 30%, #bbb, #444); border-radius: 50%; box-shadow: 2px 2px 6px rgba(0,0,0,0.6); border: 1px solid #d4af37;"></div>
        <p style="font-size: 1.8em; letter-spacing: 4px; color: #ffd700; font-family: 'Times New Roman', serif; font-weight: bold;">DESARROLLADO POR WILLIAN ALMENAR</p>
        <p style="color: #ffd700; font-family: 'Times New Roman', serif; font-weight: bold;">Prohibida la reproducción total o parcial</p>
        <p style="color: #ffd700; font-family: 'Times New Roman', serif; font-weight: bold;">DERECHOS RESERVADOS</p>
        <p style="color: #ffd700; font-family: 'Times New Roman', serif; font-weight: bold;">Santa Teresa del Tuy, 2026</p>
    </div>
</div>
""", unsafe_allow_html=True)
