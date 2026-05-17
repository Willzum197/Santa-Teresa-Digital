import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
from supabase import create_client, Client
from PIL import Image
import base64
import io
import tempfile
import os

# ============================================
# CONFIGURACION DE SUPABASE
# ============================================
def init_supabase():
    """Inicializa la conexión con Supabase usando secrets"""
    try:
        # Leer credenciales desde secrets de Streamlit
        supabase_url = st.secrets["SUPABASE_URL"]
        supabase_key = st.secrets["SUPABASE_KEY"]
        
        # Crear cliente de Supabase
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Probar conexión
        test = supabase.table("noticias").select("count", count="exact").limit(1).execute()
        
        return supabase
    except Exception as e:
        st.error(f"Error de conexión con Supabase: {str(e)}")
        st.stop()

supabase = init_supabase()

# ============================================
# DETECTAR DISPOSITIVO MOVIL
# ============================================
def is_mobile():
    try:
        user_agent = st.context.headers.get('User-Agent', '').lower()
        mobile_keywords = ['android', 'iphone', 'ipad', 'ipod', 'windows phone', 'mobile', 'blackberry', 'opera mini', 'iemobile']
        return any(keyword in user_agent for keyword in mobile_keywords)
    except:
        return False

es_movil = is_mobile()

# ============================================
# ESTILOS PARA MOVIL
# ============================================
if es_movil:
    st.markdown("""
    <style>
    .main > div {
        padding: 8px !important;
        margin: 5px 0 !important;
    }
    .stButton > button {
        padding: 6px 12px !important;
        font-size: 0.85em !important;
    }
    h1 {
        font-size: 1.4em !important;
    }
    h2, h3 {
        font-size: 1.1em !important;
    }
    .stats-panel {
        padding: 8px !important;
    }
    .streamlit-expanderHeader {
        font-size: 0.85em !important;
        padding: 6px !important;
    }
    [data-testid="stSidebar"] {
        min-width: 220px !important;
    }
    </style>
    """, unsafe_allow_html=True)

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
[data-testid="stDecoration"] {display: none !important;}
[data-testid="stStatusWidget"] {display: none !important;}
.stAppDeployButton {display: none !important;}
.viewerBadge_container__1QSob {display: none !important;}
.stVersion {display: none !important;}
.stApp > header {display: none !important;}
[data-testid="collapsedControl"] {display: none !important;}
</style>
""", unsafe_allow_html=True)

# ============================================
# URL DE LA APP
# ============================================
APP_URL = "https://santateresaldia.streamlit.app/"

# ============================================
# CONFIGURACION DE PAGINA
# ============================================
st.set_page_config(
    page_title="Santa Teresa al Dia",
    page_icon="🇻🇪",
    layout="wide"
)

# ============================================
# ZONA HORARIA
# ============================================
CARACAS_TZ = pytz.timezone('America/Caracas')

def get_fecha_hora_venezuela():
    ahora_utc = datetime.now(pytz.UTC)
    ahora_caracas = ahora_utc.astimezone(CARACAS_TZ)
    return ahora_caracas

# ============================================
# FUNCIONES DE CONVERSION
# ============================================
def video_a_base64(file):
    if file:
        try:
            bytes_data = file.read()
            if len(bytes_data) > 50 * 1024 * 1024:
                st.error("Video muy grande (maximo 50 MB)")
                return None
            return base64.b64encode(bytes_data).decode()
        except Exception:
            return None
    return None

def audio_a_base64(file):
    if file:
        try:
            bytes_data = file.read()
            if len(bytes_data) > 20 * 1024 * 1024:
                st.error("Audio muy grande (maximo 20 MB)")
                return None
            return base64.b64encode(bytes_data).decode()
        except Exception:
            return None
    return None

def img_a_base64(file):
    if file:
        try:
            img = Image.open(file)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            img.thumbnail((800, 800))
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=70)
            return f"data:image/jpeg;base64,{base64.b64encode(buf.getvalue()).decode()}"
        except Exception:
            return None
    return None

def mostrar_video(video_data, formato):
    try:
        video_bytes = base64.b64decode(video_data)
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{formato}") as tmp:
            tmp.write(video_bytes)
            tmp_path = tmp.name
        if es_movil:
            st.video(tmp_path)
        else:
            st.markdown('<div style="max-width: 500px; margin: 0 auto;">', unsafe_allow_html=True)
            st.video(tmp_path)
            st.markdown('</div>', unsafe_allow_html=True)
        os.unlink(tmp_path)
    except Exception:
        st.error("Error al cargar video")

def mostrar_audio(audio_data, formato):
    try:
        audio_bytes = base64.b64decode(audio_data)
        with tempfile.NamedTemporaryFile(delete=False, suffix=f".{formato}") as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name
        st.audio(tmp_path)
        os.unlink(tmp_path)
    except Exception:
        st.error("Error al cargar audio")

# ============================================
# CREAR TABLAS EN SUPABASE
# ============================================
def crear_tablas_supabase():
    """
    NOTA: Las tablas deben crearse MANUALMENTE en Supabase
    Ejecuta este SQL en el SQL Editor de Supabase:
    """
    sql_script = """
    -- Tabla de noticias
    CREATE TABLE IF NOT EXISTS noticias (
        id SERIAL PRIMARY KEY,
        titulo TEXT,
        categoria TEXT,
        contenido TEXT,
        imagen_url TEXT,
        fecha TEXT,
        autor TEXT
    );
    
    -- Tabla de negocios
    CREATE TABLE IF NOT EXISTS negocios (
        id SERIAL PRIMARY KEY,
        nombre TEXT,
        categoria TEXT,
        resena TEXT,
        imagen_url TEXT,
        direccion TEXT,
        telefono TEXT,
        horario TEXT,
        fecha TEXT
    );
    
    -- Tabla de reflexiones
    CREATE TABLE IF NOT EXISTS reflexiones (
        id SERIAL PRIMARY KEY,
        titulo TEXT,
        contenido TEXT,
        versiculo TEXT,
        autor TEXT,
        fecha TEXT,
        activo BOOLEAN DEFAULT TRUE
    );
    
    -- Tabla de cronicas
    CREATE TABLE IF NOT EXISTS cronicas (
        id SERIAL PRIMARY KEY,
        titulo TEXT,
        contenido TEXT,
        autor TEXT,
        fecha TEXT,
        lugar TEXT,
        estado TEXT
    );
    
    -- Tabla de videos
    CREATE TABLE IF NOT EXISTS videos (
        id SERIAL PRIMARY KEY,
        titulo TEXT,
        video_data TEXT,
        formato TEXT,
        fecha TEXT
    );
    
    -- Tabla de musicas
    CREATE TABLE IF NOT EXISTS musicas (
        id SERIAL PRIMARY KEY,
        titulo TEXT,
        audio_data TEXT,
        formato TEXT,
        fecha TEXT
    );
    
    -- Tabla de denuncias
    CREATE TABLE IF NOT EXISTS denuncias (
        id SERIAL PRIMARY KEY,
        denunciante TEXT,
        titulo TEXT,
        descripcion TEXT,
        ubicacion TEXT,
        fecha TEXT,
        estatus TEXT DEFAULT 'Pendiente'
    );
    
    -- Tabla de opiniones
    CREATE TABLE IF NOT EXISTS opiniones (
        id SERIAL PRIMARY KEY,
        usuario TEXT,
        comentario TEXT,
        calificacion INTEGER,
        fecha TEXT,
        aprobada BOOLEAN DEFAULT FALSE
    );
    
    -- Tabla de visitas
    CREATE TABLE IF NOT EXISTS visitas (
        id INTEGER PRIMARY KEY,
        conteo INTEGER DEFAULT 1500
    );
    
    -- Tabla de configuracion
    CREATE TABLE IF NOT EXISTS configuracion (
        id INTEGER PRIMARY KEY,
        logo_url TEXT,
        dolar REAL DEFAULT 489.55
    );
    
    -- Insertar datos iniciales
    INSERT INTO visitas (id, conteo) VALUES (1, 1500) ON CONFLICT (id) DO NOTHING;
    INSERT INTO configuracion (id, logo_url, dolar) VALUES (1, NULL, 489.55) ON CONFLICT (id) DO NOTHING;
    """
    st.info("⚠️ Ejecuta el script SQL arriba en el SQL Editor de Supabase")
    return True

# ============================================
# FUNCIONES DE ACCESO A DATOS CON SUPABASE
# ============================================

# --- NOTICIAS ---
def add_noticia(titulo, categoria, contenido, imagen):
    try:
        ahora = get_fecha_hora_venezuela()
        img_url = img_a_base64(imagen) if imagen else None
        data = {
            "titulo": titulo,
            "categoria": categoria,
            "contenido": contenido,
            "imagen_url": img_url,
            "fecha": ahora.strftime("%d/%m/%Y"),
            "autor": "Admin"
        }
        supabase.table("noticias").insert(data).execute()
        return True
    except Exception as e:
        st.error(f"Error: {e}")
        return False

def get_noticias(categoria=None):
    try:
        if categoria and categoria != "Todas":
            response = supabase.table("noticias").select("*").eq("categoria", categoria).order("id", desc=True).execute()
        else:
            response = supabase.table("noticias").select("*").order("id", desc=True).execute()
        return pd.DataFrame(response.data)
    except Exception:
        return pd.DataFrame()

def delete_noticia(id_):
    try:
        supabase.table("noticias").delete().eq("id", id_).execute()
        return True
    except Exception:
        return False

# --- NEGOCIOS ---
def add_negocio(nombre, categoria, resena, direccion, telefono, horario, imagen):
    try:
        ahora = get_fecha_hora_venezuela()
        img_url = img_a_base64(imagen) if imagen else None
        data = {
            "nombre": nombre,
            "categoria": categoria,
            "resena": resena,
            "imagen_url": img_url,
            "direccion": direccion,
            "telefono": telefono,
            "horario": horario,
            "fecha": ahora.strftime("%d/%m/%Y")
        }
        supabase.table("negocios").insert(data).execute()
        return True
    except Exception:
        return False

def get_negocios():
    try:
        response = supabase.table("negocios").select("*").order("id", desc=True).execute()
        return pd.DataFrame(response.data)
    except Exception:
        return pd.DataFrame()

def delete_negocio(id_):
    try:
        supabase.table("negocios").delete().eq("id", id_).execute()
        return True
    except Exception:
        return False

# --- REFLEXIONES ---
def add_reflexion(titulo, contenido, versiculo):
    try:
        ahora = get_fecha_hora_venezuela()
        # Desactivar todas las reflexiones
        supabase.table("reflexiones").update({"activo": False}).execute()
        # Insertar nueva reflexion activa
        data = {
            "titulo": titulo,
            "contenido": contenido,
            "versiculo": versiculo,
            "autor": "Admin",
            "fecha": ahora.strftime("%d/%m/%Y"),
            "activo": True
        }
        supabase.table("reflexiones").insert(data).execute()
        return True
    except Exception:
        return False

def get_reflexion_activa():
    try:
        response = supabase.table("reflexiones").select("*").eq("activo", True).limit(1).execute()
        if response.data:
            return response.data[0]
        return None
    except Exception:
        return None

def get_reflexiones():
    try:
        response = supabase.table("reflexiones").select("*").order("id", desc=True).execute()
        return pd.DataFrame(response.data)
    except Exception:
        return pd.DataFrame()

def delete_reflexion(id_):
    try:
        supabase.table("reflexiones").delete().eq("id", id_).execute()
        return True
    except Exception:
        return False

# --- CRONICAS ---
def add_cronica(titulo, contenido, lugar, estado):
    try:
        ahora = get_fecha_hora_venezuela()
        data = {
            "titulo": titulo,
            "contenido": contenido,
            "autor": "Admin",
            "fecha": ahora.strftime("%d/%m/%Y"),
            "lugar": lugar,
            "estado": estado
        }
        supabase.table("cronicas").insert(data).execute()
        return True
    except Exception:
        return False

def get_cronicas(estado=None):
    try:
        if estado and estado != "Todos":
            response = supabase.table("cronicas").select("*").eq("estado", estado).order("id", desc=True).execute()
        else:
            response = supabase.table("cronicas").select("*").order("id", desc=True).execute()
        return pd.DataFrame(response.data)
    except Exception:
        return pd.DataFrame()

def delete_cronica(id_):
    try:
        supabase.table("cronicas").delete().eq("id", id_).execute()
        return True
    except Exception:
        return False

# --- VIDEOS ---
def add_video(titulo, archivo_video):
    try:
        ahora = get_fecha_hora_venezuela()
        video_data = video_a_base64(archivo_video)
        if video_data:
            formato = archivo_video.type.split("/")[-1] if archivo_video.type else "mp4"
            data = {
                "titulo": titulo,
                "video_data": video_data,
                "formato": formato,
                "fecha": ahora.strftime("%d/%m/%Y")
            }
            supabase.table("videos").insert(data).execute()
            return True
        return False
    except Exception:
        return False

def get_videos():
    try:
        response = supabase.table("videos").select("*").order("id", desc=True).execute()
        return pd.DataFrame(response.data)
    except Exception:
        return pd.DataFrame()

def delete_video(id_):
    try:
        supabase.table("videos").delete().eq("id", id_).execute()
        return True
    except Exception:
        return False

# --- MUSICA ---
def add_musica(titulo, archivo_audio):
    try:
        ahora = get_fecha_hora_venezuela()
        audio_data = audio_a_base64(archivo_audio)
        if audio_data:
            formato = archivo_audio.type.split("/")[-1] if archivo_audio.type else "mp3"
            data = {
                "titulo": titulo,
                "audio_data": audio_data,
                "formato": formato,
                "fecha": ahora.strftime("%d/%m/%Y")
            }
            supabase.table("musicas").insert(data).execute()
            return True
        return False
    except Exception:
        return False

def get_musicas():
    try:
        response = supabase.table("musicas").select("*").order("id", desc=True).execute()
        return pd.DataFrame(response.data)
    except Exception:
        return pd.DataFrame()

def delete_musica(id_):
    try:
        supabase.table("musicas").delete().eq("id", id_).execute()
        return True
    except Exception:
        return False

# --- DENUNCIAS ---
def add_denuncia(denunciante, titulo, descripcion, ubicacion):
    try:
        ahora = get_fecha_hora_venezuela()
        data = {
            "denunciante": denunciante or "Anonimo",
            "titulo": titulo,
            "descripcion": descripcion,
            "ubicacion": ubicacion,
            "fecha": ahora.strftime("%d/%m/%Y"),
            "estatus": "Pendiente"
        }
        supabase.table("denuncias").insert(data).execute()
        return True
    except Exception:
        return False

def get_denuncias():
    try:
        response = supabase.table("denuncias").select("*").order("id", desc=True).execute()
        return pd.DataFrame(response.data)
    except Exception:
        return pd.DataFrame()

def update_denuncia_status(id_, status):
    try:
        supabase.table("denuncias").update({"estatus": status}).eq("id", id_).execute()
        return True
    except Exception:
        return False

def delete_denuncia(id_):
    try:
        supabase.table("denuncias").delete().eq("id", id_).execute()
        return True
    except Exception:
        return False

# --- OPINIONES ---
def add_opinion(usuario, comentario, calificacion):
    try:
        ahora = get_fecha_hora_venezuela()
        data = {
            "usuario": usuario,
            "comentario": comentario,
            "calificacion": calificacion,
            "fecha": ahora.strftime("%d/%m/%Y %H:%M"),
            "aprobada": False
        }
        supabase.table("opiniones").insert(data).execute()
        return True
    except Exception:
        return False

def get_opiniones(aprobadas=True):
    try:
        if aprobadas:
            response = supabase.table("opiniones").select("*").eq("aprobada", True).order("id", desc=True).execute()
        else:
            response = supabase.table("opiniones").select("*").order("id", desc=True).execute()
        return pd.DataFrame(response.data)
    except Exception:
        return pd.DataFrame()

def approve_opinion(id_):
    try:
        supabase.table("opiniones").update({"aprobada": True}).eq("id", id_).execute()
        return True
    except Exception:
        return False

def delete_opinion(id_):
    try:
        supabase.table("opiniones").delete().eq("id", id_).execute()
        return True
    except Exception:
        return False

# --- VISITAS Y CONFIGURACION ---
def actualizar_visitas():
    try:
        # Obtener conteo actual
        response = supabase.table("visitas").select("conteo").eq("id", 1).execute()
        if response.data:
            conteo_actual = response.data[0]["conteo"]
            supabase.table("visitas").update({"conteo": conteo_actual + 1}).eq("id", 1).execute()
    except Exception:
        pass

def get_visitas():
    try:
        response = supabase.table("visitas").select("conteo").eq("id", 1).execute()
        if response.data:
            return int(response.data[0]["conteo"])
        return 1500
    except Exception:
        return 1500

def get_dolar():
    try:
        response = supabase.table("configuracion").select("dolar").eq("id", 1).execute()
        if response.data and response.data[0]["dolar"]:
            return float(response.data[0]["dolar"])
        return 489.55
    except Exception:
        return 489.55

def actualizar_dolar_manual(nuevo_valor):
    try:
        supabase.table("configuracion").update({"dolar": nuevo_valor}).eq("id", 1).execute()
        return True
    except Exception:
        return False

def get_logo():
    try:
        response = supabase.table("configuracion").select("logo_url").eq("id", 1).execute()
        if response.data and response.data[0]["logo_url"]:
            return response.data[0]["logo_url"]
        return None
    except Exception:
        return None

def save_logo(url):
    try:
        supabase.table("configuracion").update({"logo_url": url}).eq("id", 1).execute()
        return True
    except Exception:
        return False

# ============================================
# INICIALIZAR DATOS SI ESTAN VACIOS
# ============================================
def inicializar_datos():
    """Inserta datos de ejemplo si las tablas estan vacias"""
    try:
        # Verificar si hay noticias
        noticias = get_noticias()
        if noticias.empty:
            fecha_actual = datetime.now().strftime("%d/%m/%Y")
            noticias_iniciales = [
                ("Bienvenidos a Santa Teresa al Dia", "Nacional", "Un espacio para mantenernos informados sobre lo que sucede en nuestra comunidad.", fecha_actual, "Admin"),
                ("Santa Teresa progresa", "Nacional", "Nuestra ciudad sigue creciendo y desarrollándose cada día.", fecha_actual, "Admin"),
                ("Vinotinto se prepara", "Deportes", "La selección continúa su preparación para los próximos compromisos.", fecha_actual, "Admin"),
            ]
            for n in noticias_iniciales:
                add_noticia(n[0], n[1], n[2], None)
        
        # Verificar si hay reflexiones
        reflexiones = get_reflexiones()
        if reflexiones.empty:
            add_reflexion("La Paz de Dios", "No te angusties por nada. Presenta tus peticiones delante de Dios.", "Filipenses 4:6-7")
        
        # Verificar si hay cronicas
        cronicas = get_cronicas()
        if cronicas.empty:
            cronicas_iniciales = [
                ("Los Valles del Tuy", "Los Valles del Tuy fueron testigos de importantes batallas por la independencia.", "Valles del Tuy", "Miranda"),
                ("La Batalla de Carabobo", "El 24 de junio de 1821, el Ejército Patriota liderado por Simón Bolívar derrotó a las fuerzas realistas.", "Campo de Carabobo", "Carabobo"),
            ]
            for c in cronicas_iniciales:
                add_cronica(c[0], c[1], c[2], c[3])
                
    except Exception as e:
        st.warning(f"No se pudieron inicializar datos: {e}")

# Ejecutar inicialización
inicializar_datos()

# ============================================
# CONTADOR DE VISITAS
# ============================================
if 'visitante_contado' not in st.session_state:
    actualizar_visitas()
    st.session_state.visitante_contado = True

visitas = get_visitas()
dolar = get_dolar()

# ============================================
# ESTILOS PRINCIPALES
# ============================================
st.markdown("""
<style>
.stApp {
    background: linear-gradient(180deg, #FFD700 0%, #00247D 50%, #CF142B 100%);
}
.main > div {
    background-color: rgba(0,0,0,0.7);
    border-radius: 15px;
    padding: 20px;
    margin: 10px 0;
}
[data-testid="stSidebar"] {
    background-color: rgba(0,0,0,0.85) !important;
    border-right: 3px solid #FFD700;
}
[data-testid="stSidebar"] * {
    color: white !important;
}
h1, h2, h3, h4 {
    color: #FFD700 !important;
}
p, span, label {
    color: white !important;
}
.stButton > button {
    background: linear-gradient(135deg, #FFD700, #CF142B);
    color: white !important;
    border: none;
    font-weight: bold;
    border-radius: 25px;
}
input, textarea, .stSelectbox {
    background-color: rgba(255,255,255,0.95) !important;
    color: black !important;
    border-radius: 12px;
    border: 2px solid #FFD700 !important;
}
.stats-panel {
    background: rgba(0,0,0,0.6);
    padding: 15px;
    border-radius: 20px;
    border: 2px solid #FFD700;
    text-align: center;
    margin-bottom: 20px;
}
.bronze-footer {
    background: linear-gradient(145deg, #8c6a31, #5d431a);
    border: 5px solid #d4af37;
    padding: 35px 25px;
    border-radius: 20px;
    text-align: center;
    margin-top: 50px;
}
.bronze-footer p {
    color: #ffd700 !important;
    font-family: 'Times New Roman', serif;
    font-weight: bold;
}
.bronze-footer .titulo {
    font-size: 1.8em;
    letter-spacing: 4px;
}
.screw {
    position: absolute;
    width: 22px;
    height: 22px;
    background: radial-gradient(circle at 30% 30%, #bbb, #444);
    border-radius: 50%;
    box-shadow: 2px 2px 6px rgba(0,0,0,0.6);
    border: 1px solid #d4af37;
}
.screw-tl { top: 15px; left: 15px; }
.screw-tr { top: 15px; right: 15px; }
.screw-bl { bottom: 15px; left: 15px; }
.screw-br { bottom: 15px; right: 15px; }
.streamlit-expanderHeader {
    background-color: rgba(0,0,0,0.5);
    border-radius: 10px;
    border-left: 4px solid #FFD700;
    font-weight: bold;
}
.share-row {
    display: flex;
    justify-content: center;
    gap: 15px;
    flex-wrap: wrap;
    margin: 15px 0;
}
.share-btn {
    display: inline-block;
    padding: 8px 20px;
    border-radius: 25px;
    text-align: center;
    text-decoration: none;
    font-weight: bold;
    color: white;
    min-width: 110px;
}
.share-wa { background: #25D366; }
.share-fb { background: #1877F2; }
.share-ig { background: linear-gradient(45deg, #f09433, #d62976); }
.share-copy { background: #3498db; }
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: rgba(0,0,0,0.5);
    border-radius: 15px;
    padding: 8px;
}
.stTabs [data-baseweb="tab"] {
    background-color: rgba(0,0,0,0.7);
    border-radius: 12px;
    color: #FFD700 !important;
    font-weight: bold;
    padding: 10px 25px;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #FFD700, #CF142B) !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)

# ============================================
# FECHA Y HORA
# ============================================
ahora = get_fecha_hora_venezuela()
dias = ["Lunes", "Martes", "Miercoles", "Jueves", "Viernes", "Sabado", "Domingo"]
meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

# ============================================
# LOGO
# ============================================
logo = get_logo()
if logo:
    st.markdown(f'<div style="text-align: center;"><img src="{logo}" style="max-width: 200px;"></div>', unsafe_allow_html=True)

# ============================================
# ENCABEZADO
# ============================================
st.markdown(f"""
<div style="text-align: center; margin-bottom: 20px;">
    <div style="background: linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.4));
                border-radius: 20px;
                padding: 50px 20px;
                border: 2px solid #FFD700;">
        <h1 style="color: white; text-shadow: 3px 3px 6px black;">Santa Teresa al Dia</h1>
        <p style="color: white; text-shadow: 2px 2px 4px black;">Informacion, Cultura y Fe</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================
# BOTONES DE COMPARTIR
# ============================================
st.markdown(f"""
<div class="share-row">
    <a href="https://api.whatsapp.com/send?text=Santa Teresa al Dia - {APP_URL}" target="_blank" class="share-btn share-wa">WhatsApp</a>
    <a href="https://www.facebook.com/sharer/sharer.php?u={APP_URL}" target="_blank" class="share-btn share-fb">Facebook</a>
    <button onclick="copyToClipboard('{APP_URL}')" class="share-btn share-ig">Instagram</button>
    <button onclick="copyToClipboard('{APP_URL}')" class="share-btn share-copy">Copiar</button>
</div>
<script>
function copyToClipboard(text) {{
    navigator.clipboard.writeText(text);
    alert("Enlace copiado!");
}}
</script>
""", unsafe_allow_html=True)

st.markdown("---")

# ============================================
# PANEL SUPERIOR
# ============================================
st.markdown(f"""
<div class="stats-panel">
    <span style="color:#FFD700;">⭐ {dias[ahora.weekday()]}, {ahora.day} de {meses[ahora.month-1]} de {ahora.year} ⭐</span><br>
    <span style="color:white; font-size:1.5em;">{ahora.strftime("%I:%M %p")}</span><br>
    <span style="color:#FFD700;">Visitantes: {visitas:,} | Dolar BCV: {dolar:.2f} Bs</span>
</div>
""", unsafe_allow_html=True)

# ============================================
# SIDEBAR - PANEL DE ADMINISTRACION
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
    elif clave:
        st.error("❌ Clave incorrecta")
    
    if es_admin:
        st.markdown("---")
        st.markdown("### 📋 Panel de Control")
        
        admin_opt = st.radio("Seleccionar módulo:", [
            "📰 Noticias", "🏪 Negocios", "💭 Reflexiones", "📜 Crónicas",
            "🎬 Videos", "🎵 Música", "⚠️ Denuncias", "💬 Opiniones", "⚙️ Configuración"
        ])
        
        st.session_state.admin_opt = admin_opt
        st.session_state.es_admin = True
    else:
        st.session_state.es_admin = False

# ============================================
# MENU PRINCIPAL (TABS)
# ============================================
menu_tabs = st.tabs(["🏠 Portada", "📰 Noticias", "📍 Donde ir - Donde comprar", "💭 Reflexiones", "📜 Crónicas", "🎬 Multimedia", "⚠️ Denuncias", "💬 Opiniones", "📅 Efemérides Médicas"])

# --- TAB 0: PORTADA ---
with menu_tabs[0]:
    st.title("Santa Teresa al Dia")
    
    st.markdown("### 📰 Últimas Noticias")
    noticias = get_noticias()
    if not noticias.empty:
        for _, n in noticias.head(10).iterrows():
            with st.expander(f"{n['titulo']} - {n['categoria']} ({n['fecha']})"):
                if n.get('imagen_url'):
                    st.image(n['imagen_url'], width=300)
                st.write(n['contenido'])
    else:
        st.info("No hay noticias")
    
    st.markdown("---")
    st.markdown("### ✝️ Reflexión del Día")
    ref = get_reflexion_activa()
    if ref is not None:
        with st.expander(f"{ref['titulo']}", expanded=True):
            st.write(ref['contenido'])
            st.caption(f"📖 {ref['versiculo']}")
    else:
        st.info("No hay reflexión activa")
    
    st.markdown("---")
    st.markdown("### ⭐ Recomendados")
    negocios = get_negocios()
    if not negocios.empty:
        for _, n in negocios.head(3).iterrows():
            st.markdown(f"**🏪 {n['nombre']}** - {n['categoria']}")

# --- TAB 1: NOTICIAS ---
with menu_tabs[1]:
    st.title("📰 Noticias")
    
    tab_nac, tab_inter, tab_dep = st.tabs(["🇻🇪 Nacionales", "🌎 Internacionales", "⚽ Deportes"])
    
    with tab_nac:
        noticias_nac = get_noticias(categoria="Nacional")
        if not noticias_nac.empty:
            for _, n in noticias_nac.iterrows():
                with st.expander(f"{n['titulo']} - {n['fecha']}"):
                    if n.get('imagen_url'):
                        st.image(n['imagen_url'], width=300)
                    st.write(n['contenido'])
        else:
            st.info("No hay noticias Nacionales")
    
    with tab_inter:
        noticias_inter = get_noticias(categoria="Internacional")
        if not noticias_inter.empty:
            for _, n in noticias_inter.iterrows():
                with st.expander(f"{n['titulo']} - {n['fecha']}"):
                    if n.get('imagen_url'):
                        st.image(n['imagen_url'], width=300)
                    st.write(n['contenido'])
        else:
            st.info("No hay noticias Internacionales")
    
    with tab_dep:
        noticias_dep = get_noticias(categoria="Deportes")
        if not noticias_dep.empty:
            for _, n in noticias_dep.iterrows():
                with st.expander(f"{n['titulo']} - {n['fecha']}"):
                    if n.get('imagen_url'):
                        st.image(n['imagen_url'], width=300)
                    st.write(n['contenido'])
        else:
            st.info("No hay noticias de Deportes")

# --- TAB 2: DONDE IR - DONDE COMPRAR ---
with menu_tabs[2]:
    st.title("📍 Donde ir - Donde comprar")
    
    negocios = get_negocios()
    if not negocios.empty:
        for _, n in negocios.iterrows():
            col_a, col_b = st.columns([1, 2])
            with col_a:
                if n.get('imagen_url'):
                    st.image(n['imagen_url'], use_container_width=True)
                else:
                    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/7/7b/Flag_of_Venezuela_%28state%29.svg/1200px-Flag_of_Venezuela_%28state%29.svg.png", use_container_width=True)
            with col_b:
                st.markdown(f"### {n['nombre']}")
                st.caption(n['categoria'])
                st.write(n['resena'])
                if n.get('direccion'):
                    st.write(f"📍 **Dirección:** {n['direccion']}")
                if n.get('telefono'):
                    st.write(f"📞 **Teléfono:** {n['telefono']}")
                if n.get('horario'):
                    st.write(f"⏰ **Horario:** {n['horario']}")
            st.markdown("---")
    else:
        st.info("No hay negocios agregados")

# --- TAB 3: REFLEXIONES ---
with menu_tabs[3]:
    st.title("💭 Reflexiones")
    
    ref = get_reflexion_activa()
    if ref is not None:
        with st.expander(f"✨ ACTUAL: {ref['titulo']}", expanded=True):
            st.write(ref['contenido'])
            st.caption(f"📖 {ref['versiculo']}")
            st.caption(f"📅 {ref['fecha']}")
    else:
        st.info("No hay reflexión activa")
    
    st.markdown("---")
    st.markdown("### 📜 Reflexiones Anteriores")
    reflexiones = get_reflexiones()
    if not reflexiones.empty:
        for _, r in reflexiones.iterrows():
            if ref is None or r['id'] != ref['id']:
                with st.expander(f"{r['titulo']} - {r['fecha']}"):
                    st.write(r['contenido'])
                    if r.get('versiculo'):
                        st.caption(f"📖 {r['versiculo']}")
    else:
        st.info("No hay reflexiones anteriores")

# --- TAB 4: CRONICAS ---
with menu_tabs[4]:
    st.title("📜 Crónicas")
    
    estados = ["Todos", "Miranda", "Carabobo", "Distrito Capital", "Zulia", "Lara", "Aragua", "Bolivar", "Anzoategui", "Merida", "Tachira", "Nueva Esparta", "Sucre", "Falcon", "Barinas", "Portuguesa", "Guarico", "Cojedes", "Trujillo", "Yaracuy", "Apure", "Amazonas", "Delta Amacuro", "Vargas"]
    estado_filtro = st.selectbox("Filtrar por estado:", estados)
    
    cronicas = get_cronicas(estado_filtro if estado_filtro != "Todos" else None)
    if not cronicas.empty:
        for _, c in cronicas.iterrows():
            with st.expander(f"📖 {c['titulo']} - {c['lugar']}, {c['estado']}"):
                st.write(c['contenido'])
                st.caption(f"📅 {c['fecha']}")
    else:
        st.info("No hay crónicas disponibles")

# --- TAB 5: MULTIMEDIA ---
with menu_tabs[5]:
    st.title("🎬 Multimedia")
    
    tab_vid, tab_mus, tab_rad = st.tabs(["🎥 Videos", "🎵 Música", "📻 Radio"])
    
    with tab_vid:
        videos = get_videos()
        if not videos.empty:
            for _, v in videos.iterrows():
                with st.expander(f"🎬 {v['titulo']}"):
                    mostrar_video(v['video_data'], v['formato'])
                    st.caption(f"Subido: {v['fecha']}")
        else:
            st.info("No hay videos disponibles")
    
    with tab_mus:
        musicas = get_musicas()
        if not musicas.empty:
            for _, m in musicas.iterrows():
                with st.expander(f"🎵 {m['titulo']}"):
                    mostrar_audio(m['audio_data'], m['formato'])
                    st.caption(f"Agregado: {m['fecha']}")
        else:
            st.info("No hay música disponible")
    
    with tab_rad:
        st.markdown("### 📻 Radio Online")
        st.audio("https://streaming.radiosenlinea.net/9090/stream")

# --- TAB 6: DENUNCIAS ---
with menu_tabs[6]:
    st.title("⚠️ Denuncias Ciudadanas")
    
    tab_den, tab_ver = st.tabs(["📝 Hacer Denuncia", "👁️ Ver Denuncias"])
    
    with tab_den:
        with st.form("fd"):
            nombre = st.text_input("Nombre (opcional)")
            titulo = st.text_input("Título *")
            desc = st.text_area("Descripción *")
            ubic = st.text_input("Ubicación")
            if st.form_submit_button("Enviar Denuncia"):
                if titulo and desc:
                    add_denuncia(nombre, titulo, desc, ubic)
                    st.success("✅ Denuncia enviada correctamente")
                    st.balloons()
                else:
                    st.error("❌ Título y descripción son obligatorios")
    
    with tab_ver:
        denuncias = get_denuncias()
        if not denuncias.empty:
            for _, d in denuncias.iterrows():
                st.markdown(f"**📌 {d['titulo']}** - `{d['estatus']}`")
                st.caption(f"📍 {d['ubicacion'] if d['ubicacion'] else 'No especificada'}")
                with st.expander("Ver detalles"):
                    st.write(d['descripcion'])
                    st.caption(f"📅 {d['fecha']}")
                st.divider()
        else:
            st.info("No hay denuncias registradas")

# --- TAB 7: OPINIONES ---
with menu_tabs[7]:
    st.title("💬 Opiniones")
    
    tab_op, tab_ver_op = st.tabs(["✍️ Dar Opinión", "👁️ Ver Opiniones"])
    
    with tab_op:
        with st.form("fo"):
            usuario = st.text_input("Nombre *")
            comentario = st.text_area("Comentario *")
            estrellas = st.slider("Calificación", 1, 5, 5)
            if st.form_submit_button("Enviar Opinión"):
                if usuario and comentario:
                    add_opinion(usuario, comentario, estrellas)
                    st.success("✅ Opinión enviada, será revisada por un administrador")
                    st.balloons()
                else:
                    st.error("❌ Nombre y comentario son obligatorios")
    
    with tab_ver_op:
        opiniones = get_opiniones(aprobadas=True)
        if not opiniones.empty:
            for _, op in opiniones.iterrows():
                stars = "⭐" * int(op['calificacion']) + "☆" * (5 - int(op['calificacion']))
                st.markdown(f"**👤 {op['usuario']}** {stars}")
                st.write(f"\"{op['comentario']}\"")
                st.caption(f"📅 {op['fecha']}")
                st.divider()
        else:
            st.info("No hay opiniones aprobadas")

# --- TAB 8: EFEMÉRIDES MÉDICAS ---
with menu_tabs[8]:
    st.title("📅 Efemérides Médicas")
    
    fecha_actual_str = f"{ahora.day} de {meses[ahora.month-1]}"
    st.markdown(f"### 📌 {dias[ahora.weekday()]}, {fecha_actual_str} de {ahora.year}")
    
    col_ven, col_mundo = st.columns(2)
    
    with col_ven:
        st.markdown("#### 🇻🇪 Venezuela")
        
        efemerides_venezuela = {
            "24 de Junio": "Día del Médico Venezolano. Se conmemora el nacimiento del Dr. José María Vargas, médico cirujano y presidente de Venezuela.",
            "3 de Diciembre": "Día del Odontólogo Venezolano.",
            "13 de Octubre": "Día del Trabajador de la Salud en Venezuela.",
            "10 de Diciembre": "Día de la Enfermera Venezolana.",
            "12 de Mayo": "Día de la Madre (salud familiar).",
            "12 de Marzo": "Día del Oftalmólogo Venezolano.",
            "15 de Abril": "Día del Bioanalista Venezolano."
        }
        
        hoy_ven = None
        for fecha, texto in efemerides_venezuela.items():
            if fecha == fecha_actual_str:
                hoy_ven = texto
                break
        
        if hoy_ven:
            st.success(f"🎉 **¡HOY!** {fecha_actual_str}: {hoy_ven}")
        else:
            st.info(f"📌 Para hoy ({fecha_actual_str}) no hay una efeméride médica registrada en Venezuela.")
        
        st.markdown("---")
        st.markdown("**📅 Otras efemérides importantes:**")
        for fecha, texto in efemerides_venezuela.items():
            st.markdown(f"- **{fecha}:** {texto}")
    
    with col_mundo:
        st.markdown("#### 🌎 Mundo")
        
        efemerides_mundo = {
            "12 de Mayo": "Día Internacional de la Enfermería (natalicio de Florence Nightingale).",
            "6 de Abril": "Día Mundial de la Actividad Física.",
            "7 de Abril": "Día Mundial de la Salud.",
            "31 de Mayo": "Día Mundial sin Tabaco.",
            "14 de Junio": "Día Mundial del Donante de Sangre.",
            "28 de Julio": "Día Mundial contra la Hepatitis.",
            "8 de Septiembre": "Día Mundial de la Fisioterapia.",
            "10 de Octubre": "Día Mundial de la Salud Mental.",
            "14 de Noviembre": "Día Mundial de la Diabetes.",
            "1 de Diciembre": "Día Mundial de la Lucha contra el Sida.",
            "13 de Febrero": "Día Mundial de la Radio (salud).",
            "17 de Mayo": "Día Mundial de la Hipertensión.",
            "21 de Junio": "Día Mundial de la Esclerosis Lateral Amiotrófica (ELA)."
        }
        
        hoy_mundo = None
        for fecha, texto in efemerides_mundo.items():
            if fecha == fecha_actual_str:
                hoy_mundo = texto
                break
        
        if hoy_mundo:
            st.success(f"🎉 **¡HOY!** {fecha_actual_str}: {hoy_mundo}")
        else:
            st.info(f"📌 Para hoy ({fecha_actual_str}) no hay una efeméride médica mundial registrada.")
        
        st.markdown("---")
        st.markdown("**📅 Otras efemérides importantes:**")
        for fecha, texto in efemerides_mundo.items():
            st.markdown(f"- **{fecha}:** {texto}")
    
    st.markdown("---")
    st.caption("📚 Fuentes: Federación Médica Venezolana, Organización Mundial de la Salud (OMS)")

# ============================================
# PANEL ADMIN - CONTENIDO
# ============================================
if st.session_state.get('es_admin', False):
    st.sidebar.markdown("---")
    st.sidebar.markdown("### ⚙️ Acciones disponibles")
    
    admin_opt = st.session_state.get('admin_opt', "📰 Noticias")
    
    st.title("🔧 Panel de Administración")
    
    if "📰 Noticias" in admin_opt:
        st.subheader("📰 Gestionar Noticias")
        with st.form("fn"):
            titulo = st.text_input("Título")
            categoria = st.selectbox("Categoría", ["Nacional", "Internacional", "Deportes", "Reportajes"])
            contenido = st.text_area("Contenido")
            imagen = st.file_uploader("Imagen", type=["jpg", "png", "jpeg"])
            if st.form_submit_button("📤 Publicar Noticia"):
                if titulo and contenido:
                    add_noticia(titulo, categoria, contenido, imagen)
                    st.success("✅ Noticia publicada correctamente")
                    st.rerun()
                else:
                    st.error("❌ Título y contenido son obligatorios")
        
        st.markdown("---")
        st.markdown("### 📋 Noticias existentes")
        for _, n in get_noticias().iterrows():
            with st.expander(f"{n['titulo']} - {n['categoria']}"):
                st.write(n['contenido'])
                if st.button("🗑️ Eliminar", key=f"del_{n['id']}"):
                    delete_noticia(n['id'])
                    st.success("✅ Noticia eliminada")
                    st.rerun()
    
    elif "🏪 Negocios" in admin_opt:
        st.subheader("🏪 Gestionar Negocios")
        with st.form("fneg"):
            nombre = st.text_input("Nombre del negocio")
            categoria = st.text_input("Categoría")
            resena = st.text_area("Reseña")
            direccion = st.text_input("Dirección")
            telefono = st.text_input("Teléfono")
            horario = st.text_input("Horario")
            imagen = st.file_uploader("Foto", type=["jpg", "png", "jpeg"])
            if st.form_submit_button("➕ Agregar Negocio"):
                if nombre and resena:
                    add_negocio(nombre, categoria, resena, direccion, telefono, horario, imagen)
                    st.success("✅ Negocio agregado correctamente")
                    st.rerun()
                else:
                    st.error("❌ Nombre y reseña son obligatorios")
        
        st.markdown("---")
        st.markdown("### 📋 Negocios existentes")
        for _, n in get_negocios().iterrows():
            with st.expander(f"{n['nombre']} - {n['categoria']}"):
                st.write(n['resena'])
                if st.button("🗑️ Eliminar", key=f"del_neg_{n['id']}"):
                    delete_negocio(n['id'])
                    st.success("✅ Negocio eliminado")
                    st.rerun()
    
    elif "💭 Reflexiones" in admin_opt:
        st.subheader("💭 Gestionar Reflexiones")
        with st.form("fref"):
            titulo = st.text_input("Título")
            versiculo = st.text_input("Versículo")
            contenido = st.text_area("Contenido")
            if st.form_submit_button("💾 Guardar Reflexión (activa)"):
                if titulo and contenido:
                    add_reflexion(titulo, contenido, versiculo)
                    st.success("✅ Reflexión guardada como activa")
                    st.rerun()
                else:
                    st.error("❌ Título y contenido son obligatorios")
        
        st.markdown("---")
        st.markdown("### 📋 Reflexiones anteriores")
        for _, r in get_reflexiones().iterrows():
            with st.expander(f"{r['titulo']} - {r['fecha']}"):
                st.write(r['contenido'])
                if r.get('versiculo'):
                    st.caption(f"📖 {r['versiculo']}")
                if st.button("🗑️ Eliminar", key=f"del_ref_{r['id']}"):
                    delete_reflexion(r['id'])
                    st.success("✅ Reflexión eliminada")
                    st.rerun()
    
    elif "📜 Crónicas" in admin_opt:
        st.subheader("📜 Gestionar Crónicas")
        with st.form("fcro"):
            titulo = st.text_input("Título")
            lugar = st.text_input("Lugar")
            estado = st.selectbox("Estado", ["Miranda", "Carabobo", "Distrito Capital", "Zulia", "Lara", "Aragua", "Bolivar", "Anzoategui", "Merida", "Tachira", "Nueva Esparta", "Sucre", "Falcon", "Barinas", "Portuguesa", "Guarico", "Cojedes", "Trujillo", "Yaracuy", "Apure", "Amazonas", "Delta Amacuro", "Vargas"])
            contenido = st.text_area("Contenido")
            if st.form_submit_button("💾 Guardar Crónica"):
                if titulo and contenido:
                    add_cronica(titulo, contenido, lugar, estado)
                    st.success("✅ Crónica guardada correctamente")
                    st.rerun()
                else:
                    st.error("❌ Título y contenido son obligatorios")
        
        st.markdown("---")
        st.markdown("### 📋 Crónicas existentes")
        for _, c in get_cronicas().iterrows():
            with st.expander(f"{c['titulo']} - {c['lugar']}"):
                st.write(c['contenido'])
                if st.button("🗑️ Eliminar", key=f"del_cron_{c['id']}"):
                    delete_cronica(c['id'])
                    st.success("✅ Crónica eliminada")
                    st.rerun()
    
    elif "🎬 Videos" in admin_opt:
        st.subheader("🎬 Gestionar Videos")
        with st.form("fvid"):
            titulo = st.text_input("Título del video")
            archivo = st.file_uploader("Archivo de video", type=["mp4", "avi", "mov", "mkv"])
            if st.form_submit_button("📤 Subir Video"):
                if titulo and archivo:
                    add_video(titulo, archivo)
                    st.success("✅ Video subido correctamente")
                    st.rerun()
                else:
                    st.error("❌ Título y archivo son obligatorios")
        
        st.markdown("---")
        st.markdown("### 📋 Videos existentes")
        for _, v in get_videos().iterrows():
            with st.expander(v['titulo']):
                mostrar_video(v['video_data'], v['formato'])
                if st.button("🗑️ Eliminar", key=f"del_vid_{v['id']}"):
                    delete_video(v['id'])
                    st.success("✅ Video eliminado")
                    st.rerun()
    
    elif "🎵 Música" in admin_opt:
        st.subheader("🎵 Gestionar Música")
        with st.form("fmus"):
            titulo = st.text_input("Título de la canción")
            archivo = st.file_uploader("Archivo de audio", type=["mp3", "wav", "ogg"])
            if st.form_submit_button("📤 Subir Audio"):
                if titulo and archivo:
                    add_musica(titulo, archivo)
                    st.success("✅ Audio subido correctamente")
                    st.rerun()
                else:
                    st.error("❌ Título y archivo son obligatorios")
        
        st.markdown("---")
        st.markdown("### 📋 Archivos de música")
        for _, m in get_musicas().iterrows():
            with st.expander(m['titulo']):
                mostrar_audio(m['audio_data'], m['formato'])
                if st.button("🗑️ Eliminar", key=f"del_mus_{m['id']}"):
                    delete_musica(m['id'])
                    st.success("✅ Audio eliminado")
                    st.rerun()
    
    elif "⚠️ Denuncias" in admin_opt:
        st.subheader("⚠️ Gestionar Denuncias")
        for _, d in get_denuncias().iterrows():
            with st.expander(f"📌 {d['titulo']} - {d['estatus']}"):
                st.write(f"**Denunciante:** {d['denunciante']}")
                st.write(f"**Descripción:** {d['descripcion']}")
                st.write(f"**Ubicación:** {d['ubicacion'] if d['ubicacion'] else 'No especificada'}")
                nuevo = st.selectbox("Cambiar estado:", ["Pendiente", "En revisión", "Resuelta", "Descartada"], 
                                    index=["Pendiente", "En revisión", "Resuelta", "Descartada"].index(d['estatus']), 
                                    key=f"est_{d['id']}")
                if st.button("✅ Actualizar", key=f"upd_{d['id']}"):
                    update_denuncia_status(d['id'], nuevo)
                    st.success("✅ Estado actualizado")
                    st.rerun()
                if st.button("🗑️ Eliminar", key=f"del_den_{d['id']}"):
                    delete_denuncia(d['id'])
                    st.success("✅ Denuncia eliminada")
                    st.rerun()
    
    elif "💬 Opiniones" in admin_opt:
        st.subheader("💬 Gestionar Opiniones")
        st.markdown("### ⏳ Opiniones pendientes de aprobar")
        for _, op in get_opiniones(aprobadas=False).iterrows():
            if not op['aprobada']:
                with st.expander(f"👤 {op['usuario']} - {op['calificacion']}⭐"):
                    st.write(f"**Comentario:** {op['comentario']}")
                    st.caption(f"📅 {op['fecha']}")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("✅ Aprobar", key=f"aprob_{op['id']}"):
                            approve_opinion(op['id'])
                            st.success("✅ Opinión aprobada")
                            st.rerun()
                    with col2:
                        if st.button("🗑️ Eliminar", key=f"del_op_{op['id']}"):
                            delete_opinion(op['id'])
                            st.success("✅ Opinión eliminada")
                            st.rerun()
        
        st.markdown("---")
        st.markdown("### ✅ Opiniones aprobadas")
        for _, op in get_opiniones(aprobadas=True).iterrows():
            with st.expander(f"👤 {op['usuario']} - {op['calificacion']}⭐"):
                st.write(f"**Comentario:** {op['comentario']}")
                st.caption(f"📅 {op['fecha']}")
                if st.button("🗑️ Eliminar", key=f"del_op_aprob_{op['id']}"):
                    delete_opinion(op['id'])
                    st.success("✅ Opinión eliminada")
                    st.rerun()
    
    elif "⚙️ Configuración" in admin_opt:
        st.subheader("⚙️ Configuración del Sistema")
        
        st.markdown("### 💵 Tipo de Cambio Dólar BCV")
        st.write(f"Valor actual: **{dolar:.2f} Bs**")
        nuevo_dolar = st.number_input("Nuevo valor:", value=float(dolar), step=0.01, format="%.2f")
        if st.button("💾 Actualizar Dólar"):
            actualizar_dolar_manual(nuevo_dolar)
            st.success("✅ Valor del dólar actualizado")
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 🖼️ Logo de la aplicación")
        if logo:
            st.image(logo, width=150)
        nuevo_logo = st.file_uploader("Subir nuevo logo", type=["png", "jpg", "jpeg"])
        if nuevo_logo and st.button("💾 Guardar Logo"):
            b64 = img_a_base64(nuevo_logo)
            if b64:
                save_logo(b64)
                st.success("✅ Logo guardado correctamente")
                st.rerun()

# ============================================
# FOOTER
# ============================================
st.markdown("""
<div class="bronze-footer">
    <div class="screw screw-tl"></div>
    <div class="screw screw-tr"></div>
    <div class="screw screw-bl"></div>
    <div class="screw screw-br"></div>
    <p class="titulo">DESARROLLADO POR WILLIAN ALMENAR</p>
    <p>Prohibida la reproducción total o parcial</p>
    <p>DERECHOS RESERVADOS</p>
    <p>Santa Teresa del Tuy, 2026</p>
</div>
""", unsafe_allow_html=True)
